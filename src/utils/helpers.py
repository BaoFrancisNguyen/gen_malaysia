#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FONCTIONS D'AIDE - UTILS MODULE
===============================

Fonctions utilitaires partagées dans toute l'application.
Évite la duplication de code et centralise les calculs communs.
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

from config import AppConfig


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
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('malaysia_electricity_generator')
    logger.info("✅ Système de logging initialisé")
    
    return logger


# ==============================================================================
# GÉNÉRATION D'IDENTIFIANTS
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
    Génère un ID de session unique
    
    Returns:
        str: ID de session avec timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_part = generate_unique_id(length=6)
    return f"session_{timestamp}_{unique_part}"


# ==============================================================================
# CALCULS GÉOGRAPHIQUES ET GÉOMÉTRIQUES
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
    # Rayon de la Terre en km
    R = 6371.0
    
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
    
    return R * c


def calculate_approximate_area(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calcule une surface approximative en m² depuis une liste de coordonnées
    
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
        # 1 degré ≈ 111 km à l'équateur
        area_m2 = area * 111000 * 111000
        
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


# ==============================================================================
# MANIPULATION DE DONNÉES
# ==============================================================================

def safe_float_parse(value: Any, default: float = 0.0) -> float:
    """
    Parse une valeur en float de manière sécurisée
    
    Args:
        value: Valeur à parser
        default: Valeur par défaut si échec
        
    Returns:
        float: Valeur parsée ou défaut
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_parse(value: Any, default: int = 0) -> int:
    """
    Parse une valeur en int de manière sécurisée
    
    Args:
        value: Valeur à parser
        default: Valeur par défaut si échec
        
    Returns:
        int: Valeur parsée ou défaut
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def chunk_list(data_list: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Divise une liste en chunks de taille donnée
    
    Args:
        data_list: Liste à diviser
        chunk_size: Taille des chunks
        
    Returns:
        List[List]: Liste de chunks
    """
    chunks = []
    for i in range(0, len(data_list), chunk_size):
        chunks.append(data_list[i:i + chunk_size])
    return chunks


def deep_merge_dict(dict1: Dict, dict2: Dict) -> Dict:
    """
    Fusion profonde de deux dictionnaires
    
    Args:
        dict1: Premier dictionnaire
        dict2: Second dictionnaire (prioritaire)
        
    Returns:
        Dict: Dictionnaire fusionné
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


# ==============================================================================
# FORMATAGE ET AFFICHAGE
# ==============================================================================

def format_duration(seconds: float) -> str:
    """
    Formate une durée en secondes vers un format lisible
    
    Args:
        seconds: Durée en secondes
        
    Returns:
        str: Durée formatée
    """
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
    """
    Formate une taille de fichier en bytes vers un format lisible
    
    Args:
        size_bytes: Taille en bytes
        
    Returns:
        str: Taille formatée
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    
    if i >= len(size_names):
        i = len(size_names) - 1
    
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def format_number(number: float, precision: int = 2) -> str:
    """
    Formate un nombre avec séparateurs de milliers
    
    Args:
        number: Nombre à formater
        precision: Nombre de décimales
        
    Returns:
        str: Nombre formaté
    """
    if precision == 0:
        return f"{int(number):,}".replace(',', ' ')
    else:
        return f"{number:,.{precision}f}".replace(',', ' ')


# ==============================================================================
# UTILITAIRES FICHIERS ET SYSTÈME
# ==============================================================================

def ensure_directory(directory_path: Path) -> bool:
    """
    S'assure qu'un dossier existe
    
    Args:
        directory_path: Chemin du dossier
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Erreur création dossier {directory_path}: {e}")
        return False


def get_file_size_mb(file_path: Path) -> float:
    """
    Retourne la taille d'un fichier en MB
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        float: Taille en MB
    """
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def clean_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier en supprimant les caractères interdits
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        str: Nom de fichier nettoyé
    """
    # Caractères interdits
    forbidden_chars = '<>:"/\\|?*'
    
    cleaned = filename
    for char in forbidden_chars:
        cleaned = cleaned.replace(char, '_')
    
    # Suppression des espaces multiples et trim
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


# ==============================================================================
# UTILITAIRES SPÉCIFIQUES MALAYSIA
# ==============================================================================

def normalize_building_type(raw_type: str) -> str:
    """
    Normalise un type de bâtiment vers nos catégories standards
    
    Args:
        raw_type: Type brut (ex: depuis OSM)
        
    Returns:
        str: Type normalisé
    """
    if not raw_type:
        return 'residential'
    
    raw_lower = raw_type.lower()
    
    # Mapping vers nos types
    type_mapping = {
        'house': 'residential',
        'apartment': 'residential',
        'flat': 'residential',
        'terrace': 'residential',
        'shop': 'commercial',
        'retail': 'commercial',
        'mall': 'commercial',
        'store': 'commercial',
        'office': 'office',
        'government': 'office',
        'civic': 'office',
        'factory': 'industrial',
        'warehouse': 'industrial',
        'industrial': 'industrial',
        'school': 'school',
        'university': 'school',
        'college': 'school',
        'hospital': 'hospital',
        'clinic': 'hospital',
        'healthcare': 'hospital'
    }
    
    for key, normalized_type in type_mapping.items():
        if key in raw_lower:
            return normalized_type
    
    return 'residential'  # Par défaut


def validate_malaysia_coordinates(lat: float, lon: float) -> bool:
    """
    Vérifie si des coordonnées sont dans les limites de la Malaysia
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        bool: True si dans les limites Malaysia
    """
    from config import MalaysiaConfig
    
    bounds = MalaysiaConfig.BOUNDS
    return (bounds['south'] <= lat <= bounds['north'] and 
            bounds['west'] <= lon <= bounds['east'])


# ==============================================================================
# UTILITAIRES DE PERFORMANCE
# ==============================================================================

def log_performance(func):
    """
    Décorateur pour logger les performances d'une fonction
    
    Args:
        func: Fonction à décorer
        
    Returns:
        Function: Fonction décorée
    """
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
    """
    Retourne l'utilisation mémoire actuelle en MB
    
    Returns:
        float: Mémoire utilisée en MB
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0  # psutil non disponible


# ==============================================================================
# UTILITAIRES DE VALIDATION
# ==============================================================================

def is_valid_date_string(date_string: str) -> bool:
    """
    Vérifie si une chaîne est une date valide au format YYYY-MM-DD
    
    Args:
        date_string: Chaîne de date
        
    Returns:
        bool: True si valide
    """
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def is_valid_frequency(frequency: str) -> bool:
    """
    Vérifie si une fréquence pandas est valide
    
    Args:
        frequency: Fréquence (ex: '1H', '15T')
        
    Returns:
        bool: True si valide
    """
    valid_frequencies = ['15T', '30T', '1H', '2H', '3H', '6H', '12H', 'D', 'W']
    return frequency in valid_frequencies