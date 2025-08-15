#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATEURS - UTILS MODULE
===========================

Fonctions de validation centralisées pour l'application.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

from config import MalaysiaConfig, ExportConfig

logger = logging.getLogger(__name__)


# ==============================================================================
# VALIDATEURS GÉOGRAPHIQUES
# ==============================================================================

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Valide des coordonnées géographiques
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        bool: True si valides
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        # Limites globales
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False
        
        return True
        
    except (ValueError, TypeError):
        return False


def validate_malaysia_coordinates(latitude: float, longitude: float) -> bool:
    """
    Valide que les coordonnées sont dans les limites Malaysia
    
    Args:
        latitude: Latitude
        longitude: Longitude
        
    Returns:
        bool: True si dans Malaysia
    """
    if not validate_coordinates(latitude, longitude):
        return False
    
    bounds = MalaysiaConfig.BOUNDS
    return (bounds['south'] <= latitude <= bounds['north'] and 
            bounds['west'] <= longitude <= bounds['east'])


def validate_bbox(bbox: List[float]) -> bool:
    """
    Valide une bounding box
    
    Args:
        bbox: [west, south, east, north]
        
    Returns:
        bool: True si valide
    """
    try:
        if len(bbox) != 4:
            return False
        
        west, south, east, north = bbox
        
        # Validation coordonnées
        if not validate_coordinates(south, west) or not validate_coordinates(north, east):
            return False
        
        # Validation ordre
        if west >= east or south >= north:
            return False
        
        return True
        
    except (ValueError, TypeError, IndexError):
        return False


# ==============================================================================
# VALIDATEURS TEMPORELS
# ==============================================================================

