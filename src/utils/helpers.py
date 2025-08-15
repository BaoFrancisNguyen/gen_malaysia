#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FONCTIONS D'AIDE CORRIGÉES - UTILS MODULE
=========================================

Version plus permissive pour les bâtiments OSM.
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
# GÉNÉRATION D'IDENTIFIANTS (inchangé)
# ==============================================================================

def generate_unique_id(prefix: str = '', length: int = 8) -> str:
    """Génère un identifiant unique"""
    unique_part = str(uuid.uuid4()).replace('-', '')[:length].upper()
    return f"{prefix}_{unique_part}" if prefix else unique_part


def generate_building_id(building_type: str, source: str) -> str:
    """Génère un ID descriptif pour un bâtiment"""
    type_prefix = building_type[0].upper() if building_type else 'B'
    source_code = source[:3].upper() if source else 'SRC'
    unique_part = generate_unique_id(length=6)
    return f"{type_prefix}{source_code}{unique_part}"


def generate_session_id() -> str:
    """Génère un ID de session unique avec timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_part = generate_unique_id(length=6)
    return f"session_{timestamp}_{unique_part}"


# ==============================================================================
# CALCULS GÉOGRAPHIQUES (plus permissifs)
# ==============================================================================

def validate_malaysia_coordinates(latitude: float, longitude: float) -> bool:
    """
    Vérifie si des coordonnées sont dans les limites Malaysia
    VERSION PLUS PERMISSIVE
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        bool: True si dans les limites Malaysia (élarges)
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        # Limites élargies pour Malaysia (plus permissives)
        return (0.0 <= lat <= 8.0 and 99.0 <= lon <= 120.0)
        
    except (ValueError, TypeError):
        return False


