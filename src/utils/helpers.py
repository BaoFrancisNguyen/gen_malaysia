#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FONCTIONS D'AIDE AMÉLIORÉES - UTILS MODULE AVEC GÉOMÉTRIE
=========================================================

Version améliorée compatible avec electricity_generator.py et water_generator.py
qui inclut le support pour la géométrie précise et les métadonnées d'étages.
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
# GÉNÉRATION D'IDENTIFIANTS AMÉLIORÉS
# ==============================================================================

def generate_unique_id(prefix: str = '', length: int = 8) -> str:
    """Génère un identifiant unique amélioré"""
    unique_part = str(uuid.uuid4()).replace('-', '')[:length].upper()
    return f"{prefix}_{unique_part}" if prefix else unique_part


def generate_enhanced_building_id(building_type: str, zone: str, geometry_source: str = 'osm') -> str:
    """
    Génère un ID descriptif pour un bâtiment amélioré avec géométrie
    
    Args:
        building_type: Type de bâtiment
        zone: Zone géographique
        geometry_source: Source de la géométrie
        
    Returns:
        str: ID unique descriptif
    """
    type_prefix = building_type[0].upper() if building_type else 'B'
    zone_code = zone[:3].upper() if zone else 'UNK'
    geom_code = 'P' if geometry_source == 'osm_polygon' else 'E'  # P=Precise, E=Estimated
    unique_part = generate_unique_id(length=6)
    return f"{type_prefix}{zone_code}{geom_code}{unique_part}"


def generate_session_id() -> str:
    """Génère un ID de session unique avec timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_part = generate_unique_id(length=6)
    return f"session_{timestamp}_{unique_part}"


# ==============================================================================
# CALCULS GÉOGRAPHIQUES AMÉLIORÉS
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


def calculate_precise_polygon_area(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calcule la surface précise d'un polygone en m² avec correction latitude
    
    Args:
        coordinates: Liste de tuples (latitude, longitude)
        
    Returns:
        float: Surface précise en m²
    """
    if not coordinates or len(coordinates) < 3:
        return 100.0  # Surface par défaut raisonnable
    
    try:
        # Formule shoelace pour calculer l'aire d'un polygone
        n = len(coordinates)
        area_deg = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            # Protection contre les valeurs nulles
            if coordinates[i] and coordinates[j] and len(coordinates[i]) >= 2 and len(coordinates[j]) >= 2:
                area_deg += coordinates[i][0] * coordinates[j][1]
                area_deg -= coordinates[j][0] * coordinates[i][1]
        
        area_deg = abs(area_deg) / 2.0
        
        # Conversion précise degrés -> m² avec correction latitude
        lat_center = sum(coord[0] for coord in coordinates) / len(coordinates)
        
        # Correction pour la longitude selon la latitude (projection Mercator)
        meters_per_degree_lat = 111000  # Constant
        meters_per_degree_lon = 111000 * math.cos(math.radians(lat_center))
        
        area_m2 = area_deg * meters_per_degree_lat * meters_per_degree_lon
        
        # Surface réaliste entre 10m² et 100,000m²
        return max(min(area_m2, 100000), 10.0)
        
    except Exception as e:
        # En cas d'erreur, retourner une surface par défaut
        return 100.0


