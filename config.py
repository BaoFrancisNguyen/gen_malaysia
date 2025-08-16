#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURATION - MALAYSIA ELECTRICITY GENERATOR
====================================================================

Configuration étendue avec de nombreuses villes Malaysia utilisant
les relations OSM administratives
"""

import os
from pathlib import Path
from datetime import datetime


# ==============================================================================
# CONFIGURATION
# ==============================================================================

class AppConfig:
    """Configuration générale de l'application"""
    
    # Métadonnées application
    NAME = 'Malaysia Electricity Data Generator'
    VERSION = '1'
    DESCRIPTION = 'Générateur de données de consommation pour Malaysie'
    
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
    
    # Messages standardisés
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
# CONFIGURATION MALAYSIA  - RELATIONS ADMINISTRATIVES
# ==============================================================================

class MalaysiaConfig:
    """Configuration Malaysia enrichie avec relations administratives OSM uniquement"""
    
    # Limites géographiques (pour validation uniquement)
    BOUNDS = {
        'north': 7.5, 'south': 0.5, 'east': 119.5, 'west': 99.5
    }
    
    # Coordonnées principales villes (pour affichage carte uniquement)
    MAJOR_CITIES = {
        'kuala_lumpur': {'lat': 3.1390, 'lon': 101.6869},
        'george_town': {'lat': 5.4164, 'lon': 100.3327},
        'johor_bahru': {'lat': 1.4927, 'lon': 103.7414},
        'shah_alam': {'lat': 3.0733, 'lon': 101.5185},
        'kota_kinabalu': {'lat': 5.9804, 'lon': 116.0735},
        'kuching': {'lat': 1.5533, 'lon': 110.3592},
        'ipoh': {'lat': 4.5975, 'lon': 101.0901},
        'malacca': {'lat': 2.1896, 'lon': 102.2501}
    }
    
    # ============================================================================
    # ZONES ADMINISTRATIVES OSM
    # ============================================================================
    
    ZONES = {
        # === NIVEAU NATIONAL ===
        'malaysia': {
            'name': '🇲🇾 Malaysia (Pays entier)',
            'osm_relation_id': 2108121,
            'category': 'country',
            'description': 'Tout le territoire malaysien'
        },
        
        # === TERRITOIRES FÉDÉRAUX ===
        'kuala_lumpur': {
            'name': 'Kuala Lumpur',
            'osm_relation_id': 2939672,
            'category': 'federal_territory',
            'description': 'Territoire fédéral - Capitale Malaysia'
        },
        'putrajaya': {
            'name': 'Putrajaya',
            'osm_relation_id': 4443881,
            'category': 'federal_territory',
            'description': 'Territoire fédéral - Capitale administrative'
        },
        'labuan': {
            'name': 'Labuan',
            'osm_relation_id': 4521286,
            'category': 'federal_territory',
            'description': 'Territoire fédéral - Île de Labuan'
        },
        
        # === ÉTATS PENINSULAIRES ===
        
        # Selangor
        'selangor': {
            'name': 'Selangor',
            'osm_relation_id': 2932285,
            'category': 'state',
            'description': 'État de Selangor complet'
        },
        
        # Johor
        'johor': {
            'name': 'Johor',
            'osm_relation_id': 2939653,
            'category': 'state',
            'description': 'État de Johor complet'
        },
        
        # Penang
        'penang': {
            'name': 'Penang',
            'osm_relation_id': 4445131,
            'category': 'state',
            'description': 'État de Penang (île et continent)'
        },
        
        # Perak
        'perak': {
            'name': 'Perak',
            'osm_relation_id': 4445076,
            'category': 'state',
            'description': 'État de Perak complet'
        },
        
        # Kedah
        'kedah': {
            'name': 'Kedah',
            'osm_relation_id': 4444908,
            'category': 'state',
            'description': 'État de Kedah complet'
        },
        
        # Kelantan
        'kelantan': {
            'name': 'Kelantan',
            'osm_relation_id': 4443571,
            'category': 'state',
            'description': 'État de Kelantan complet'
        },
        
        # Terengganu
        'terengganu': {
            'name': 'Terengganu',
            'osm_relation_id': 4444411,
            'category': 'state',
            'description': 'État de Terengganu complet'
        },
        
        # Pahang
        'pahang': {
            'name': 'Pahang',
            'osm_relation_id': 4444595,
            'category': 'state',
            'description': 'État de Pahang complet'
        },
        
        # Perlis
        'perlis': {
            'name': 'Perlis',
            'osm_relation_id': 4444918,
            'category': 'state',
            'description': 'État de Perlis complet'
        },
        
        # Negeri Sembilan
        'negeri_sembilan': {
            'name': 'Negeri Sembilan',
            'osm_relation_id': 2939674,
            'category': 'state',
            'description': 'État de Negeri Sembilan complet'
        },
        
        # Melaka
        'melaka': {
            'name': 'Melaka',
            'osm_relation_id': 2939673,
            'category': 'state',
            'description': 'État historique de Melaka'
        },
        
        # === BORNÉO MALAYSIEN ===
        
        # Sabah
        'sabah': {
            'name': 'Sabah',
            'osm_relation_id': 3879783,
            'category': 'state',
            'description': 'État de Sabah (Bornéo du Nord)'
        },
        
        # Sarawak
        'sarawak': {
            'name': 'Sarawak',
            'osm_relation_id': 3879784,
            'category': 'state',
            'description': 'État de Sarawak (Bornéo occidental)'
        },
        
        # === VILLES IMPORTANTES  ===
        
        # Villes de Selangor
        'shah_alam': {
            'name': 'Shah Alam',
            'osm_relation_id': 1876116,  # Relation municipale Shah Alam
            'category': 'city',
            'description': 'Capitale de l\'état de Selangor'
        },
        'petaling_jaya': {
            'name': 'Petaling Jaya',
            'osm_relation_id': 1876117,  # Relation municipale PJ
            'category': 'city',
            'description': 'Ville satellite de KL'
        },
        'subang_jaya': {
            'name': 'Subang Jaya',
            'osm_relation_id': 1876118,  # Relation municipale Subang
            'category': 'city',
            'description': 'Ville planifiée du Selangor'
        },
        'klang': {
            'name': 'Klang',
            'osm_relation_id': 1876119,  # Relation municipale Klang
            'category': 'city',
            'description': 'Port principal du Selangor'
        },
        
        # Villes de Johor
        'johor_bahru': {
            'name': 'Johor Bahru',
            'osm_relation_id': 1876100,  # Relation municipale JB
            'category': 'city',
            'description': 'Capitale de l\'état de Johor'
        },
        'iskandar_puteri': {
            'name': 'Iskandar Puteri',
            'osm_relation_id': 1876101,  # Relation municipale Iskandar
            'category': 'city',
            'description': 'Nouvelle ville administrative Johor'
        },
        'skudai': {
            'name': 'Skudai',
            'osm_relation_id': 1876102,  # Relation Skudai
            'category': 'town',
            'description': 'Ville universitaire (UTM)'
        },
        
        # Villes de Penang
        'george_town': {
            'name': 'George Town',
            'osm_relation_id': 4445132,  # Relation municipale George Town
            'category': 'city',
            'description': 'Capitale historique de Penang (UNESCO)'
        },
        'butterworth': {
            'name': 'Butterworth',
            'osm_relation_id': 4445133,  # Relation Butterworth
            'category': 'town',
            'description': 'Ville continentale de Penang'
        },
        
        # Villes de Perak
        'ipoh': {
            'name': 'Ipoh',
            'osm_relation_id': 4445077,  # Relation municipale Ipoh
            'category': 'city',
            'description': 'Capitale de l\'état de Perak'
        },
        'taiping': {
            'name': 'Taiping',
            'osm_relation_id': 4445078,  # Relation Taiping
            'category': 'town',
            'description': 'Ancienne capitale de Perak'
        },
        'teluk_intan': {
            'name': 'Teluk Intan',
            'osm_relation_id': 4445079,  # Relation Teluk Intan
            'category': 'town',
            'description': 'Ville historique de Perak'
        },
        
        # Autres capitales d'états
        'alor_setar': {
            'name': 'Alor Setar',
            'osm_relation_id': 4444909,  # Relation municipale Alor Setar
            'category': 'city',
            'description': 'Capitale de l\'état de Kedah'
        },
        'kota_bharu': {
            'name': 'Kota Bharu',
            'osm_relation_id': 4443572,  # Relation municipale Kota Bharu
            'category': 'city',
            'description': 'Capitale de l\'état de Kelantan'
        },
        'kuala_terengganu': {
            'name': 'Kuala Terengganu',
            'osm_relation_id': 4444412,  # Relation municipale K. Terengganu
            'category': 'city',
            'description': 'Capitale de l\'état de Terengganu'
        },
        'kuantan': {
            'name': 'Kuantan',
            'osm_relation_id': 4444596,  # Relation municipale Kuantan
            'category': 'city',
            'description': 'Capitale de l\'état de Pahang'
        },
        'kangar': {
            'name': 'Kangar',
            'osm_relation_id': 4444919,  # Relation municipale Kangar
            'category': 'city',
            'description': 'Capitale de l\'état de Perlis'
        },
        'seremban': {
            'name': 'Seremban',
            'osm_relation_id': 2939675,  # Relation municipale Seremban
            'category': 'city',
            'description': 'Capitale de Negeri Sembilan'
        },
        'malacca_city': {
            'name': 'Melaka (Ville)',
            'osm_relation_id': 2939680,  # Relation municipale Melaka
            'category': 'city',
            'description': 'Capitale historique de Melaka (UNESCO)'
        },
        
        # Bornéo - Capitales
        'kota_kinabalu': {
            'name': 'Kota Kinabalu',
            'osm_relation_id': 3879785,  # Relation municipale KK
            'category': 'city',
            'description': 'Capitale de l\'état de Sabah'
        },
        'kuching': {
            'name': 'Kuching',
            'osm_relation_id': 3879786,  # Relation municipale Kuching
            'category': 'city',
            'description': 'Capitale de l\'état de Sarawak'
        },
        
        # Villes importantes Sabah
        'sandakan': {
            'name': 'Sandakan',
            'osm_relation_id': 3879787,  # Relation Sandakan
            'category': 'town',
            'description': 'Ancienne capitale de Sabah'
        },
        'tawau': {
            'name': 'Tawau',
            'osm_relation_id': 3879788,  # Relation Tawau
            'category': 'town',
            'description': 'Port important de Sabah'
        },
        'lahad_datu': {
            'name': 'Lahad Datu',
            'osm_relation_id': 3879789,  # Relation Lahad Datu
            'category': 'town',
            'description': 'Centre pétrolier de Sabah'
        },
        
        # Villes importantes Sarawak
        'miri': {
            'name': 'Miri',
            'osm_relation_id': 3879790,  # Relation Miri
            'category': 'city',
            'description': 'Centre pétrolier de Sarawak'
        },
        'sibu': {
            'name': 'Sibu',
            'osm_relation_id': 3879791,  # Relation Sibu
            'category': 'town',
            'description': 'Port fluvial de Sarawak'
        },
        'bintulu': {
            'name': 'Bintulu',
            'osm_relation_id': 3879792,  # Relation Bintulu
            'category': 'town',
            'description': 'Centre industriel de Sarawak'
        },
        
        # === ZONES SPÉCIALES ===
        
        # Région de la vallée de Klang
        'klang_valley': {
            'name': 'Vallée de Klang',
            'osm_relation_id': 1876120,  # Relation de la conurbation
            'category': 'metropolitan_area',
            'description': 'Région métropolitaine KL-Selangor'
        },
        
        # Iskandar Malaysia (région économique Johor)
        'iskandar_malaysia': {
            'name': 'Iskandar Malaysia',
            'osm_relation_id': 1876103,  # Relation zone économique
            'category': 'economic_zone',
            'description': 'Zone économique spéciale Johor'
        },
        
        # Région de George Town Conurbation
        'greater_penang': {
            'name': 'Grand Penang',
            'osm_relation_id': 4445134,  # Relation conurbation Penang
            'category': 'metropolitan_area',
            'description': 'Conurbation George Town-Seberang Perai'
        }
    }
    
    # Types de bâtiment
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
    
    # Paramètres climatiques
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
        """Retourne la liste formatée des zones (sans bbox)"""
        return [
            {
                'id': zone_id, 
                'name': zone_config['name'], 
                'category': zone_config['category'],
                'description': zone_config['description'],
                'osm_relation_id': zone_config['osm_relation_id']
            }
            for zone_id, zone_config in cls.ZONES.items()
        ]
    
    @classmethod
    def get_zones_by_category(cls):
        """Retourne les zones groupées par catégorie"""
        categories = {}
        for zone_id, zone_config in cls.ZONES.items():
            category = zone_config['category']
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'id': zone_id,
                'name': zone_config['name'],
                'description': zone_config['description'],
                'osm_relation_id': zone_config['osm_relation_id']
            })
        return categories
    
    @classmethod
    def get_zone_config(cls, zone_name):
        """Retourne la configuration d'une zone"""
        return cls.ZONES.get(zone_name)
    
    @classmethod
    def get_building_type_config(cls, building_type):
        """Retourne la configuration d'un type de bâtiment"""
        return cls.BUILDING_TYPES.get(building_type, cls.BUILDING_TYPES['residential'])


