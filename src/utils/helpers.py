#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FONCTIONS D'AIDE - UTILS MODULE
===============================

Fonctions utilitaires centralisées. Version optimisée sans redondances.
"""

import os
import sys
import uuid
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np

from config import AppConfig, MalaysiaConfig, LogConfig, MathConstants


# ==============================================================================
# CONFIGURATION LOGGING (centralisée)
# ==============================================================================

def setup_logging() -> logging.Logger:
    """
    Configure le système de logging de l'application
    
    Returns:
        logging.Logger: Logger configuré
    """
    # Créer le dossier logs s'il n'existe pas
    AppConfig.LOGS_DIR.mkdir(exist_ok=True)
    
    # Configuration du logging
    log_file = AppConfig.LOGS_DIR / 'app.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format=LogConfig.LOG_FORMAT,
        datefmt=LogConfig.LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('malaysia_electricity_generator')
    logger.info("✅ Système de logging initialisé")
    
    return logger


# ==============================================================================
# GÉNÉRATION D'IDENTIFIANTS (centralisée)
# ==============================================================================

def generate_unique_id(prefix: str = '', length: int = 8) -> str:
    """
    Génère un identifiant unique
    
    Args:
        prefix: Préfixe optionnel
        length: Longueur de la partie unique
        
    Returns:
        str: Identifiant unique
    """
    unique_part = str(uuid.uuid4()).replace('-', '')[:length].upper()
    return f"{prefix}_{unique_part}" if prefix else unique_part


def generate_building_id(building_type: str, source: str) -> str:
    """
    Génère un ID descriptif pour un bâtiment
    
    Args:
        building_type: Type de bâtiment
        source: Source des données (ex: 'OSM')
        
    Returns:
        str: ID du bâtiment
    """
    # Première lettre du type
    type_prefix = building_type[0].upper() if building_type else 'B'
    
    # Code source
    source_code = source[:3].upper() if source else 'SRC'
    
    # Partie unique
    unique_part = generate_unique_id(length=6)
    
    return f"{type_prefix}{source_code}{unique_part}"


def generate_session_id() -> str:
    """
    Génère un ID de session unique avec timestamp
    
    Returns:
        str: ID de session
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_part = generate_unique_id(length=6)
    return f"session_{timestamp}_{unique_part}"


# ==============================================================================
# CALCULS GÉOGRAPHIQUES (centralisés et optimisés)
# ==============================================================================

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance entre deux points en kilomètres (formule haversine)
    
    Args:
        lat1, lon1: Coordonnées du premier point
        lat2, lon2: Coordonnées du second point
        
    Returns:
        float: Distance en kilomètres
    """
    # Conversion en radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Différences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Formule haversine
    a = (math.sin(dlat / 2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return MathConstants.EARTH_RADIUS_KM * c


def calculate_approximate_area(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calcule une surface approximative en m² depuis une liste de coordonnées
    VERSION UNIQUE - Supprime les doublons dans building.py
    
    Args:
        coordinates: Liste de tuples (latitude, longitude)
        
    Returns:
        float: Surface approximative en m²
    """
    if len(coordinates) < 3:
        return 50.0  # Surface par défaut pour points isolés
    
    try:
        # Formule shoelace pour calculer l'aire d'un polygone
        n = len(coordinates)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        
        area = abs(area) / 2.0
        
        # Conversion approximative degrés -> m²
        area_m2 = area * MathConstants.METERS_PER_DEGREE_LAT * MathConstants.METERS_PER_DEGREE_LAT
        
        # Surface minimale et maximale réalistes
        return max(min(area_m2, 100000), 10.0)  # Entre 10m² et 100,000m²
        
    except Exception:
        return 50.0  # Valeur par défaut en cas d'erreur


def calculate_bbox_area(bbox: List[float]) -> float:
    """
    Calcule la surface d'une bbox en km²
    
    Args:
        bbox: [west, south, east, north]
        
    Returns:
        float: Surface en km²
    """
    west, south, east, north = bbox
    
    # Largeur et hauteur en degrés
    width_deg = east - west
    height_deg = north - south
    
    # Conversion approximative
    width_km = width_deg * 111  # 1° ≈ 111 km
    height_km = height_deg * 111
    
    return width_km * height_km


def validate_malaysia_coordinates(latitude: float, longitude: float) -> bool:
    """
    Vérifie si des coordonnées sont dans les limites Malaysia
    VERSION UNIQUE - Centralisée ici, supprime les doublons
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        bool: True si dans les limites Malaysia
    """
    bounds = MalaysiaConfig.BOUNDS
    return (bounds['south'] <= latitude <= bounds['north'] and 
            bounds['west'] <= longitude <= bounds['east'])


# ==============================================================================
# MANIPULATION DE DONNÉES (optimisée)
# ==============================================================================

def safe_float_parse(value: Any, default: float = 0.0) -> float:
    """Parse une valeur en float de manière sécurisée"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_parse(value: Any, default: int = 0) -> int:
    """Parse une valeur en int de manière sécurisée"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def chunk_list(data_list: List[Any], chunk_size: int) -> List[List[Any]]:
    """Divise une liste en chunks de taille donnée"""
    chunks = []
    for i in range(0, len(data_list), chunk_size):
        chunks.append(data_list[i:i + chunk_size])
    return chunks