def calculate_polygon_perimeter(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calcule le périmètre d'un polygone en mètres
    
    Args:
        coordinates: Liste de tuples (latitude, longitude)
        
    Returns:
        float: Périmètre en mètres
    """
    if not coordinates or len(coordinates) < 2:
        return 0.0
    
    try:
        perimeter = 0.0
        
        for i in range(len(coordinates)):
            j = (i + 1) % len(coordinates)
            if coordinates[i] and coordinates[j]:
                distance = haversine_distance(coordinates[i], coordinates[j])
                perimeter += distance
        
        return perimeter
        
    except Exception:
        return 0.0


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calcule la distance entre deux points en mètres (formule haversine)
    
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
        return 6371000 * c  # Rayon terre en mètres
        
    except Exception:
        return 0.0


def calculate_shape_complexity(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calcule un indice de complexité de forme du bâtiment
    
    Args:
        coordinates: Points du polygone
        
    Returns:
        float: Indice de complexité (1.0 = cercle parfait, >1.0 = plus complexe)
    """
    if not coordinates or len(coordinates) < 3:
        return 1.0
    
    try:
        # Calcul périmètre et aire
        perimeter = calculate_polygon_perimeter(coordinates)
        area = calculate_precise_polygon_area(coordinates)
        
        if area <= 0 or perimeter <= 0:
            return 1.0
        
        # Indice de compacité basé sur le cercle équivalent
        # Pour un cercle: périmètre = 2π√(aire/π) donc complexité = 1
        circle_perimeter = 2 * math.sqrt(math.pi * area)
        complexity = perimeter / circle_perimeter
        
        return max(1.0, min(complexity, 5.0))  # Limité entre 1.0 et 5.0
        
    except Exception:
        return 1.0


def create_approximate_square_geometry(
    center_lat: float, 
    center_lon: float, 
    area_m2: float
) -> List[Dict]:
    """
    Crée une géométrie carrée approximative pour un bâtiment sans polygone
    
    Args:
        center_lat: Latitude du centre
        center_lon: Longitude du centre
        area_m2: Surface désirée en m²
        
    Returns:
        List[Dict]: Géométrie approximative (carré)
    """
    try:
        # Calcul côté du carré équivalent
        side_m = math.sqrt(area_m2)
        
        # Conversion en degrés (approximatif)
        side_deg_lat = side_m / 111000
        side_deg_lon = side_m / (111000 * math.cos(math.radians(center_lat)))
        
        # Carré centré sur les coordonnées
        geometry = [
            {'lat': center_lat - side_deg_lat/2, 'lon': center_lon - side_deg_lon/2},
            {'lat': center_lat - side_deg_lat/2, 'lon': center_lon + side_deg_lon/2},
            {'lat': center_lat + side_deg_lat/2, 'lon': center_lon + side_deg_lon/2},
            {'lat': center_lat + side_deg_lat/2, 'lon': center_lon - side_deg_lon/2},
            {'lat': center_lat - side_deg_lat/2, 'lon': center_lon - side_deg_lon/2}  # Fermeture
        ]
        
        return geometry
        
    except Exception:
        # Géométrie par défaut très simple
        return [
            {'lat': center_lat - 0.0001, 'lon': center_lon - 0.0001},
            {'lat': center_lat - 0.0001, 'lon': center_lon + 0.0001},
            {'lat': center_lat + 0.0001, 'lon': center_lon + 0.0001},
            {'lat': center_lat + 0.0001, 'lon': center_lon - 0.0001},
            {'lat': center_lat - 0.0001, 'lon': center_lon - 0.0001}
        ]


# ==============================================================================
# NORMALISATION AMÉLIORÉE DE DONNÉES
# ==============================================================================

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


def normalize_enhanced_building_data(building: Dict) -> Dict:
    """
    Normalise les données d'un bâtiment amélioré pour être plus robuste
    VERSION AMÉLIORÉE: conserve géométrie et métadonnées d'étages
    
    Args:
        building: Données bâtiment brutes avec enrichissements
        
    Returns:
        Dict: Données bâtiment normalisées avec enrichissements conservés
    """
    if not isinstance(building, dict):
        return create_fallback_enhanced_building('unknown_normalize')
    
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
    
    # === GÉOMÉTRIE AMÉLIORÉE ===
    geometry = building.get('geometry', [])
    has_precise_geometry = building.get('has_precise_geometry', len(geometry) >= 3)
    geometry_source = building.get('geometry_source', 'estimated')
    
    # Calcul surface précise si géométrie disponible
    if has_precise_geometry and geometry:
        # Conversion géométrie en coordonnées
        coordinates = []
        for point in geometry:
            if isinstance(point, dict) and 'lat' in point and 'lon' in point:
                coordinates.append((point['lat'], point['lon']))
        
        if len(coordinates) >= 3:
            polygon_area = calculate_precise_polygon_area(coordinates)
            polygon_perimeter = calculate_polygon_perimeter(coordinates)
            shape_complexity = calculate_shape_complexity(coordinates)
        else:
            polygon_area = safe_float_parse(building.get('surface_area_m2'), 100.0)
            polygon_perimeter = 0.0
            shape_complexity = 1.0
    else:
        polygon_area = safe_float_parse(building.get('surface_area_m2'), 100.0)
        polygon_perimeter = 0.0
        shape_complexity = 1.0
        # Créer géométrie approximative
        geometry = create_approximate_square_geometry(latitude, longitude, polygon_area)
        has_precise_geometry = False
        geometry_source = 'estimated'
    
    # === SURFACE ===
    # Utiliser la surface calculée du polygone si disponible
    surface_area = polygon_area if polygon_area > 0 else safe_float_parse(building.get('surface_area_m2'), 100.0)
    if surface_area <= 0 or surface_area > 100000:
        surface_area = 100.0
    
    # === ÉTAGES ET STRUCTURE ===
    floors_count = extract_floors_count_enhanced(building)
    levels_source = building.get('levels_source', 'estimated')
    levels_confidence = building.get('levels_confidence', 'low')
    height_m = safe_float_parse(building.get('height_m'))
    roof_levels = safe_int_parse(building.get('roof_levels'))
    
    # === CONSTRUCTION ===
    construction_material = building.get('construction_material')
    construction_year = extract_construction_year_safe(building)
    roof_material = building.get('roof_material')
    building_subtype = building.get('building_subtype')
    building_use = building.get('building_use')
    
    # === MÉTADONNÉES OSM ===
    osm_id = safe_get_building_field(building, 'osm_id')
    osm_type = building.get('osm_type', 'way')
    osm_timestamp = building.get('osm_timestamp')
    osm_version = safe_int_parse(building.get('osm_version'))
    osm_changeset = safe_int_parse(building.get('osm_changeset'))
    
    # === QUALITÉ ===
    validation_score = safe_float_parse(building.get('validation_score'), 0.5)
    if not (0.0 <= validation_score <= 1.0):
        validation_score = 0.5
    
    # === ASSEMBLAGE FINAL ===
    normalized = {
        # Identifiants
        'unique_id': str(building_id),
        'osm_id': osm_id,
        
        # Localisation
        'latitude': latitude,
        'longitude': longitude,
        'zone_name': safe_get_building_field(building, 'zone_name', 'unknown'),
        
        # Type et usage
        'building_type': building_type,
        'building_subtype': building_subtype,
        'building_use': building_use,
        
        # Géométrie et surface
        'geometry': geometry,
        'has_precise_geometry': has_precise_geometry,
        'geometry_source': geometry_source,
        'surface_area_m2': surface_area,
        'polygon_area_m2': polygon_area,
        'polygon_perimeter_m': polygon_perimeter,
        'shape_complexity': shape_complexity,
        
        # Étages et structure
        'floors_count': floors_count,
        'building_levels': floors_count,
        'levels_source': levels_source,
        'levels_confidence': levels_confidence,
        'height_m': height_m,
        'roof_levels': roof_levels,
        
        # Construction
        'construction_material': construction_material,
        'construction_year': construction_year,
        'roof_material': roof_material,
        
        # Métadonnées OSM
        'osm_type': osm_type,
        'osm_timestamp': osm_timestamp,
        'osm_version': osm_version,
        'osm_changeset': osm_changeset,
        
        # Qualité et source
        'validation_score': validation_score,
        'source': building.get('source', 'osm'),
        'tags': building.get('tags', {}),
        
        # Métadonnées de traitement
        'geometry_metadata': {
            'has_precise_geometry': has_precise_geometry,
            'geometry_source': geometry_source,
            'points_count': len(geometry),
            'polygon_area_m2': polygon_area,
            'polygon_perimeter_m': polygon_perimeter,
            'shape_complexity': shape_complexity
        },
        'floors_metadata': {
            'floors_count': floors_count,
            'source': levels_source,
            'confidence': levels_confidence,
            'height_m': height_m,
            'roof_levels': roof_levels
        }
    }
    
    return normalized


def extract_floors_count_enhanced(building: Dict) -> int:
    """
    Extrait le nombre d'étages de manière améliorée avec multiples sources
    
    Args:
        building: Données du bâtiment
        
    Returns:
        int: Nombre d'étages (minimum 1)
    """
    # Sources prioritaires d'étages
    floors_sources = [
        building.get('floors_count'),
        building.get('building_levels'),
        building.get('levels'),
        building.get('floors'),
        building.get('osm_tags', {}).get('building:levels'),
        building.get('tags', {}).get('building:levels'),
        building.get('osm_tags', {}).get('levels'),
        building.get('tags', {}).get('levels')
    ]
    
    for floors_value in floors_sources:
        if floors_value is not None:
            try:
                floors = int(float(floors_value))
                if 1 <= floors <= 200:  # Limites raisonnables
                    return floors
            except (ValueError, TypeError):
                continue
    
    # Estimation basée sur la hauteur si disponible
    height_m = safe_float_parse(building.get('height_m'))
    if height_m and height_m > 0:
        estimated_floors = max(1, round(height_m / 3.5))  # 3.5m par étage
        if estimated_floors <= 200:
            return estimated_floors
    
    # Estimation basée sur le type de bâtiment
    building_type = building.get('building_type', 'residential')
    return estimate_floors_by_type_advanced(building_type)


def estimate_floors_by_type_advanced(building_type: str) -> int:
    """
    Estime le nombre d'étages selon le type de bâtiment - VERSION AVANCÉE
    
    Args:
        building_type: Type de bâtiment
        
    Returns:
        int: Nombre d'étages estimé
    """
    import numpy as np
    
    type_probabilities = {
        'residential': {
            'floors': [1, 2, 3, 4, 5],
            'probabilities': [0.5, 0.3, 0.15, 0.04, 0.01]
        },
        'office': {
            'floors': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20],
            'probabilities': [0.1, 0.2, 0.15, 0.15, 0.1, 0.08, 0.06, 0.05, 0.04, 0.03, 0.02, 0.02]
        },
        'commercial': {
            'floors': [1, 2, 3, 4, 5, 6],
            'probabilities': [0.4, 0.25, 0.15, 0.1, 0.05, 0.05]
        },
        'industrial': {
            'floors': [1, 2, 3],
            'probabilities': [0.7, 0.2, 0.1]
        },
        'hospital': {
            'floors': [2, 3, 4, 5, 6, 7, 8],
            'probabilities': [0.1, 0.2, 0.25, 0.2, 0.15, 0.05, 0.05]
        },
        'school': {
            'floors': [1, 2, 3, 4, 5],
            'probabilities': [0.2, 0.3, 0.25, 0.15, 0.1]
        }
    }
    
    config = type_probabilities.get(building_type, type_probabilities['residential'])
    return np.random.choice(config['floors'], p=config['probabilities'])


