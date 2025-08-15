#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURATION CENTRALISÉE - MALAYSIA ELECTRICITY GENERATOR
===========================================================

Configuration unique et centralisée. Remplace constants.py pour éviter les redondances.
"""

import os
from pathlib import Path
from datetime import datetime


# ==============================================================================
# CONFIGURATION PROJET
# ==============================================================================

class AppConfig:
    """Configuration générale de l'application"""
    
    # Métadonnées application
    NAME = 'Malaysia Electricity Data Generator'
    VERSION = '3.0.0'
    DESCRIPTION = 'Générateur de données électriques pour Malaysia avec architecture factorisée'
    
    # Chemins du projet
    PROJECT_ROOT = Path(__file__).parent.absolute()
    EXPORTS_DIR = PROJECT_ROOT / 'exports'
    LOGS_DIR = PROJECT_ROOT / 'logs'
    STATIC_DIR = PROJECT_ROOT / 'static'
    TEMPLATES_DIR = PROJECT_ROOT / 'templates'
    
    # Configuration Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'malaysia-electricity-dev-key')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # Limites système (centralisées)
    SYSTEM_LIMITS = {
        'max_buildings_per_zone': 50000,
        'max_timeseries_points': 1000000,
        'max_weather_stations': 50,
        'max_generation_days': 365,
        'max_export_file_size_mb': 2000,
        'max_memory_usage_mb': 4000,
        'max_processing_time_minutes': 30
    }
    
    # Messages standardisés (fusionnés depuis constants.py)
    MESSAGES = {
        'errors': {
            'invalid_coordinates': "Coordonnées invalides pour Malaysia",
            'invalid_building_type': "Type de bâtiment non reconnu",
            'invalid_date_range': "Plage de dates invalide",
            'invalid_frequency': "Fréquence non supportée",
            'file_too_large': "Fichier trop volumineux",
            'missing_required_field': "Champ requis manquant",
            'data_inconsistent': "Données incohérentes détectées",
            'generation_failed': "Échec de la génération",
            'export_failed': "Échec de l'export",
            'validation_failed': "Validation des données échouée",
            'insufficient_memory': "Mémoire insuffisante",
            'timeout_exceeded': "Délai d'attente dépassé"
        },
        'success': {
            'data_generated': "Données générées avec succès",
            'data_exported': "Données exportées avec succès",
            'buildings_loaded': "Bâtiments chargés avec succès",
            'validation_passed': "Validation réussie",
            'session_completed': "Session terminée avec succès"
        },
        'info': {
            'processing': "Traitement en cours...",
            'loading_osm': "Chargement des données OSM...",
            'generating_data': "Génération des données électriques...",
            'generating_weather': "Génération des données météorologiques...",
            'exporting_data': "Export des données...",
            'validating_data': "Validation des données..."
        }
    }
    
    @classmethod
    def init_directories(cls):
        """Crée les dossiers nécessaires"""
        for directory in [cls.EXPORTS_DIR, cls.LOGS_DIR]:
            directory.mkdir(exist_ok=True)


# ==============================================================================
# CONFIGURATION MALAYSIA (centralisée et optimisée)
# ==============================================================================

