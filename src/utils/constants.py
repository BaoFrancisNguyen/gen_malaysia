#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONSTANTES DU PROJET - UTILS MODULE
===================================

Constantes centralisées pour éviter la duplication et faciliter la maintenance.
"""

# ==============================================================================
# CONSTANTES GÉOGRAPHIQUES MALAYSIA
# ==============================================================================

# Limites géographiques de la Malaysia
MALAYSIA_BOUNDS = {
    'north': 7.5,
    'south': 0.5,
    'east': 119.5,
    'west': 99.5
}

# Coordonnées des principales villes Malaysia
MAJOR_CITIES_COORDINATES = {
    'kuala_lumpur': {'lat': 3.1390, 'lon': 101.6869},
    'george_town': {'lat': 5.4164, 'lon': 100.3327},
    'johor_bahru': {'lat': 1.4927, 'lon': 103.7414},
    'shah_alam': {'lat': 3.0733, 'lon': 101.5185},
    'kota_kinabalu': {'lat': 5.9804, 'lon': 116.0735},
    'kuching': {'lat': 1.5533, 'lon': 110.3592},
    'malacca': {'lat': 2.1896, 'lon': 102.2501},
    'ipoh': {'lat': 4.5975, 'lon': 101.0901}
}

# Fuseaux horaires Malaysia
MALAYSIA_TIMEZONE = 'Asia/Kuala_Lumpur'
MALAYSIA_UTC_OFFSET = '+08:00'


# ==============================================================================
# TYPES DE BÂTIMENTS ET CONSOMMATION
# ==============================================================================

# Types de bâtiments supportés avec consommations de base
BUILDING_TYPES = {
    'residential': {
        'base_consumption_kwh_m2_day': 0.8,
        'description': 'Bâtiments résidentiels',
        'typical_size_m2': (50, 300),
        'occupancy_hours': (16, 24)  # Heures d'occupation par jour
    },
    'commercial': {
        'base_consumption_kwh_m2_day': 1.5,
        'description': 'Bâtiments commerciaux',
        'typical_size_m2': (100, 2000),
        'occupancy_hours': (10, 14)
    },
    'office': {
        'base_consumption_kwh_m2_day': 2.0,
        'description': 'Bureaux et administrations',
        'typical_size_m2': (200, 5000),
        'occupancy_hours': (8, 10)
    },
    'industrial': {
        'base_consumption_kwh_m2_day': 3.5,
        'description': 'Bâtiments industriels',
        'typical_size_m2': (500, 10000),
        'occupancy_hours': (16, 24)
    },
    'school': {
        'base_consumption_kwh_m2_day': 1.2,
        'description': 'Établissements scolaires',
        'typical_size_m2': (300, 3000),
        'occupancy_hours': (8, 12)
    },
    'hospital': {
        'base_consumption_kwh_m2_day': 4.0,
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


# ==============================================================================
# FRÉQUENCES D'ÉCHANTILLONNAGE
# ==============================================================================

# Fréquences supportées pour les séries temporelles
SUPPORTED_FREQUENCIES = {
    '15T': {
        'description': '15 minutes',
        'points_per_day': 96,
        'recommended_max_days': 7
    },
    '30T': {
        'description': '30 minutes',
        'points_per_day': 48,
        'recommended_max_days': 14
    },
    '1H': {
        'description': '1 heure',
        'points_per_day': 24,
        'recommended_max_days': 30
    },
    '3H': {
        'description': '3 heures',
        'points_per_day': 8,
        'recommended_max_days': 90
    },
    '6H': {
        'description': '6 heures',
        'points_per_day': 4,
        'recommended_max_days': 180
    },
    'D': {
        'description': '1 jour',
        'points_per_day': 1,
        'recommended_max_days': 365
    }
}

# Fréquence par défaut
DEFAULT_FREQUENCY = '1H'


# ==============================================================================
# CONFIGURATION MÉTÉOROLOGIQUE
# ==============================================================================

# Paramètres climatiques Malaysia (climat tropical)
MALAYSIA_CLIMATE = {
    'average_temperature': 27.0,  # °C
    'temperature_range': (24, 34),
    'average_humidity': 0.8,  # 80%
    'humidity_range': (0.6, 0.95),
    'average_precipitation_mm_month': 200,
    'dry_season_months': [6, 7, 8],  # Juin-Août
    'wet_season_months': [11, 12, 1, 2],  # Nov-Fév
    'monsoon_periods': {
        'southwest': [5, 6, 7, 8, 9],
        'northeast': [11, 12, 1, 2, 3]
    }
}

# Codes météorologiques WMO
WEATHER_CODES = {
    0: 'Ciel clair',
    1: 'Principalement clair',
    2: 'Partiellement nuageux',
    3: 'Couvert',
    45: 'Brouillard',
    48: 'Brouillard givrant',
    51: 'Bruine légère',
    53: 'Bruine modérée',
    55: 'Bruine dense',
    61: 'Pluie légère',
    63: 'Pluie modérée',
    65: 'Pluie forte',
    80: 'Averses légères',
    81: 'Averses modérées',
    82: 'Averses violentes',
    95: 'Orage',
    96: 'Orage avec grêle légère',
    99: 'Orage avec grêle forte'
}


# ==============================================================================
# FORMATS D'EXPORT
# ==============================================================================

# Formats de fichiers supportés
SUPPORTED_EXPORT_FORMATS = {
    'csv': {
        'extension': '.csv',
        'mime_type': 'text/csv',
        'description': 'Comma Separated Values',
        'compression': False,
        'max_size_mb': 500
    },
    'parquet': {
        'extension': '.parquet',
        'mime_type': 'application/octet-stream',
        'description': 'Apache Parquet',
        'compression': True,
        'max_size_mb': 2000
    },
    'xlsx': {
        'extension': '.xlsx',
        'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'description': 'Microsoft Excel',
        'compression': True,
        'max_size_mb': 100
    }
}

# Configuration par format
CSV_CONFIG = {
    'separator': ',',
    'encoding': 'utf-8',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'float_format': '%.4f',
    'decimal': '.',
    'thousands': None
}

PARQUET_CONFIG = {
    'engine': 'pyarrow',
    'compression': 'snappy',
    'row_group_size': 50000,
    'use_dictionary': True
}

EXCEL_CONFIG = {
    'engine': 'openpyxl',
    'sheet_name': 'Data',
    'index': False
}


# ==============================================================================
# VALEURS PAR DÉFAUT
# ==============================================================================

# Valeurs par défaut pour la génération
DEFAULT_VALUES = {
    'building_surface_m2': 100.0,
    'building_type': 'residential',
    'energy_efficiency_class': 'C',
    'generation_frequency': '1H',
    'weather_stations_count': 5,
    'export_format': 'csv'
}

# Limites système
SYSTEM_LIMITS = {
    'max_buildings_per_zone': 50000,
    'max_timeseries_points': 1000000,
    'max_weather_stations': 50,
    'max_generation_days': 365,
    'max_export_file_size_mb': 2000,
    'max_memory_usage_mb': 4000
}


# ==============================================================================
# MESSAGES ET TEXTES
# ==============================================================================

# Messages d'erreur standardisés
ERROR_MESSAGES = {
    'invalid_coordinates': "Coordonnées invalides pour Malaysia",
    'invalid_building_type': "Type de bâtiment non reconnu",
    'invalid_date_range': "Plage de dates invalide",
    'invalid_frequency': "Fréquence non supportée",
    'file_too_large': "Fichier trop volumineux",
    'missing_required_field': "Champ requis manquant",
    'data_inconsistent': "Données incohérentes détectées",
    'generation_failed': "Échec de la génération",
    'export_failed': "Échec de l'export",
    'osm_connection_failed': "Connexion OSM échouée",
    'validation_failed': "Validation des données échouée",
    'insufficient_memory': "Mémoire insuffisante",
    'timeout_exceeded': "Délai d'attente dépassé"
}

# Messages de succès
SUCCESS_MESSAGES = {
    'data_generated': "Données générées avec succès",
    'data_exported': "Données exportées avec succès",
    'buildings_loaded': "Bâtiments chargés avec succès",
    'validation_passed': "Validation réussie",
    'configuration_saved': "Configuration sauvegardée",
    'cache_cleared': "Cache vidé avec succès",
    'session_completed': "Session terminée avec succès"
}

# Messages d'information
INFO_MESSAGES = {
    'processing': "Traitement en cours...",
    'loading_osm': "Chargement des données OSM...",
    'generating_data': "Génération des données électriques...",
    'generating_weather': "Génération des données météorologiques...",
    'exporting_data': "Export des données...",
    'validating_data': "Validation des données...",
    'optimizing_performance': "Optimisation des performances...",
    'preparing_export': "Préparation des fichiers d'export..."
}

# Messages d'avertissement
WARNING_MESSAGES = {
    'large_dataset': "Volume de données important détecté",
    'performance_impact': "Impact sur les performances possible",
    'memory_usage_high': "Utilisation mémoire élevée",
    'slow_generation': "Génération plus lente que prévu",
    'data_quality_issues': "Problèmes de qualité des données détectés",
    'partial_results': "Résultats partiels seulement"
}


# ==============================================================================
# CONFIGURATION API ET SERVICES
# ==============================================================================

# URLs et endpoints
API_ENDPOINTS = {
    'overpass_primary': 'https://overpass-api.de/api/interpreter',
    'overpass_backup': 'https://overpass.kumi.systems/api/interpreter',
    'nominatim': 'https://nominatim.openstreetmap.org/'
}

# Timeouts et limites
API_TIMEOUTS = {
    'overpass_query': 60,  # secondes
    'nominatim_query': 10,
    'http_request': 30,
    'connection': 10
}

# Headers HTTP
HTTP_HEADERS = {
    'User-Agent': 'Malaysia-Electricity-Generator/3.0 (Research Project)',
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate'
}


# ==============================================================================
# EXPRESSIONS RÉGULIÈRES
# ==============================================================================

# Patterns de validation
VALIDATION_PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    'date_iso': r'^\d{4}-\d{2}-\d{2}$',
    'datetime_iso': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
    'filename_safe': r'^[a-zA-Z0-9._-]+$',
    'building_id': r'^[A-Z][A-Z0-9]{2}[A-Z0-9]{6}$',
    'zone_name': r'^[a-z][a-z0-9_]{1,50}$',
    'frequency': r'^(\d+[TMHD]|D|W|M)$'
}

# Caractères interdits dans les noms de fichiers
FORBIDDEN_FILENAME_CHARS = '<>:"/\\|?*'

# Extensions de fichiers autorisées
ALLOWED_FILE_EXTENSIONS = ['.csv', '.parquet', '.xlsx', '.json', '.txt']


# ==============================================================================
# CONSTANTES MATHÉMATIQUES ET SCIENTIFIQUES
# ==============================================================================

# Constantes physiques
PHYSICAL_CONSTANTS = {
    'earth_radius_km': 6371.0,
    'degrees_to_radians': 0.017453292519943295,
    'radians_to_degrees': 57.29577951308232,
    'meters_per_degree_lat': 111000,
    'seconds_per_day': 86400,
    'minutes_per_hour': 60,
    'hours_per_day': 24,
    'days_per_year': 365.25
}

# Facteurs de conversion
CONVERSION_FACTORS = {
    'kwh_to_wh': 1000,
    'wh_to_kwh': 0.001,
    'celsius_to_kelvin': 273.15,
    'kelvin_to_celsius': -273.15,
    'bytes_to_kb': 1024,
    'kb_to_mb': 1024,
    'mb_to_gb': 1024,
    'mm_to_cm': 0.1,
    'cm_to_m': 0.01,
    'm_to_km': 0.001
}

# Préfixes de taille
SIZE_PREFIXES = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


# ==============================================================================
# CONFIGURATION PERFORMANCE
# ==============================================================================

# Limites de performance
PERFORMANCE_LIMITS = {
    'max_memory_mb': 4096,
    'max_processing_time_minutes': 30,
    'batch_size_buildings': 1000,
    'batch_size_timeseries': 10000,
    'chunk_size_export': 50000,
    'cache_size_items': 1000,
    'cache_ttl_seconds': 3600
}

# Seuils d'alerte performance
PERFORMANCE_ALERTS = {
    'slow_query_seconds': 10,
    'large_dataset_mb': 100,
    'high_memory_usage_percent': 80,
    'many_buildings_count': 10000,
    'long_timeseries_days': 90
}


# ==============================================================================
# MÉTADONNÉES APPLICATION
# ==============================================================================

# Informations sur l'application
APPLICATION_INFO = {
    'name': 'Malaysia Electricity Data Generator',
    'version': '3.0.0',
    'description': 'Générateur de données électriques pour Malaysia avec architecture factorisée',
    'author': 'AI Assistant',
    'license': 'MIT',
    'python_min_version': '3.8',
    'supported_os': ['Windows', 'Linux', 'macOS']
}

# Métadonnées de version
VERSION_INFO = {
    'major': 3,
    'minor': 0,
    'patch': 0,
    'release_type': 'stable',
    'build_date': '2025-01-XX',
    'architecture': 'factorisee'
}


# ==============================================================================
# CONFIGURATION LOGGING
# ==============================================================================

# Niveaux de log
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Format des logs
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Taille maximale des fichiers de log
LOG_MAX_SIZE_MB = 10
LOG_BACKUP_COUNT = 5