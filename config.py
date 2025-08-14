#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURATION CENTRALISÉE - MALAYSIA ELECTRICITY GENERATOR
===========================================================

Configuration centralisée pour éviter les doublons de code.
"""

import os
from pathlib import Path
from datetime import datetime


# ==============================================================================
# CONFIGURATION PROJET
# ==============================================================================

class AppConfig:
    """Configuration générale de l'application"""
    
    # Chemins du projet
    PROJECT_ROOT = Path(__file__).parent.absolute()
    EXPORTS_DIR = PROJECT_ROOT / 'exports'
    LOGS_DIR = PROJECT_ROOT / 'logs'
    STATIC_DIR = PROJECT_ROOT / 'static'
    TEMPLATES_DIR = PROJECT_ROOT / 'templates'
    
    # Configuration Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'malaysia-electricity-dev-key')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # Création des dossiers
    @classmethod
    def init_directories(cls):
        """Crée les dossiers nécessaires"""
        for directory in [cls.EXPORTS_DIR, cls.LOGS_DIR]:
            directory.mkdir(exist_ok=True)


# ==============================================================================
# CONFIGURATION MALAYSIA
# ==============================================================================

class MalaysiaConfig:
    """Configuration spécifique à la Malaysia"""
    
    # Limites géographiques
    BOUNDS = {
        'north': 7.5,
        'south': 0.5,
        'east': 119.5,
        'west': 99.5
    }
    
    # Zones administratives
    ZONES = {
        'malaysia': {
            'name': 'Malaysia (Pays entier)',
            'bbox': [99.5, 0.5, 119.5, 7.5],
            'osm_relation_id': '2108121'
        },
        'kuala_lumpur': {
            'name': 'Kuala Lumpur',
            'bbox': [101.6, 3.05, 101.75, 3.25],
            'osm_relation_id': '1124314'
        },
        'selangor': {
            'name': 'Selangor',
            'bbox': [100.8, 2.8, 102.0, 3.8],
            'osm_relation_id': '1876107'
        },
        'johor': {
            'name': 'Johor',
            'bbox': [102.8, 1.2, 104.8, 2.8],
            'osm_relation_id': '1876099'
        },
        'penang': {
            'name': 'Penang',
            'bbox': [100.1, 5.1, 100.6, 5.5],
            'osm_relation_id': '1876102'
        }
    }
    
    # Types de bâtiments avec consommation électrique ET eau
    BUILDING_TYPES = {
        'residential': {
            'base_consumption_kwh_m2_day': 0.8,
            'base_water_consumption_l_m2_day': 150,
            'osm_tags': ['residential', 'house', 'apartments', 'terrace'],
            'description': 'Bâtiments résidentiels'
        },
        'commercial': {
            'base_consumption_kwh_m2_day': 1.5,
            'base_water_consumption_l_m2_day': 80,
            'osm_tags': ['commercial', 'retail', 'shop', 'mall'],
            'description': 'Bâtiments commerciaux'
        },
        'office': {
            'base_consumption_kwh_m2_day': 2.0,
            'base_water_consumption_l_m2_day': 60,
            'osm_tags': ['office', 'government', 'civic'],
            'description': 'Bureaux et administrations'
        },
        'industrial': {
            'base_consumption_kwh_m2_day': 3.5,
            'base_water_consumption_l_m2_day': 200,
            'osm_tags': ['industrial', 'warehouse', 'factory'],
            'description': 'Bâtiments industriels'
        },
        'school': {
            'base_consumption_kwh_m2_day': 1.2,
            'base_water_consumption_l_m2_day': 100,
            'osm_tags': ['school', 'university', 'college'],
            'description': 'Établissements scolaires'
        },
        'hospital': {
            'base_consumption_kwh_m2_day': 4.0,
            'base_water_consumption_l_m2_day': 300,
            'osm_tags': ['hospital', 'clinic', 'healthcare'],
            'description': 'Établissements de santé'
        }
    }
    
    @classmethod
    def get_all_zones_list(cls):
        """Retourne la liste formatée des zones"""
        zones = []
        for zone_id, zone_config in cls.ZONES.items():
            zones.append({
                'id': zone_id,
                'name': zone_config['name'],
                'bbox': zone_config['bbox']
            })
        return zones
    
    @classmethod
    def get_zone_config(cls, zone_name):
        """Retourne la configuration d'une zone"""
        return cls.ZONES.get(zone_name)
    
    @classmethod
    def get_building_type_config(cls, building_type):
        """Retourne la configuration d'un type de bâtiment"""
        return cls.BUILDING_TYPES.get(building_type, cls.BUILDING_TYPES['residential'])