class MalaysiaConfig:
    """Configuration spécifique à la Malaysia - VERSION UNIQUE"""
    
    # Limites géographiques (une seule définition)
    BOUNDS = {
        'north': 7.5, 'south': 0.5, 'east': 119.5, 'west': 99.5
    }
    
    # Coordonnées principales villes (centralisées)
    MAJOR_CITIES = {
        'kuala_lumpur': {'lat': 3.1390, 'lon': 101.6869},
        'george_town': {'lat': 5.4164, 'lon': 100.3327},
        'johor_bahru': {'lat': 1.4927, 'lon': 103.7414},
        'shah_alam': {'lat': 3.0733, 'lon': 101.5185},
        'kota_kinabalu': {'lat': 5.9804, 'lon': 116.0735},
        'kuching': {'lat': 1.5533, 'lon': 110.3592}
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
            'osm_relation_id': '4445131'
        }
    }
    
    # Types de bâtiments UNIFIÉS (électricité + eau)
    BUILDING_TYPES = {
        'residential': {
            'base_consumption_kwh_m2_day': 0.8,
            'base_water_consumption_l_m2_day': 150,
            'osm_tags': ['residential', 'house', 'apartments', 'terrace'],
            'description': 'Bâtiments résidentiels',
            'typical_size_m2': (50, 300),
            'occupancy_hours': (16, 24)
        },
        'commercial': {
            'base_consumption_kwh_m2_day': 1.5,
            'base_water_consumption_l_m2_day': 80,
            'osm_tags': ['commercial', 'retail', 'shop', 'mall'],
            'description': 'Bâtiments commerciaux',
            'typical_size_m2': (100, 2000),
            'occupancy_hours': (10, 14)
        },
        'office': {
            'base_consumption_kwh_m2_day': 2.0,
            'base_water_consumption_l_m2_day': 60,
            'osm_tags': ['office', 'government', 'civic'],
            'description': 'Bureaux et administrations',
            'typical_size_m2': (200, 5000),
            'occupancy_hours': (8, 10)
        },
        'industrial': {
            'base_consumption_kwh_m2_day': 3.5,
            'base_water_consumption_l_m2_day': 200,
            'osm_tags': ['industrial', 'warehouse', 'factory'],
            'description': 'Bâtiments industriels',
            'typical_size_m2': (500, 10000),
            'occupancy_hours': (16, 24)
        },
        'school': {
            'base_consumption_kwh_m2_day': 1.2,
            'base_water_consumption_l_m2_day': 100,
            'osm_tags': ['school', 'university', 'college'],
            'description': 'Établissements scolaires',
            'typical_size_m2': (300, 3000),
            'occupancy_hours': (8, 12)
        },
        'hospital': {
            'base_consumption_kwh_m2_day': 4.0,
            'base_water_consumption_l_m2_day': 300,
            'osm_tags': ['hospital', 'clinic', 'healthcare'],
            'description': 'Établissements de santé',
            'typical_size_m2': (1000, 20000),
            'occupancy_hours': (24, 24)
        }
    }
    
    # Classes d'efficacité énergétique
    ENERGY_EFFICIENCY_CLASSES = {
        'A': {'factor': 0.7, 'description': 'Très efficace'},
        'B': {'factor': 0.85, 'description': 'Efficace'},
        'C': {'factor': 1.0, 'description': 'Standard'},
        'D': {'factor': 1.15, 'description': 'Peu efficace'},
        'E': {'factor': 1.3, 'description': 'Inefficace'}
    }
    
    # Paramètres climatiques (centralisés)
    CLIMATE = {
        'average_temperature': 27.0,  # °C
        'temperature_range': (24, 34),
        'average_humidity': 0.8,  # 80%
        'humidity_range': (0.6, 0.95),
        'base_pressure': 1013.25,  # hPa
        'precipitation_prob_afternoon': 0.3,
        'precipitation_prob_night': 0.1,
        'dry_season_months': [6, 7, 8],
        'wet_season_months': [11, 12, 1, 2]
    }
    
    @classmethod
    def get_all_zones_list(cls):
        """Retourne la liste formatée des zones"""
        return [
            {'id': zone_id, 'name': zone_config['name'], 'bbox': zone_config['bbox']}
            for zone_id, zone_config in cls.ZONES.items()
        ]
    
    @classmethod
    def get_zone_config(cls, zone_name):
        """Retourne la configuration d'une zone"""
        return cls.ZONES.get(zone_name)
    
    @classmethod
    def get_building_type_config(cls, building_type):
        """Retourne la configuration d'un type de bâtiment"""
        return cls.BUILDING_TYPES.get(building_type, cls.BUILDING_TYPES['residential'])


# ==============================================================================
# CONFIGURATION TEMPORELLE ET FRÉQUENCES
# ==============================================================================

class TimeConfig:
    """Configuration temporelle centralisée"""
    
    # Fuseaux horaires
    MALAYSIA_TIMEZONE = 'Asia/Kuala_Lumpur'
    MALAYSIA_UTC_OFFSET = '+08:00'
    
    # Fréquences supportées (une seule définition)
    SUPPORTED_FREQUENCIES = {
        '15T': {'description': '15 minutes', 'points_per_day': 96, 'recommended_max_days': 7},
        '30T': {'description': '30 minutes', 'points_per_day': 48, 'recommended_max_days': 14},
        '1H': {'description': '1 heure', 'points_per_day': 24, 'recommended_max_days': 30},
        '3H': {'description': '3 heures', 'points_per_day': 8, 'recommended_max_days': 90},
        '6H': {'description': '6 heures', 'points_per_day': 4, 'recommended_max_days': 180},
        'D': {'description': '1 jour', 'points_per_day': 1, 'recommended_max_days': 365}
    }
    
    DEFAULT_FREQUENCY = '1H'