def calculate_approximate_area(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calcule une surface approximative en m² - VERSION ROBUSTE
    
    Args:
        coordinates: Liste de tuples (latitude, longitude)
        
    Returns:
        float: Surface approximative en m²
    """
    if not coordinates or len(coordinates) < 3:
        return 100.0  # Surface par défaut raisonnable
    
    try:
        # Formule shoelace pour calculer l'aire d'un polygone
        n = len(coordinates)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            # Protection contre les valeurs nulles
            if coordinates[i] and coordinates[j] and len(coordinates[i]) >= 2 and len(coordinates[j]) >= 2:
                area += coordinates[i][0] * coordinates[j][1]
                area -= coordinates[j][0] * coordinates[i][1]
        
        area = abs(area) / 2.0
        
        # Conversion approximative degrés -> m²
        area_m2 = area * MathConstants.METERS_PER_DEGREE_LAT * MathConstants.METERS_PER_DEGREE_LAT
        
        # Surface réaliste entre 20m² et 50,000m²
        return max(min(area_m2, 50000), 20.0)
        
    except Exception as e:
        # En cas d'erreur, retourner une surface par défaut
        return 100.0


def normalize_building_type(raw_type: str) -> str:
    """
    Normalise un type de bâtiment - VERSION TRÈS PERMISSIVE
    
    Args:
        raw_type: Type brut (ex: depuis OSM)
        
    Returns:
        str: Type normalisé
    """
    if not raw_type or not isinstance(raw_type, str):
        return 'residential'  # Par défaut
    
    raw_lower = raw_type.lower().strip()
    
    # Mapping très permissif
    if any(keyword in raw_lower for keyword in ['house', 'home', 'residential', 'apartment', 'terrace', 'detached']):
        return 'residential'
    elif any(keyword in raw_lower for keyword in ['shop', 'store', 'retail', 'commercial', 'mall']):
        return 'commercial'
    elif any(keyword in raw_lower for keyword in ['office', 'government', 'civic', 'public']):
        return 'office'
    elif any(keyword in raw_lower for keyword in ['factory', 'industrial', 'warehouse', 'manufacture']):
        return 'industrial'
    elif any(keyword in raw_lower for keyword in ['school', 'university', 'college', 'education']):
        return 'school'
    elif any(keyword in raw_lower for keyword in ['hospital', 'clinic', 'medical', 'health']):
        return 'hospital'
    else:
        return 'residential'  # Par défaut pour tout le reste


# ==============================================================================
# MANIPULATION SÉCURISÉE DE DONNÉES
# ==============================================================================

def safe_float_parse(value: Any, default: float = 0.0) -> float:
    """Parse une valeur en float de manière sécurisée"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_parse(value: Any, default: int = 0) -> int:
    """Parse une valeur en int de manière sécurisée"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_get_building_field(building: Dict, field: str, default: Any = None) -> Any:
    """
    Récupère un champ de bâtiment de manière sécurisée
    
    Args:
        building: Dictionnaire bâtiment
        field: Nom du champ
        default: Valeur par défaut
        
    Returns:
        Any: Valeur du champ ou défaut
    """
    if not isinstance(building, dict):
        return default
    
    # Essaie plusieurs variantes du nom de champ
    field_variants = [
        field,
        field.lower(),
        field.upper(),
        field.replace('_', ''),
        field.replace('_', '-')
    ]
    
    for variant in field_variants:
        if variant in building:
            value = building[variant]
            if value is not None:
                return value
    
    return default


def normalize_building_data(building: Dict) -> Dict:
    """
    Normalise les données d'un bâtiment pour être plus robuste
    
    Args:
        building: Données bâtiment brutes
        
    Returns:
        Dict: Données bâtiment normalisées
    """
    if not isinstance(building, dict):
        return {
            'id': generate_unique_id('unknown'),
            'building_type': 'residential',
            'latitude': 3.1390,  # KL par défaut
            'longitude': 101.6869,
            'surface_area_m2': 100.0,
            'zone_name': 'unknown',
            'source': 'unknown'
        }
    
    # Récupération sécurisée des champs essentiels
    building_id = (safe_get_building_field(building, 'id') or 
                  safe_get_building_field(building, 'building_id') or 
                  safe_get_building_field(building, 'osm_id') or
                  generate_unique_id('norm'))
    
    # Coordonnées avec fallback sur KL
    latitude = safe_float_parse(safe_get_building_field(building, 'latitude'), 3.1390)
    longitude = safe_float_parse(safe_get_building_field(building, 'longitude'), 101.6869)
    
    # Validation et correction des coordonnées
    if not validate_malaysia_coordinates(latitude, longitude):
        latitude = 3.1390   # KL par défaut
        longitude = 101.6869
    
    # Type de bâtiment normalisé
    raw_type = safe_get_building_field(building, 'building_type', 'residential')
    building_type = normalize_building_type(raw_type)
    
    # Surface avec valeur par défaut raisonnable
    surface = safe_float_parse(safe_get_building_field(building, 'surface_area_m2'), 100.0)
    if surface <= 0 or surface > 100000:
        surface = 100.0
    
    # Zone avec fallback
    zone_name = safe_get_building_field(building, 'zone_name', 'unknown')
    
    # Source
    source = safe_get_building_field(building, 'source', 'osm')
    
    return {
        'id': str(building_id),
        'building_type': building_type,
        'latitude': latitude,
        'longitude': longitude,
        'surface_area_m2': surface,
        'zone_name': zone_name,
        'source': source,
        'osm_id': safe_get_building_field(building, 'osm_id'),
        'tags': safe_get_building_field(building, 'tags', {})
    }


def robust_building_list_validation(buildings: List[Dict]) -> List[Dict]:
    """
    Valide et normalise une liste de bâtiments de manière très robuste
    
    Args:
        buildings: Liste de bâtiments bruts
        
    Returns:
        List[Dict]: Liste de bâtiments normalisés et valides
    """
    if not buildings or not isinstance(buildings, list):
        return []
    
    normalized_buildings = []
    
    for i, building in enumerate(buildings):
        try:
            # Normalisation robuste
            normalized = normalize_building_data(building)
            normalized_buildings.append(normalized)
            
        except Exception as e:
            # En cas d'erreur, créer un bâtiment par défaut
            logger = logging.getLogger(__name__)
            logger.warning(f"Erreur normalisation bâtiment {i}: {e}")
            
            default_building = {
                'id': generate_unique_id(f'error_{i}'),
                'building_type': 'residential',
                'latitude': 3.1390 + (i % 10) * 0.001,  # Légère variation
                'longitude': 101.6869 + (i % 10) * 0.001,
                'surface_area_m2': 100.0,
                'zone_name': 'unknown',
                'source': 'error_recovery'
            }
            normalized_buildings.append(default_building)
    
    return normalized_buildings


# ==============================================================================
# UTILITAIRES SYSTÈME ET FORMATAGE (inchangés)
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


def get_file_size_mb(file_path: Path) -> float:
    """Retourne la taille d'un fichier en MB"""
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def clean_filename(filename: str) -> str:
    """Nettoie un nom de fichier en supprimant les caractères interdits"""
    forbidden_chars = '<>:"/\\|?*'
    
    cleaned = filename
    for char in forbidden_chars:
        cleaned = cleaned.replace(char, '_')
    
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


# ==============================================================================
# FACTORY PATTERNS POUR MÉTADONNÉES (inchangés)
# ==============================================================================

def create_metadata_base() -> Dict:
    """Crée les métadonnées de base standardisées"""
    return {
        'created_at': datetime.now().isoformat(),
        'system_version': AppConfig.VERSION,
        'system_name': AppConfig.NAME
    }


def create_success_response(message_code: str, data: Any = None, **kwargs) -> Dict:
    """Crée une réponse de succès standardisée"""
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


def create_error_response(error_code: str, details: str = None, **kwargs) -> Dict:
    """Crée une réponse d'erreur standardisée"""
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


# ==============================================================================
# LOGGING ET SYSTÈME
# ==============================================================================

def setup_logging() -> logging.Logger:
    """Configure le système de logging de l'application"""
    AppConfig.LOGS_DIR.mkdir(exist_ok=True)
    
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