def deep_merge_dict(dict1: Dict, dict2: Dict) -> Dict:
    """Fusion profonde de deux dictionnaires"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


# ==============================================================================
# FORMATAGE ET AFFICHAGE (centralisé)
# ==============================================================================

def format_duration(seconds: float) -> str:
    """Formate une durée en secondes vers un format lisible"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}min"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_file_size(size_bytes: int) -> str:
    """Formate une taille de fichier en bytes vers un format lisible"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = MathConstants.SIZE_PREFIXES
    i = int(math.floor(math.log(size_bytes, 1024)))
    
    if i >= len(size_names):
        i = len(size_names) - 1
    
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def format_number(number: float, precision: int = 2) -> str:
    """Formate un nombre avec séparateurs de milliers"""
    if precision == 0:
        return f"{int(number):,}".replace(',', ' ')
    else:
        return f"{number:,.{precision}f}".replace(',', ' ')


# ==============================================================================
# UTILITAIRES FICHIERS ET SYSTÈME
# ==============================================================================

def ensure_directory(directory_path: Path) -> bool:
    """S'assure qu'un dossier existe"""
    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Erreur création dossier {directory_path}: {e}")
        return False


def get_file_size_mb(file_path: Path) -> float:
    """Retourne la taille d'un fichier en MB"""
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)  # Conversion directe en MB
    except Exception:
        return 0.0


def clean_filename(filename: str) -> str:
    """Nettoie un nom de fichier en supprimant les caractères interdits"""
    # Caractères interdits centralisés
    forbidden_chars = '<>:"/\\|?*'
    
    cleaned = filename
    for char in forbidden_chars:
        cleaned = cleaned.replace(char, '_')
    
    # Suppression des espaces multiples et trim
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


# ==============================================================================
# UTILITAIRES SPÉCIFIQUES MALAYSIA (centralisés)
# ==============================================================================

def normalize_building_type(raw_type: str) -> str:
    """
    Normalise un type de bâtiment vers nos catégories standards
    VERSION UNIQUE - Supprime le doublon dans building.py
    
    Args:
        raw_type: Type brut (ex: depuis OSM)
        
    Returns:
        str: Type normalisé
    """
    if not raw_type:
        return 'residential'
    
    raw_lower = raw_type.lower()
    
    # Utilisation de la configuration centralisée
    for building_type, config in MalaysiaConfig.BUILDING_TYPES.items():
        osm_tags = config.get('osm_tags', [])
        if any(tag in raw_lower for tag in osm_tags):
            return building_type
    
    return 'residential'  # Par défaut


# ==============================================================================
# FACTORY PATTERNS POUR MÉTADONNÉES (nouveaux)
# ==============================================================================

def create_metadata_base() -> Dict:
    """Crée les métadonnées de base standardisées"""
    return {
        'created_at': datetime.now().isoformat(),
        'system_version': AppConfig.VERSION,
        'system_name': AppConfig.NAME
    }


def create_session_metadata(session_type: str, **kwargs) -> Dict:
    """
    Crée des métadonnées de session standardisées
    
    Args:
        session_type: Type de session ('generation', 'export', 'osm')
        **kwargs: Paramètres additionnels
        
    Returns:
        Dict: Métadonnées de session
    """
    metadata = create_metadata_base()
    metadata.update({
        'session_id': generate_session_id(),
        'session_type': session_type,
        'parameters': kwargs
    })
    return metadata


def create_error_response(error_code: str, details: str = None, **kwargs) -> Dict:
    """
    Crée une réponse d'erreur standardisée
    
    Args:
        error_code: Code d'erreur depuis AppConfig.MESSAGES['errors']
        details: Détails additionnels
        **kwargs: Données additionnelles
        
    Returns:
        Dict: Réponse d'erreur standardisée
    """
    error_message = AppConfig.MESSAGES['errors'].get(error_code, error_code)
    
    response = {
        'success': False,
        'error': error_message,
        'error_code': error_code,
        'timestamp': datetime.now().isoformat()
    }
    
    if details:
        response['details'] = details
    
    response.update(kwargs)
    return response


def create_success_response(message_code: str, data: Any = None, **kwargs) -> Dict:
    """
    Crée une réponse de succès standardisée
    
    Args:
        message_code: Code de message depuis AppConfig.MESSAGES['success']
        data: Données de réponse
        **kwargs: Données additionnelles
        
    Returns:
        Dict: Réponse de succès standardisée
    """
    success_message = AppConfig.MESSAGES['success'].get(message_code, message_code)
    
    response = {
        'success': True,
        'message': success_message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    response.update(kwargs)
    return response


# ==============================================================================
# UTILITAIRES DE PERFORMANCE (optimisés)
# ==============================================================================

def log_performance(func):
    """Décorateur pour logger les performances d'une fonction"""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger = logging.getLogger(__name__)
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"⏱️ {func.__name__} exécuté en {format_duration(execution_time)}")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ {func.__name__} échoué après {format_duration(execution_time)}: {e}")
            raise
    
    return wrapper