def extract_construction_year_safe(building: Dict) -> Optional[int]:
    """
    Extrait l'année de construction de manière sécurisée
    
    Args:
        building: Données du bâtiment
        
    Returns:
        Optional[int]: Année de construction ou None
    """
    year_sources = [
        building.get('construction_year'),
        building.get('start_date'),
        building.get('osm_tags', {}).get('start_date'),
        building.get('tags', {}).get('start_date'),
        building.get('osm_tags', {}).get('building:year'),
        building.get('tags', {}).get('building:year')
    ]
    
    for year_value in year_sources:
        if year_value:
            try:
                # Extraction de l'année depuis différents formats
                year_str = str(year_value)
                # Chercher un pattern de 4 chiffres consécutifs
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', year_str)
                if year_match:
                    year = int(year_match.group())
                    if 1800 <= year <= 2030:
                        return year
            except (ValueError, TypeError):
                continue
    
    return None


def create_fallback_enhanced_building(identifier: str) -> Dict:
    """
    Crée un bâtiment de fallback amélioré avec géométrie
    
    Args:
        identifier: Identifiant unique
        
    Returns:
        Dict: Bâtiment de fallback avec toutes les propriétés améliorées
    """
    # Coordonnées par défaut (Kuala Lumpur)
    default_lat = 3.1390
    default_lon = 101.6869
    default_surface = 100.0
    
    # Géométrie approximative
    geometry = create_approximate_square_geometry(default_lat, default_lon, default_surface)
    
    return {
        'unique_id': f'fallback_{identifier}',
        'osm_id': None,
        'latitude': default_lat,
        'longitude': default_lon,
        'zone_name': 'unknown',
        'building_type': 'residential',
        'building_subtype': None,
        'building_use': None,
        'geometry': geometry,
        'has_precise_geometry': False,
        'geometry_source': 'fallback',
        'surface_area_m2': default_surface,
        'polygon_area_m2': default_surface,
        'polygon_perimeter_m': 40.0,  # Périmètre d'un carré de 100m²
        'shape_complexity': 1.0,
        'floors_count': 1,
        'building_levels': 1,
        'levels_source': 'fallback',
        'levels_confidence': 'low',
        'height_m': None,
        'roof_levels': None,
        'construction_material': None,
        'construction_year': None,
        'roof_material': None,
        'osm_type': 'way',
        'osm_timestamp': None,
        'osm_version': None,
        'osm_changeset': None,
        'validation_score': 0.3,
        'source': 'fallback',
        'tags': {},
        'geometry_metadata': {
            'has_precise_geometry': False,
            'geometry_source': 'fallback',
            'points_count': len(geometry),
            'polygon_area_m2': default_surface,
            'polygon_perimeter_m': 40.0,
            'shape_complexity': 1.0
        },
        'floors_metadata': {
            'floors_count': 1,
            'source': 'fallback',
            'confidence': 'low',
            'height_m': None,
            'roof_levels': None
        }
    }