# ==============================================================================
# CONFIGURATION MÉTÉO
# ==============================================================================

class WeatherConfig:
    """Configuration météorologique optimisée"""
    
    # Colonnes météo (33 colonnes définitives)
    COLUMNS = [
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
    
    # Paramètres climatiques Malaysia - AJOUT DE L'ATTRIBUT MANQUANT
    CLIMATE_PARAMS = {
        'base_temperature': 27.0,  # °C
        'base_humidity': 0.8,      # 80%
        'base_pressure': 1013.25,  # hPa
        'temperature_variation': 5.0,  # Variation diurne
        'seasonal_variation': 2.0,     # Variation saisonnière
        'precipitation_prob_afternoon': 0.3,
        'precipitation_prob_night': 0.1
    }
    
    @classmethod
    def get_climate_params(cls):
        """Retourne les paramètres climatiques depuis MalaysiaConfig"""
        return cls.CLIMATE_PARAMS


# ==============================================================================
# CONFIGURATION EXPORT
# ==============================================================================

class ExportConfig:
    """Configuration export centralisée et optimisée"""
    
    # Formats supportés (unique)
    SUPPORTED_FORMATS = ['csv', 'parquet', 'xlsx']
    
    # Noms de fichiers standardisés
    DEFAULT_FILENAMES = {
        'buildings': 'buildings_metadata',
        'consumption': 'electricity_consumption', 
        'water': 'water_consumption',
        'weather': 'weather_simulation'
    }
    
    # Configuration par format (centralisée)
    FORMAT_CONFIG = {
        'csv': {
            'separator': ',',
            'encoding': 'utf-8',
            'extension': '.csv',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'mime_type': 'text/csv'
        },
        'parquet': {
            'compression': 'snappy',
            'extension': '.parquet',
            'engine': 'pyarrow',
            'mime_type': 'application/octet-stream'
        },
        'xlsx': {
            'sheet_name': 'Data',
            'extension': '.xlsx',
            'engine': 'openpyxl',
            'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
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
    """Configuration OpenStreetMap centralisée"""
    
    # Configuration Overpass API
    OVERPASS_CONFIG = {
        'timeout': 60,
        'user_agent': f'{AppConfig.NAME}/{AppConfig.VERSION}'
    }
    
    # Endpoints API (centralisés)
    API_ENDPOINTS = {
        'overpass_primary': 'https://overpass-api.de/api/interpreter',
        'overpass_backup': 'https://overpass.kumi.systems/api/interpreter',
        'nominatim': 'https://nominatim.openstreetmap.org/'
    }
    
    # Headers HTTP standardisés
    HTTP_HEADERS = {
        'User-Agent': f'{AppConfig.NAME}/{AppConfig.VERSION} (Research Project)',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate'
    }
    
    @classmethod
    def build_overpass_query(cls, bbox):
        """Construit une requête Overpass optimisée - VERSION CORRIGÉE"""
        west, south, east, north = bbox
        
        # Requête Overpass QL corrigée avec syntaxe valide
        query = f"""[out:json][timeout:{cls.OVERPASS_CONFIG['timeout']}];
    (
    way["building"](bbox:{south},{west},{north},{east});
    relation["building"](bbox:{south},{west},{north},{east});
    );
    out geom;"""
        
        return query



# ==============================================================================
# CONFIGURATION LOGGING
# ==============================================================================

class LogConfig:
    """Configuration logging centralisée"""
    
    # Format et niveaux
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Tailles limites
    LOG_MAX_SIZE_MB = 10
    LOG_BACKUP_COUNT = 5
    
    # Niveaux disponibles
    LEVELS = {
        'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50
    }


# ==============================================================================
# CONSTANTES MATHÉMATIQUES
# ==============================================================================

class MathConstants:
    """Constantes mathématiques et scientifiques centralisées"""
    
    # Constantes physiques
    EARTH_RADIUS_KM = 6371.0
    DEGREES_TO_RADIANS = 0.017453292519943295
    METERS_PER_DEGREE_LAT = 111000
    
    # Facteurs de conversion
    CONVERSION = {
        'kwh_to_wh': 1000,
        'celsius_to_kelvin': 273.15,
        'bytes_to_mb': 1024 * 1024,
        'mm_to_m': 0.001
    }
    
    # Préfixes de taille
    SIZE_PREFIXES = ['B', 'KB', 'MB', 'GB', 'TB']


# Initialisation automatique des dossiers
AppConfig.init_directories()