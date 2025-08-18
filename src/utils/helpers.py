#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FONCTIONS D'AIDE - UTILS MODULE
==============================================

Fonctions utilitaires pour l'application Malaysia Electricity Generator.
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
# GÉNÉRATION D'IDENTIFIANTS
# ==============================================================================

def generate_unique_id(prefix: str = '', length: int = 8) -> str:
    """Génère un identifiant unique"""
    unique_part = str(uuid.uuid4()).replace('-', '')[:length].upper()
    return f"{prefix}_{unique_part}" if prefix else unique_part


def generate_building_id(building_type: str, zone: str) -> str:
    """
    Génère un ID descriptif pour un bâtiment
    
    Args:
        building_type: Type de bâtiment
        zone: Zone géographique
        
    Returns:
        str: ID unique descriptif
    """
    type_prefix = building_type[0].upper() if building_type else 'B'
    zone_code = zone[:3].upper() if zone else 'UNK'
    unique_part = generate_unique_id(length=6)
    return f"{type_prefix}{zone_code}{unique_part}"


def generate_session_id() -> str:
    """Génère un ID de session unique avec timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_part = generate_unique_id(length=6)
    return f"session_{timestamp}_{unique_part}"


# ==============================================================================
# CALCULS GÉOGRAPHIQUES
# ==============================================================================

def validate_malaysia_coordinates(latitude: float, longitude: float) -> bool:
    """
    Vérifie si des coordonnées sont dans les limites Malaysia
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        bool: True si dans les limites Malaysia
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        # Limites Malaysia (permissives)
        return (0.0 <= lat <= 8.0 and 99.0 <= lon <= 120.0)
        
    except (ValueError, TypeError):
        return False