def robust_building_list_validation(buildings: List[Dict]) -> List[Dict]:
    """
    Valide et normalise une liste de bâtiments améliorés de manière très robuste
    VERSION AMÉLIORÉE: conserve géométrie et métadonnées
    
    Args:
        buildings: Liste de bâtiments bruts avec enrichissements
        
    Returns:
        List[Dict]: Liste de bâtiments normalisés et enrichis
    """
    if not buildings or not isinstance(buildings, list):
        return []
    
    normalized_buildings = []
    
    for i, building in enumerate(buildings):
        try:
            # Normalisation améliorée
            normalized = normalize_enhanced_building_data(building)
            normalized_buildings.append(normalized)
            
        except Exception as e:
            # En cas d'erreur, créer un bâtiment par défaut amélioré
            logger = logging.getLogger(__name__)
            logger.warning(f"Erreur normalisation bâtiment amélioré {i}: {e}")
            
            fallback_building = create_fallback_enhanced_building(f'error_{i}')
            normalized_buildings.append(fallback_building)
    
    return normalized_buildings


# ==============================================================================
# MANIPULATION SÉCURISÉE DE DONNÉES (inchangées)
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
# FONCTIONS UTILITAIRES (inchangées mais compatibles)
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
# LOGGING ET SYSTÈME (inchangées)
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
    
    logger = logging.getLogger('malaysia_electricity_generator_enhanced')
    logger.info("✅ Système de logging amélioré initialisé")
    
    return logger