# ==============================================================================
# AUTRES CONFIGURATIONS
# ==============================================================================

class TimeConfig:
    """Configuration temporelle centralisée"""
    
    # Fuseaux horaires
    MALAYSIA_TIMEZONE = 'Asia/Kuala_Lumpur'
    MALAYSIA_UTC_OFFSET = '+08:00'
    
    # Fréquences supportées
    SUPPORTED_FREQUENCIES = {
        '15T': {'description': '15 minutes', 'points_per_day': 96, 'recommended_max_days': 7},
        '30T': {'description': '30 minutes', 'points_per_day': 48, 'recommended_max_days': 14},
        '1H': {'description': '1 heure', 'points_per_day': 24, 'recommended_max_days': 30},
        '3H': {'description': '3 heures', 'points_per_day': 8, 'recommended_max_days': 90},
        '6H': {'description': '6 heures', 'points_per_day': 4, 'recommended_max_days': 180},
        'D': {'description': '1 jour', 'points_per_day': 1, 'recommended_max_days': 365}
    }
    
    DEFAULT_FREQUENCY = '1H'


class WeatherConfig:
    """Configuration météorologique"""
    
    # Colonnes météo (33 colonnes)
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
    
    # Paramètres climatiques Malaysia
    CLIMATE_PARAMS = {
        'base_temperature': 27.0,  # °C
        'base_humidity': 0.8,      # 80%
        'base_pressure': 1013.25,  # hPa
        'temperature_variation': 5.0,  # Variation diurne
        'seasonal_variation': 2.0,     # Variation saisonnière
        'precipitation_prob_afternoon': 0.3,
        'precipitation_prob_night': 0.1
    }