# ==============================================================================
# CONFIGURATION MÉTÉO
# ==============================================================================

class WeatherConfig:
    """Configuration pour la génération météorologique"""
    
    # Colonnes météo (33 colonnes spécifiées)
    WEATHER_COLUMNS = [
        'timestamp', 'temperature_2m', 'relative_humidity_2m', 'dew_point_2m',
        'apparent_temperature', 'precipitation', 'rain', 'snowfall', 'snow_depth',
        'weather_code', 'pressure_msl', 'surface_pressure', 'cloud_cover',
        'cloud_cover_low', 'cloud_cover_mid', 'cloud_cover_high',
        'et0_fao_evapotranspiration', 'vapour_pressure_deficit', 'wind_speed_10m',
        'wind_direction_10m', 'wind_gusts_10m', 'soil_temperature_0_to_7cm',
        'soil_temperature_7_to_28cm', 'soil_moisture_0_to_7cm',
        'soil_moisture_7_to_28cm', 'is_day', 'sunshine_duration',
        'shortwave_radiation', 'direct_radiation', 'diffuse_radiation',
        'direct_normal_irradiance', 'terrestrial_radiation', 'location_id'
    ]
    
    # Paramètres climatiques Malaysia (tropical)
    CLIMATE_PARAMS = {
        'base_temperature': 27.0,  # °C
        'base_humidity': 0.8,      # 80%
        'base_pressure': 1013.25,  # hPa
        'temperature_variation': 5.0,  # Variation diurne
        'seasonal_variation': 2.0,     # Variation saisonnière
        'precipitation_prob_afternoon': 0.3,  # Probabilité pluie après-midi
        'precipitation_prob_night': 0.1       # Probabilité pluie nuit
    }


# ==============================================================================
# CONFIGURATION EXPORT
# ==============================================================================

class ExportConfig:
    """Configuration pour l'export des données"""
    
    # Formats supportés
    SUPPORTED_FORMATS = ['csv', 'parquet', 'xlsx']
    
    # Noms de fichiers par défaut
    DEFAULT_FILENAMES = {
        'buildings': 'buildings_metadata',
        'consumption': 'electricity_consumption', 
        'weather': 'weather_simulation'
    }
    
    # Configuration par format
    FORMAT_CONFIG = {
        'csv': {
            'separator': ',',
            'encoding': 'utf-8',
            'extension': '.csv'
        },
        'parquet': {
            'compression': 'snappy',
            'extension': '.parquet'
        },
        'xlsx': {
            'sheet_name': 'Data',
            'extension': '.xlsx'
        }
    }
    
    @classmethod
    def get_timestamped_filename(cls, base_name, file_format):
        """Génère un nom de fichier avec timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        extension = cls.FORMAT_CONFIG[file_format]['extension']
        return f"{base_name}_{timestamp}{extension}"


# ==============================================================================
# CONFIGURATION OSM
# ==============================================================================

class OSMConfig:
    """Configuration pour OpenStreetMap"""
    
    # Configuration Overpass API
    OVERPASS_CONFIG = {
        'timeout': 60,
        'user_agent': 'Malaysia-Electricity-Generator/3.0'
    }
    
    # Tags OSM à rechercher
    BUILDING_QUERY_TAGS = [
        'building~"."',
        'landuse~"residential|commercial|industrial"'
    ]
    
    @classmethod
    def build_overpass_query(cls, bbox):
        """Construit une requête Overpass"""
        south, west, north, east = bbox
        
        query = f"""
        [out:json][timeout:{cls.OVERPASS_CONFIG['timeout']}];
        (
          way["building"~"."](bbox:{south},{west},{north},{east});
          relation["building"~"."](bbox:{south},{west},{north},{east});
        );
        out geom;
        """
        return query


# Initialisation des dossiers au chargement du module
AppConfig.init_directories()