# ==============================================================================
# FONCTIONS D'ANALYSE GÉOMÉTRIQUE
# ==============================================================================

def analyze_building_geometry_quality(buildings: List[Dict]) -> Dict:
    """
    Analyse la qualité géométrique d'une liste de bâtiments
    
    Args:
        buildings: Liste des bâtiments avec géométrie
        
    Returns:
        Dict: Analyse de qualité géométrique
    """
    if not buildings:
        return {'error': 'Aucun bâtiment à analyser'}
    
    total = len(buildings)
    with_precise_geometry = 0
    with_floors_data = 0
    surface_stats = []
    complexity_stats = []
    validation_scores = []
    
    for building in buildings:
        # Géométrie précise
        if building.get('has_precise_geometry', False):
            with_precise_geometry += 1
        
        # Données d'étages
        if building.get('floors_count', 1) > 1:
            with_floors_data += 1
        
        # Surface
        surface = building.get('polygon_area_m2', building.get('surface_area_m2', 0))
        if surface > 0:
            surface_stats.append(surface)
        
        # Complexité
        complexity = building.get('shape_complexity', 1.0)
        complexity_stats.append(complexity)
        
        # Score validation
        score = building.get('validation_score', 0)
        if score > 0:
            validation_scores.append(score)
    
    # Calculs statistiques
    analysis = {
        'overview': {
            'total_buildings': total,
            'with_precise_geometry': with_precise_geometry,
            'with_floors_data': with_floors_data,
            'geometry_rate': round(with_precise_geometry / total, 3),
            'floors_rate': round(with_floors_data / total, 3)
        },
        'surface_analysis': {},
        'complexity_analysis': {},
        'validation_analysis': {}
    }
    
    # Analyse surfaces
    if surface_stats:
        analysis['surface_analysis'] = {
            'count': len(surface_stats),
            'total_m2': round(sum(surface_stats), 1),
            'average_m2': round(sum(surface_stats) / len(surface_stats), 1),
            'min_m2': round(min(surface_stats), 1),
            'max_m2': round(max(surface_stats), 1),
            'median_m2': round(sorted(surface_stats)[len(surface_stats)//2], 1)
        }
    
    # Analyse complexité
    if complexity_stats:
        analysis['complexity_analysis'] = {
            'average': round(sum(complexity_stats) / len(complexity_stats), 3),
            'min': round(min(complexity_stats), 3),
            'max': round(max(complexity_stats), 3),
            'simple_buildings': sum(1 for c in complexity_stats if c <= 1.2),
            'complex_buildings': sum(1 for c in complexity_stats if c >= 2.0)
        }
    
    # Analyse validation
    if validation_scores:
        analysis['validation_analysis'] = {
            'average_score': round(sum(validation_scores) / len(validation_scores), 3),
            'min_score': round(min(validation_scores), 3),
            'max_score': round(max(validation_scores), 3),
            'high_quality': sum(1 for s in validation_scores if s >= 0.8),
            'medium_quality': sum(1 for s in validation_scores if 0.5 <= s < 0.8),
            'low_quality': sum(1 for s in validation_scores if s < 0.5)
        }
    
    return analysis


def generate_geometry_summary_report(buildings: List[Dict]) -> Dict:
    """
    Génère un rapport de synthèse géométrique des bâtiments
    
    Args:
        buildings: Liste des bâtiments avec géométrie
        
    Returns:
        Dict: Rapport complet
    """
    if not buildings:
        return {'error': 'Aucun bâtiment à analyser'}
    
    # Analyse géométrique
    geometry_analysis = analyze_building_geometry_quality(buildings)
    
    # Répartition par type avec géométrie
    type_geometry_distribution = {}
    for building in buildings:
        btype = building.get('building_type', 'unknown')
        has_geom = building.get('has_precise_geometry', False)
        
        if btype not in type_geometry_distribution:
            type_geometry_distribution[btype] = {
                'total': 0,
                'with_geometry': 0,
                'geometry_rate': 0.0
            }
        
        type_geometry_distribution[btype]['total'] += 1
        if has_geom:
            type_geometry_distribution[btype]['with_geometry'] += 1
    
    # Calcul des taux
    for btype, data in type_geometry_distribution.items():
        if data['total'] > 0:
            data['geometry_rate'] = round(data['with_geometry'] / data['total'], 3)
    
    return {
        'metadata': {
            'total_buildings': len(buildings),
            'analysis_timestamp': datetime.now().isoformat(),
            'enhanced_features': True
        },
        'geometry_analysis': geometry_analysis,
        'type_geometry_distribution': type_geometry_distribution,
        'recommendations': _generate_geometry_recommendations(geometry_analysis),
        'report_version': '1.1.0'
    }


def _generate_geometry_recommendations(analysis: Dict) -> List[str]:
    """
    Génère des recommandations basées sur l'analyse géométrique
    
    Args:
        analysis: Résultats de l'analyse
        
    Returns:
        List[str]: Liste de recommandations
    """
    recommendations = []
    
    overview = analysis.get('overview', {})
    geometry_rate = overview.get('geometry_rate', 0)
    
    if geometry_rate < 0.3:
        recommendations.append("Améliorer l'extraction géométrique des bâtiments OSM")
    elif geometry_rate < 0.7:
        recommendations.append("Géométrie partiellement disponible - considérer des sources complémentaires")
    else:
        recommendations.append("Excellente couverture géométrique")
    
    floors_rate = overview.get('floors_rate', 0)
    if floors_rate < 0.2:
        recommendations.append("Enrichir les données d'étages via des sources additionnelles")
    
    validation = analysis.get('validation_analysis', {})
    if validation and validation.get('average_score', 0) < 0.6:
        recommendations.append("Améliorer la qualité des données de validation")
    
    complexity = analysis.get('complexity_analysis', {})
    if complexity and complexity.get('complex_buildings', 0) > complexity.get('simple_buildings', 0):
        recommendations.append("Beaucoup de bâtiments complexes - optimiser l'analyse de forme")
    
    return recommendations