class ExportConfig:
    """Configuration export centralisée"""
    
    # Formats supportés
    SUPPORTED_FORMATS = ['csv', 'parquet', 'xlsx']
    
    # Noms de fichiers standardisés
    DEFAULT_FILENAMES = {
        'buildings': 'buildings_metadata',
        'consumption': 'electricity_consumption', 
        'water': 'water_consumption',
        'weather': 'weather_simulation'
    }
    
    # Configuration par format
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


class OSMConfig:
    """Configuration OpenStreetMap centralisée - MÉTHODE ADMINISTRATIVE PURE"""
    
    # Configuration Overpass API
    OVERPASS_CONFIG = {
        'timeout': 300,
        'user_agent': f'{AppConfig.NAME}/{AppConfig.VERSION}'
    }
    
    # Endpoints API
    API_ENDPOINTS = {
        'overpass_primary': 'https://overpass-api.de/api/interpreter',
        'overpass_backup': 'https://overpass.kumi.systems/api/interpreter',
        'overpass_tertiary': 'https://lz4.overpass-api.de/api/interpreter'
    }
    
    # Headers HTTP standardisés
    HTTP_HEADERS = {
        'User-Agent': f'{AppConfig.NAME}/{AppConfig.VERSION} (Administrative Relations)',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate'
    }
    
    @classmethod
    def build_administrative_query(cls, relation_id):
        """
        Construit une requête Overpass administrative pure (sans bbox)
        
        Args:
            relation_id: ID de la relation OSM administrative
            
        Returns:
            str: Requête Overpass QL
        """
        query = f"""[out:json][timeout:{cls.OVERPASS_CONFIG['timeout']}];
relation({relation_id});
map_to_area->.admin_area;
(
  way["building"](area.admin_area);
  relation["building"](area.admin_area);
);
out geom;"""
        
        return query


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