def memory_usage_mb() -> float:
    """Retourne l'utilisation mémoire actuelle en MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / MathConstants.CONVERSION['bytes_to_mb']
    except ImportError:
        return 0.0


# ==============================================================================
# UTILITAIRES DE VALIDATION SIMPLIFIÉS
# ==============================================================================

def is_valid_date_string(date_string: str) -> bool:
    """Vérifie si une chaîne est une date valide au format YYYY-MM-DD"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def is_valid_frequency(frequency: str) -> bool:
    """Vérifie si une fréquence est valide"""
    from config import TimeConfig
    return frequency in TimeConfig.SUPPORTED_FREQUENCIES


# ==============================================================================
# UTILITAIRES DE CALCUL ÉNERGÉTIQUE (centralisés)
# ==============================================================================

def calculate_energy_intensity(consumption_kwh: float, surface_m2: float) -> float:
    """
    Calcule l'intensité énergétique en kWh/m²
    
    Args:
        consumption_kwh: Consommation en kWh
        surface_m2: Surface en m²
        
    Returns:
        float: Intensité énergétique
    """
    if surface_m2 <= 0:
        return 0.0
    return consumption_kwh / surface_m2


def calculate_water_intensity(consumption_liters: float, surface_m2: float) -> float:
    """
    Calcule l'intensité de consommation d'eau en L/m²
    
    Args:
        consumption_liters: Consommation en litres
        surface_m2: Surface en m²
        
    Returns:
        float: Intensité eau
    """
    if surface_m2 <= 0:
        return 0.0
    return consumption_liters / surface_m2


def estimate_processing_time(total_points: int, processing_rate: int = 50000) -> float:
    """
    Estime le temps de traitement en minutes
    
    Args:
        total_points: Nombre total de points de données
        processing_rate: Points traités par minute
        
    Returns:
        float: Temps estimé en minutes
    """
    return total_points / processing_rate


def estimate_memory_usage(total_points: int, bytes_per_point: int = 200) -> float:
    """
    Estime l'utilisation mémoire en MB
    
    Args:
        total_points: Nombre total de points
        bytes_per_point: Bytes par point de données
        
    Returns:
        float: Mémoire estimée en MB
    """
    total_bytes = total_points * bytes_per_point
    return total_bytes / MathConstants.CONVERSION['bytes_to_mb']


# ==============================================================================
# UTILITAIRES DE CONVERSION (centralisés)
# ==============================================================================

def convert_temperature(temp_celsius: float, to_unit: str = 'kelvin') -> float:
    """Convertit une température depuis Celsius"""
    if to_unit == 'kelvin':
        return temp_celsius + MathConstants.CONVERSION['celsius_to_kelvin']
    elif to_unit == 'fahrenheit':
        return temp_celsius * 9/5 + 32
    else:
        return temp_celsius


def convert_energy(energy_kwh: float, to_unit: str = 'wh') -> float:
    """Convertit une énergie depuis kWh"""
    if to_unit == 'wh':
        return energy_kwh * MathConstants.CONVERSION['kwh_to_wh']
    elif to_unit == 'mwh':
        return energy_kwh / 1000
    else:
        return energy_kwh


# ==============================================================================
# UTILITAIRES DE DEBUG ET DÉVELOPPEMENT
# ==============================================================================

def log_system_info():
    """Log les informations système pour debug"""
    logger = logging.getLogger(__name__)
    
    logger.info("="*50)
    logger.info("🔧 INFORMATIONS SYSTÈME")
    logger.info("="*50)
    logger.info(f"📦 Application: {AppConfig.NAME} v{AppConfig.VERSION}")
    logger.info(f"🐍 Python: {sys.version}")
    logger.info(f"💾 Mémoire: {memory_usage_mb():.1f} MB")
    logger.info(f"📁 Exports: {AppConfig.EXPORTS_DIR}")
    logger.info(f"📋 Logs: {AppConfig.LOGS_DIR}")
    logger.info("="*50)


def validate_system_requirements() -> Dict:
    """Valide les prérequis système"""
    checks = {
        'python_version': sys.version_info >= (3, 8),
        'directories_writable': all([
            AppConfig.EXPORTS_DIR.exists() or AppConfig.EXPORTS_DIR.parent.exists(),
            AppConfig.LOGS_DIR.exists() or AppConfig.LOGS_DIR.parent.exists()
        ]),
        'memory_available': memory_usage_mb() < AppConfig.SYSTEM_LIMITS['max_memory_usage_mb']
    }
    
    return {
        'all_checks_passed': all(checks.values()),
        'individual_checks': checks,
        'recommendations': [
            "Utilisez Python 3.8 ou supérieur" if not checks['python_version'] else None,
            "Vérifiez les permissions de dossiers" if not checks['directories_writable'] else None,
            "Libérez de la mémoire" if not checks['memory_available'] else None
        ]
    }
    for i in range(0, len(data_list), chunk_size):
        chunks