def validate_date_string(date_string: str) -> bool:
    """
    Valide une chaîne de date au format YYYY-MM-DD
    
    Args:
        date_string: Date à valider
        
    Returns:
        bool: True si valide
    """
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Valide une plage de dates
    
    Args:
        start_date: Date début (YYYY-MM-DD)
        end_date: Date fin (YYYY-MM-DD)
        
    Returns:
        bool: True si valide
    """
    try:
        if not validate_date_string(start_date) or not validate_date_string(end_date):
            return False
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Date de fin après début
        if end <= start:
            return False
        
        # Limites raisonnables (max 2 ans)
        if (end - start).days > 730:
            return False
        
        # Pas dans le futur lointain
        if end > datetime.now() + timedelta(days=365):
            return False
        
        return True
        
    except ValueError:
        return False


def validate_frequency(frequency: str) -> bool:
    """
    Valide une fréquence pandas
    
    Args:
        frequency: Fréquence (ex: '1H', '15T')
        
    Returns:
        bool: True si valide
    """
    valid_frequencies = ['15T', '30T', '1H', '2H', '3H', '6H', '12H', 'D', 'W', 'M']
    return frequency in valid_frequencies


# ==============================================================================
# VALIDATEURS MÉTIER
# ==============================================================================

def validate_zone_name(zone_name: str) -> bool:
    """
    Valide un nom de zone Malaysia
    
    Args:
        zone_name: Nom de la zone
        
    Returns:
        bool: True si valide
    """
    if not zone_name or not isinstance(zone_name, str):
        return False
    
    return zone_name.lower() in [zone.lower() for zone in MalaysiaConfig.ZONES.keys()]


def validate_building_type(building_type: str) -> bool:
    """
    Valide un type de bâtiment
    
    Args:
        building_type: Type à valider
        
    Returns:
        bool: True si valide
    """
    if not building_type or not isinstance(building_type, str):
        return False
    
    return building_type.lower() in [bt.lower() for bt in MalaysiaConfig.BUILDING_TYPES.keys()]


def validate_building_data(building: Dict) -> Dict:
    """
    Valide les données d'un bâtiment
    
    Args:
        building: Données du bâtiment
        
    Returns:
        Dict: Résultat de validation avec erreurs
    """
    errors = []
    warnings = []
    
    # Validation ID
    if not building.get('id'):
        errors.append("ID manquant")
    
    # Validation coordonnées
    lat = building.get('latitude')
    lon = building.get('longitude')
    if lat is None or lon is None:
        errors.append("Coordonnées manquantes")
    elif not validate_malaysia_coordinates(lat, lon):
        errors.append("Coordonnées hors Malaysia")
    
    # Validation type
    building_type = building.get('building_type')
    if not validate_building_type(building_type):
        errors.append("Type de bâtiment invalide")
    
    # Validation surface
    surface = building.get('surface_area_m2', 0)
    if surface <= 0:
        errors.append("Surface invalide")
    elif surface < 10:
        warnings.append("Surface très petite")
    elif surface > 50000:
        warnings.append("Surface très grande")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_building_list(buildings: List[Dict]) -> Dict:
    """
    Valide une liste de bâtiments
    
    Args:
        buildings: Liste des bâtiments
        
    Returns:
        Dict: Résultat de validation globale
    """
    if not buildings:
        return {
            'valid': False,
            'error': 'Liste vide',
            'buildings_count': 0
        }
    
    errors = []
    warnings = []
    valid_count = 0
    
    for i, building in enumerate(buildings):
        validation = validate_building_data(building)
        
        if validation['valid']:
            valid_count += 1
        else:
            for error in validation['errors']:
                errors.append(f"Bâtiment {i}: {error}")
        
        for warning in validation['warnings']:
            warnings.append(f"Bâtiment {i}: {warning}")
    
    # Limites de performance
    if len(buildings) > 50000:
        warnings.append("Très grand nombre de bâtiments (>50k)")
    
    return {
        'valid': len(errors) == 0,
        'buildings_count': len(buildings),
        'valid_buildings': valid_count,
        'errors': errors[:10],  # Limite affichage
        'warnings': warnings[:10],
        'validation_rate': valid_count / len(buildings) if buildings else 0
    }


# ==============================================================================
# VALIDATEURS DONNÉES
# ==============================================================================

def validate_consumption_data(consumption_df: pd.DataFrame) -> Dict:
    """
    Valide un DataFrame de consommation
    
    Args:
        consumption_df: DataFrame à valider
        
    Returns:
        Dict: Résultat de validation
    """
    if consumption_df.empty:
        return {
            'valid': False,
            'error': 'DataFrame vide'
        }
    
    errors = []
    warnings = []
    
    # Validation colonnes requises
    required_columns = ['building_id', 'timestamp', 'consumption_kwh']
    missing_columns = [col for col in required_columns if col not in consumption_df.columns]
    
    if missing_columns:
        errors.append(f"Colonnes manquantes: {missing_columns}")
    
    # Validation données
    if 'consumption_kwh' in consumption_df.columns:
        negative_count = (consumption_df['consumption_kwh'] < 0).sum()
        if negative_count > 0:
            warnings.append(f"{negative_count} valeurs négatives")
        
        extreme_count = (consumption_df['consumption_kwh'] > 100).sum()
        if extreme_count > 0:
            warnings.append(f"{extreme_count} valeurs extrêmes (>100 kWh)")
    
    # Validation timestamps
    if 'timestamp' in consumption_df.columns:
        try:
            pd.to_datetime(consumption_df['timestamp'])
        except:
            errors.append("Timestamps invalides")
    
    return {
        'valid': len(errors) == 0,
        'total_records': len(consumption_df),
        'errors': errors,
        'warnings': warnings
    }


def validate_weather_data(weather_df: pd.DataFrame) -> Dict:
    """
    Valide un DataFrame météorologique
    
    Args:
        weather_df: DataFrame à valider
        
    Returns:
        Dict: Résultat de validation
    """
    if weather_df.empty:
        return {
            'valid': False,
            'error': 'DataFrame vide'
        }
    
    errors = []
    warnings = []
    
    # Validation colonnes requises
    required_columns = ['timestamp', 'temperature_2m', 'location_id']
    missing_columns = [col for col in required_columns if col not in weather_df.columns]
    
    if missing_columns:
        errors.append(f"Colonnes manquantes: {missing_columns}")
    
    # Validation températures
    if 'temperature_2m' in weather_df.columns:
        temp_range = weather_df['temperature_2m'].agg(['min', 'max'])
        if temp_range['min'] < -50 or temp_range['max'] > 60:
            warnings.append("Températures hors limites réalistes")
    
    # Validation humidité
    if 'relative_humidity_2m' in weather_df.columns:
        humidity_issues = ((weather_df['relative_humidity_2m'] < 0) | 
                          (weather_df['relative_humidity_2m'] > 1)).sum()
        if humidity_issues > 0:
            errors.append(f"{humidity_issues} valeurs d'humidité invalides")
    
    return {
        'valid': len(errors) == 0,
        'total_records': len(weather_df),
        'errors': errors,
        'warnings': warnings
    }


# ==============================================================================
# VALIDATEURS EXPORT
# ==============================================================================

def validate_export_format(export_format: str) -> bool:
    """
    Valide un format d'export
    
    Args:
        export_format: Format à valider
        
    Returns:
        bool: True si valide
    """
    if not export_format or not isinstance(export_format, str):
        return False
    
    return export_format.lower() in ExportConfig.SUPPORTED_FORMATS


def validate_filename(filename: str) -> bool:
    """
    Valide un nom de fichier
    
    Args:
        filename: Nom de fichier à valider
        
    Returns:
        bool: True si valide
    """
    if not filename or not isinstance(filename, str):
        return False
    
    # Caractères interdits
    forbidden_chars = '<>:"/\\|?*'
    if any(char in filename for char in forbidden_chars):
        return False
    
    # Longueur raisonnable
    if len(filename) > 255:
        return False
    
    return True


def validate_export_request(
    buildings_count: int,
    consumption_count: int,
    weather_count: int,
    water_count: int,
    export_format: str
) -> Dict:
    """
    Valide une demande d'export complète
    
    Args:
        buildings_count: Nombre de bâtiments
        consumption_count: Nombre de points consommation
        weather_count: Nombre de points météo
        water_count: Nombre de points eau
        export_format: Format d'export
        
    Returns:
        Dict: Résultat de validation
    """
    errors = []
    warnings = []
    
    # Validation format
    if not validate_export_format(export_format):
        errors.append(f"Format non supporté: {export_format}")
    
    # Validation données
    if buildings_count == 0:
        errors.append("Aucun bâtiment à exporter")
    
    total_points = consumption_count + weather_count + water_count
    if total_points == 0:
        warnings.append("Aucune donnée temporelle à exporter")
    
    # Vérification limites
    if buildings_count > 100000:
        warnings.append("Très grand nombre de bâtiments")
    
    if total_points > 5000000:  # 5M points
        warnings.append("Volume très important de données temporelles")
    
    # Estimation taille
    estimated_size_mb = _estimate_export_size(
        buildings_count, consumption_count, weather_count, water_count, export_format
    )
    
    if estimated_size_mb > 1000:  # 1GB
        warnings.append(f"Taille estimée très importante: {estimated_size_mb:.0f}MB")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'estimated_size_mb': estimated_size_mb,
        'total_records': buildings_count + total_points
    }


def _estimate_export_size(
    buildings_count: int,
    consumption_count: int,
    weather_count: int,
    water_count: int,
    export_format: str
) -> float:
    """
    Estime la taille d'export en MB
    
    Args:
        buildings_count: Nombre de bâtiments
        consumption_count: Nombre de points consommation
        weather_count: Nombre de points météo
        water_count: Nombre de points eau
        export_format: Format d'export
        
    Returns:
        float: Taille estimée en MB
    """
    # Taille par enregistrement en bytes
    size_estimates = {
        'csv': {
            'buildings': 300,
            'consumption': 200,
            'weather': 500,
            'water': 180
        },
        'parquet': {
            'buildings': 120,
            'consumption': 80,
            'weather': 200,
            'water': 70
        },
        'xlsx': {
            'buildings': 400,
            'consumption': 250,
            'weather': 600,
            'water': 220
        }
    }
    
    estimates = size_estimates.get(export_format, size_estimates['csv'])
    
    total_bytes = (
        buildings_count * estimates['buildings'] +
        consumption_count * estimates['consumption'] +
        weather_count * estimates['weather'] +
        water_count * estimates['water']
    )
    
    return total_bytes / (1024 * 1024)  # Conversion en MB


# ==============================================================================
# VALIDATEURS SPÉCIALISÉS
# ==============================================================================

def validate_generation_parameters(
    buildings: List[Dict],
    start_date: str,
    end_date: str,
    frequency: str,
    weather_stations: int
) -> Dict:
    """
    Valide les paramètres de génération de données
    
    Args:
        buildings: Liste des bâtiments
        start_date: Date début
        end_date: Date fin
        frequency: Fréquence
        weather_stations: Nombre de stations météo
        
    Returns:
        Dict: Résultat de validation complète
    """
    errors = []
    warnings = []
    
    # Validation bâtiments
    building_validation = validate_building_list(buildings)
    if not building_validation['valid']:
        errors.extend(building_validation['errors'])
    
    # Validation dates
    if not validate_date_range(start_date, end_date):
        errors.append("Plage de dates invalide")
    else:
        # Vérification durée
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        duration_days = (end - start).days
        
        if duration_days > 365:
            warnings.append("Période très longue (>1 an)")
        elif duration_days < 1:
            errors.append("Période trop courte")
    
    # Validation fréquence
    if not validate_frequency(frequency):
        errors.append(f"Fréquence non supportée: {frequency}")
    
    # Validation stations météo
    if not isinstance(weather_stations, int) or weather_stations < 1:
        errors.append("Nombre de stations météo invalide")
    elif weather_stations > 50:
        warnings.append("Nombre très élevé de stations météo")
    
    # Estimation charge de travail
    if buildings and len(buildings) > 0:
        duration_days = (datetime.strptime(end_date, '%Y-%m-%d') - 
                        datetime.strptime(start_date, '%Y-%m-%d')).days
        
        # Points par jour selon fréquence
        points_per_day = {
            '15T': 96, '30T': 48, '1H': 24, '2H': 12, 
            '3H': 8, '6H': 4, '12H': 2, 'D': 1
        }.get(frequency, 24)
        
        total_consumption_points = len(buildings) * duration_days * points_per_day
        total_weather_points = weather_stations * duration_days * points_per_day
        
        if total_consumption_points > 10000000:  # 10M points
            warnings.append("Volume très important de données électriques")
        
        if total_weather_points > 1000000:  # 1M points
            warnings.append("Volume très important de données météo")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'buildings_validation': building_validation
    }


def validate_water_consumption_data(water_df: pd.DataFrame) -> Dict:
    """
    Valide un DataFrame de consommation d'eau
    
    Args:
        water_df: DataFrame à valider
        
    Returns:
        Dict: Résultat de validation
    """
    if water_df.empty:
        return {
            'valid': False,
            'error': 'DataFrame vide'
        }
    
    errors = []
    warnings = []
    
    # Validation colonnes requises
    required_columns = ['building_id', 'timestamp', 'water_consumption_liters']
    missing_columns = [col for col in required_columns if col not in water_df.columns]
    
    if missing_columns:
        errors.append(f"Colonnes manquantes: {missing_columns}")
    
    # Validation données eau
    if 'water_consumption_liters' in water_df.columns:
        negative_count = (water_df['water_consumption_liters'] < 0).sum()
        if negative_count > 0:
            warnings.append(f"{negative_count} valeurs négatives")
        
        extreme_count = (water_df['water_consumption_liters'] > 10000).sum()  # >10k L/h
        if extreme_count > 0:
            warnings.append(f"{extreme_count} valeurs extrêmes (>10k L/h)")
        
        zero_count = (water_df['water_consumption_liters'] == 0).sum()
        if zero_count > len(water_df) * 0.5:  # Plus de 50% à zéro
            warnings.append("Beaucoup de valeurs nulles")
    
    # Validation intensité eau
    if 'consumption_intensity_l_m2' in water_df.columns:
        intensity_issues = (water_df['consumption_intensity_l_m2'] > 50).sum()  # >50 L/m²/h
        if intensity_issues > 0:
            warnings.append(f"{intensity_issues} intensités eau très élevées")
    
    return {
        'valid': len(errors) == 0,
        'total_records': len(water_df),
        'errors': errors,
        'warnings': warnings
    }


# ==============================================================================
# VALIDATEURS SYSTÈME
# ==============================================================================

def validate_system_resources(
    estimated_memory_mb: float,
    estimated_processing_time_minutes: float
) -> Dict:
    """
    Valide les ressources système nécessaires
    
    Args:
        estimated_memory_mb: Mémoire estimée en MB
        estimated_processing_time_minutes: Temps de traitement estimé
        
    Returns:
        Dict: Validation des ressources
    """
    errors = []
    warnings = []
    
    # Limites mémoire
    if estimated_memory_mb > 8192:  # 8GB
        errors.append("Mémoire requise excessive (>8GB)")
    elif estimated_memory_mb > 4096:  # 4GB
        warnings.append("Mémoire requise élevée (>4GB)")
    
    # Limites temps de traitement
    if estimated_processing_time_minutes > 60:  # 1h
        warnings.append("Temps de traitement très long (>1h)")
    elif estimated_processing_time_minutes > 30:  # 30min
        warnings.append("Temps de traitement long (>30min)")
    
    return {
        'acceptable': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'estimated_memory_mb': estimated_memory_mb,
        'estimated_time_minutes': estimated_processing_time_minutes
    }


def validate_api_request(request_data: Dict, required_fields: List[str]) -> Dict:
    """
    Valide une requête API générique
    
    Args:
        request_data: Données de la requête
        required_fields: Champs requis
        
    Returns:
        Dict: Résultat de validation
    """
    errors = []
    
    if not isinstance(request_data, dict):
        errors.append("Format de requête invalide")
        return {'valid': False, 'errors': errors}
    
    # Validation champs requis
    missing_fields = [field for field in required_fields if field not in request_data]
    if missing_fields:
        errors.append(f"Champs manquants: {missing_fields}")
    
    # Validation types de base
    for field, value in request_data.items():
        if value is None:
            continue
        
        # Validation selon le nom du champ
        if 'date' in field.lower() and isinstance(value, str):
            if not validate_date_string(value):
                errors.append(f"Date invalide: {field}")
        
        elif 'frequency' in field.lower() and isinstance(value, str):
            if not validate_frequency(value):
                errors.append(f"Fréquence invalide: {field}")
        
        elif 'format' in field.lower() and isinstance(value, str):
            if not validate_export_format(value):
                errors.append(f"Format invalide: {field}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'request_data': request_data
    }