def calculate_approximate_area(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calcule la surface approximative d'un polygone en m²
    
    Args:
        coordinates: Liste de tuples (latitude, longitude)
        
    Returns:
        float: Surface en m²
    """
    if not coordinates or len(coordinates) < 3:
        return 100.0
    
    try:
        # Formule shoelace pour calculer l'aire
        n = len(coordinates)
        area_deg = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            if i < len(coordinates) and j < len(coordinates):
                area_deg += coordinates[i][0] * coordinates[j][1]
                area_deg -= coordinates[j][0] * coordinates[i][1]
        
        area_deg = abs(area_deg) / 2.0
        
        # Conversion en m²
        lat_center = sum(coord[0] for coord in coordinates) / len(coordinates)
        meters_per_degree_lat = 111000
        meters_per_degree_lon = 111000 * math.cos(math.radians(lat_center))
        
        area_m2 = area_deg * meters_per_degree_lat * meters_per_degree_lon
        
        return max(min(area_m2, 100000), 10.0)
        
    except Exception:
        return 100.0


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calcule la distance entre deux points en mètres
    
    Args:
        coord1: (latitude, longitude) du premier point
        coord2: (latitude, longitude) du second point
        
    Returns:
        float: Distance en mètres
    """
    try:
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return 6371000 * c
        
    except Exception:
        return 0.0


# ==============================================================================
# NORMALISATION DE DONNÉES
# ==============================================================================

def normalize_building_type(raw_type: str) -> str:
    """
    Normalise un type de bâtiment
    
    Args:
        raw_type: Type brut
        
    Returns:
        str: Type normalisé
    """
    if not raw_type or not isinstance(raw_type, str):
        return 'residential'
    
    raw_lower = raw_type.lower().strip()
    
    if any(keyword in raw_lower for keyword in ['house', 'home', 'residential', 'apartment']):
        return 'residential'
    elif any(keyword in raw_lower for keyword in ['shop', 'store', 'retail', 'commercial']):
        return 'commercial'
    elif any(keyword in raw_lower for keyword in ['office', 'government', 'civic']):
        return 'office'
    elif any(keyword in raw_lower for keyword in ['factory', 'industrial', 'warehouse']):
        return 'industrial'
    elif any(keyword in raw_lower for keyword in ['school', 'university', 'college']):
        return 'school'
    elif any(keyword in raw_lower for keyword in ['hospital', 'clinic', 'medical']):
        return 'hospital'
    else:
        return 'residential'


def normalize_building_data(building: Dict) -> Dict:
    """
    Normalise les données d'un bâtiment de manière robuste
    
    Args:
        building: Données bâtiment brutes
        
    Returns:
        Dict: Données bâtiment normalisées
    """
    if not isinstance(building, dict):
        return create_fallback_building('unknown_normalize')
    
    # === IDENTIFIANTS ===
    building_id = (safe_get_building_field(building, 'unique_id') or
                  safe_get_building_field(building, 'id') or 
                  safe_get_building_field(building, 'building_id') or 
                  safe_get_building_field(building, 'osm_id') or
                  generate_unique_id('norm'))
    
    # === GÉOLOCALISATION ===
    latitude = safe_float_parse(safe_get_building_field(building, 'latitude'), 3.1390)
    longitude = safe_float_parse(safe_get_building_field(building, 'longitude'), 101.6869)
    
    # Validation et correction des coordonnées
    if not validate_malaysia_coordinates(latitude, longitude):
        latitude = 3.1390   # KL par défaut
        longitude = 101.6869
    
    # === TYPE ET USAGE ===
    raw_type = safe_get_building_field(building, 'building_type', 'residential')
    building_type = normalize_building_type(raw_type)
    
    # === SURFACE ===
    surface_area = safe_float_parse(building.get('surface_area_m2'), 100.0)
    if surface_area <= 0 or surface_area > 100000:
        surface_area = 100.0
    
    # === ÉTAGES ===
    floors_count = safe_int_parse(building.get('floors_count'), 1)
    if floors_count < 1:
        floors_count = 1
    
    # === ASSEMBLAGE FINAL ===
    normalized = {
        # Identifiants
        'unique_id': str(building_id),
        'osm_id': safe_get_building_field(building, 'osm_id'),
        
        # Localisation
        'latitude': latitude,
        'longitude': longitude,
        'zone_name': safe_get_building_field(building, 'zone_name', 'unknown'),
        
        # Type et usage
        'building_type': building_type,
        
        # Géométrie et surface
        'surface_area_m2': surface_area,
        'floors_count': floors_count,
        
        # Métadonnées
        'source': building.get('source', 'osm'),
        'tags': building.get('tags', {}),
        
        # Conservation des données enrichies si disponibles
        'geometry': building.get('geometry', []),
        'has_precise_geometry': building.get('has_precise_geometry', False),
        'polygon_area_m2': building.get('polygon_area_m2', surface_area),
        'building_levels': floors_count,
        'levels_source': building.get('levels_source', 'estimated'),
        'construction_year': building.get('construction_year'),
        'validation_score': safe_float_parse(building.get('validation_score'), 0.5)
    }
    
    return normalized


def create_fallback_building(identifier: str) -> Dict:
    """
    Crée un bâtiment de fallback
    
    Args:
        identifier: Identifiant unique
        
    Returns:
        Dict: Bâtiment de fallback
    """
    return {
        'unique_id': f'fallback_{identifier}',
        'osm_id': None,
        'latitude': 3.1390,
        'longitude': 101.6869,
        'zone_name': 'unknown',
        'building_type': 'residential',
        'surface_area_m2': 100.0,
        'floors_count': 1,
        'source': 'fallback',
        'tags': {},
        'geometry': [],
        'has_precise_geometry': False,
        'polygon_area_m2': 100.0,
        'building_levels': 1,
        'levels_source': 'fallback',
        'construction_year': None,
        'validation_score': 0.3
    }


def robust_building_list_validation(buildings: List[Dict]) -> List[Dict]:
    """
    Valide et normalise une liste de bâtiments de manière robuste
    
    Args:
        buildings: Liste de bâtiments bruts
        
    Returns:
        List[Dict]: Liste de bâtiments normalisés
    """
    if not buildings or not isinstance(buildings, list):
        return []
    
    normalized_buildings = []
    
    for i, building in enumerate(buildings):
        try:
            normalized = normalize_building_data(building)
            normalized_buildings.append(normalized)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Erreur normalisation bâtiment {i}: {e}")
            
            fallback_building = create_fallback_building(f'error_{i}')
            normalized_buildings.append(fallback_building)
    
    return normalized_buildings


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


# ==============================================================================
# FONCTIONS UTILITAIRES
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
    
    size_names = ['B', 'KB', 'MB', 'GB', 'TB']
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
# LOGGING
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


# ==============================================================================
# ANALYSE GÉOMÉTRIQUE
# ==============================================================================

def analyze_building_geometry_quality(buildings: List[Dict]) -> Dict:
    """
    Analyse la qualité géométrique d'une liste de bâtiments
    
    Args:
        buildings: Liste des bâtiments
        
    Returns:
        Dict: Analyse de qualité géométrique
    """
    if not buildings:
        return {'error': 'Aucun bâtiment à analyser'}
    
    total = len(buildings)
    with_precise_geometry = 0
    with_floors_data = 0
    
    for building in buildings:
        if building.get('has_precise_geometry', False):
            with_precise_geometry += 1
        
        if building.get('floors_count', 1) > 1:
            with_floors_data += 1
    
    return {
        'overview': {
            'total_buildings': total,
            'with_precise_geometry': with_precise_geometry,
            'with_floors_data': with_floors_data,
            'geometry_rate': round(with_precise_geometry / total, 3),
            'floors_rate': round(with_floors_data / total, 3)
        }
    }