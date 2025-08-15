#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MALAYSIA ELECTRICITY GENERATOR - APPLICATION FLASK PRINCIPALE
==============================================================

Application Flask principale utilisant l'architecture modulaire factorée.

Version: 3.0.0 - Factorisée avec support de 4 types de données
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file

# Configuration du projet
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Imports des modules factorés
from src.core.osm_handler import OSMHandler
from src.core.generator import ElectricityGenerator, WeatherGenerator, WaterGenerator
from src.core.data_exporter import DataExporter
from src.services.osm_service import OSMService
from src.services.generation_service import GenerationService
from src.services.export_service import ExportService
from src.utils.validators import validate_date_range, validate_zone_name
from src.utils.helpers import setup_logging
from config import MalaysiaConfig, AppConfig

# Configuration du logging
logger = setup_logging()

# Création de l'application Flask
app = Flask(__name__)
app.config.from_object(AppConfig)

# Initialisation des services
osm_service = OSMService()
generation_service = GenerationService() 
export_service = ExportService()

# Cache global simple avec support eau
app_cache = {
    'buildings': [],
    'consumption_data': None,
    'weather_data': None,
    'water_data': None
}


# ==============================================================================
# ROUTES PRINCIPALES
# ==============================================================================

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/api/zones', methods=['GET'])
def api_get_zones():
    """API: Liste des zones Malaysia"""
    try:
        zones = MalaysiaConfig.get_all_zones_list()
        return jsonify({
            'success': True,
            'zones': zones,
            'total_zones': len(zones)
        })
    except Exception as e:
        logger.error(f"Erreur API zones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/buildings/<zone_name>', methods=['POST'])
def api_load_buildings(zone_name):
    """API: Charge les bâtiments OSM"""
    try:
        # Validation
        if not validate_zone_name(zone_name):
            return jsonify({
                'success': False, 
                'error': f'Zone invalide: {zone_name}'
            }), 400
        
        # Chargement via le service
        result = osm_service.load_buildings_for_zone(zone_name)
        
        if result['success']:
            app_cache['buildings'] = result['buildings']
            logger.info(f"Cache: {len(result['buildings'])} bâtiments stockés")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur chargement bâtiments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def api_generate_data():
    """API: Génère les données selon la sélection utilisateur - VERSION CORRIGÉE"""
    try:
        data = request.get_json()
        
        # Validation des paramètres
        required = ['start_date', 'end_date']
        for param in required:
            if param not in data:
                return jsonify({
                    'success': False,
                    'error': f'Paramètre manquant: {param}'
                }), 400
        
        # Validation des dates
        if not validate_date_range(data['start_date'], data['end_date']):
            return jsonify({
                'success': False,
                'error': 'Plage de dates invalide'
            }), 400
        
        # Vérifier cache bâtiments
        if not app_cache['buildings']:
            return jsonify({
                'success': False,
                'error': 'Aucun bâtiment chargé'
            }), 400
        
        # Récupération des choix utilisateur (par défaut tous actifs)
        generate_electricity = data.get('generate_electricity', True)
        generate_water = data.get('generate_water', True)
        generate_weather = data.get('generate_weather', True)
        
        # Validation qu'au moins un type est sélectionné
        if not any([generate_electricity, generate_water, generate_weather]):
            return jsonify({
                'success': False,
                'error': 'Aucun type de données sélectionné'
            }), 400
        
        # Génération via le service
        result = generation_service.generate_all_data(
            buildings=app_cache['buildings'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            frequency=data.get('frequency', '1H'),
            weather_stations=data.get('weather_stations', 5),
            generate_electricity=generate_electricity,
            generate_water=generate_water,
            generate_weather=generate_weather
        )
        
        if result['success']:
            # Mise à jour du cache avec les nouveaux types de données
            app_cache['consumption_data'] = result['consumption_data']
            app_cache['water_data'] = result['water_data']
            app_cache['weather_data'] = result['weather_data']
            
            logger.info(f"Cache mis à jour: "
                       f"{result['summary']['consumption_points']} points électricité, "
                       f"{result['summary']['water_points']} points eau, "
                       f"{result['summary']['weather_points']} points météo")
            
            # CORRECTION: Préparation de la réponse JSON sans les DataFrames
            response_data = {
                'success': True,
                'session_id': result['session_id'],
                'summary': result['summary'],
                'generated_types': result['generated_types'],
                'session_info': {
                    'session_id': result['session_info']['session_id'],
                    'generation_time': result['session_info']['generation_time'],
                    'generation_duration_seconds': result['session_info']['generation_duration_seconds'],
                    'parameters': result['session_info']['parameters'],
                    'summary': result['session_info']['summary']
                }
            }
            
            return jsonify(response_data)
        else:
            return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur génération: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def api_export_data():
    """API: Exporte les 4 datasets possibles"""
    try:
        data = request.get_json() or {}
        
        # Validation format
        export_format = data.get('format', 'csv')
        if export_format not in ['csv', 'parquet', 'xlsx']:
            return jsonify({
                'success': False,
                'error': f'Format non supporté: {export_format}'
            }), 400
        
        # Vérifier données
        if not app_cache['buildings']:
            return jsonify({
                'success': False,
                'error': 'Aucune donnée à exporter'
            }), 400
        
        # Export via le service avec support des 4 types
        result = export_service.export_all_datasets(
            buildings=app_cache['buildings'],
            consumption_data=app_cache['consumption_data'],
            weather_data=app_cache['weather_data'],
            water_data=app_cache['water_data'],  # Nouveau paramètre
            export_format=export_format,
            base_filename=data.get('filename')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur export: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/<filename>')
def api_download_file(filename):
    """API: Télécharge un fichier"""
    try:
        file_path = AppConfig.EXPORTS_DIR / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'Fichier non trouvé'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Erreur téléchargement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status')
def api_status():
    """API: Statut de l'application avec support des 4 types"""
    try:
        # Calcul des points pour chaque type
        consumption_points = len(app_cache['consumption_data']) if app_cache['consumption_data'] is not None else 0
        weather_points = len(app_cache['weather_data']) if app_cache['weather_data'] is not None else 0
        water_points = len(app_cache['water_data']) if app_cache['water_data'] is not None else 0
        
        return jsonify({
            'success': True,
            'status': 'active',
            'version': '3.0.0',
            'cache': {
                'buildings_loaded': len(app_cache['buildings']),
                'consumption_points': consumption_points,
                'weather_points': weather_points,
                'water_points': water_points,
                'total_points': consumption_points + weather_points + water_points
            },
            'config': {
                'available_zones': list(MalaysiaConfig.ZONES.keys()),
                'supported_formats': ['csv', 'parquet', 'xlsx'],
                'export_directory': str(AppConfig.EXPORTS_DIR),
                'data_types_supported': ['electricity', 'water', 'weather', 'buildings_metadata']
            },
            'features': {
                'four_datasets_export': True,
                'selective_generation': True,
                'interactive_mapping': True
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur statut: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clear-cache', methods=['POST'])
def api_clear_cache():
    """API: Vide le cache de l'application"""
    try:
        # Réinitialisation complète du cache
        app_cache['buildings'] = []
        app_cache['consumption_data'] = None
        app_cache['weather_data'] = None
        app_cache['water_data'] = None
        
        logger.info("🗑️ Cache application vidé")
        
        return jsonify({
            'success': True,
            'message': 'Cache vidé avec succès',
            'cache_status': {
                'buildings': 0,
                'consumption_points': 0,
                'weather_points': 0,
                'water_points': 0
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur vidage cache: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/statistics')
def api_statistics():
    """API: Statistiques détaillées de l'application"""
    try:
        # Statistiques des services
        osm_stats = osm_service.get_service_statistics()
        generation_stats = generation_service.get_service_statistics()
        export_stats = export_service.get_export_summary()
        
        return jsonify({
            'success': True,
            'application_stats': {
                'version': '3.0.0',
                'cache_status': {
                    'buildings_loaded': len(app_cache['buildings']),
                    'consumption_points': len(app_cache['consumption_data']) if app_cache['consumption_data'] is not None else 0,
                    'weather_points': len(app_cache['weather_data']) if app_cache['weather_data'] is not None else 0,
                    'water_points': len(app_cache['water_data']) if app_cache['water_data'] is not None else 0
                }
            },
            'osm_service_stats': osm_stats,
            'generation_service_stats': generation_stats,
            'export_service_stats': export_stats
        })
        
    except Exception as e:
        logger.error(f"Erreur statistiques: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# ROUTES UTILITAIRES
# ==============================================================================

@app.route('/api/validate-dates', methods=['POST'])
def api_validate_dates():
    """API: Valide une plage de dates"""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({
                'valid': False,
                'error': 'Dates manquantes'
            }), 400
        
        is_valid = validate_date_range(start_date, end_date)
        
        if is_valid:
            # Calcul statistiques
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end - start).days
            
            return jsonify({
                'valid': True,
                'duration_days': duration_days,
                'recommended_frequency': '1H' if duration_days <= 7 else '3H' if duration_days <= 30 else 'D'
            })
        else:
            return jsonify({
                'valid': False,
                'error': 'Plage de dates invalide'
            })
            
    except Exception as e:
        logger.error(f"Erreur validation dates: {e}")
        return jsonify({'valid': False, 'error': str(e)}), 500


@app.route('/api/estimate-size', methods=['POST'])
def api_estimate_size():
    """API: Estime la taille de génération/export"""
    try:
        data = request.get_json()
        
        buildings_count = len(app_cache['buildings'])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        frequency = data.get('frequency', '1H')
        weather_stations = data.get('weather_stations', 5)
        
        if not start_date or not end_date:
            return jsonify({'error': 'Dates manquantes'}), 400
        
        # Calcul estimation
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        duration_days = (end - start).days
        
        # Points par jour selon fréquence
        points_per_day = {
            '15T': 96, '30T': 48, '1H': 24, '2H': 12,
            '3H': 8, '6H': 4, '12H': 2, 'D': 1
        }.get(frequency, 24)
        
        estimated_consumption_points = buildings_count * duration_days * points_per_day
        estimated_water_points = buildings_count * duration_days * points_per_day
        estimated_weather_points = weather_stations * duration_days * points_per_day
        
        # Estimation taille (approximative)
        estimated_size_mb = (
            estimated_consumption_points * 0.2 +  # 200 bytes par point électricité
            estimated_water_points * 0.18 +       # 180 bytes par point eau
            estimated_weather_points * 0.5        # 500 bytes par point météo
        ) / 1024 / 1024
        
        return jsonify({
            'success': True,
            'estimates': {
                'duration_days': duration_days,
                'consumption_points': estimated_consumption_points,
                'water_points': estimated_water_points,
                'weather_points': estimated_weather_points,
                'total_points': estimated_consumption_points + estimated_water_points + estimated_weather_points,
                'estimated_size_mb': round(estimated_size_mb, 1),
                'estimated_generation_time_minutes': round((estimated_consumption_points + estimated_water_points + estimated_weather_points) / 50000, 1)
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur estimation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# GESTIONNAIRES D'ERREURS
# ==============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint non trouvé'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur interne: {error}")
    return jsonify({'success': False, 'error': 'Erreur interne du serveur'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': 'Requête trop volumineuse'}), 413


# ==============================================================================
# POINT D'ENTRÉE
# ==============================================================================

if __name__ == '__main__':
    logger.info("="*70)
    logger.info("🇲🇾 MALAYSIA ELECTRICITY GENERATOR v3.0 - ARCHITECTURE FACTORISÉE")
    logger.info("="*70)
    logger.info("✨ Architecture modulaire avec séparation des responsabilités")
    logger.info("📁 4 fichiers d'export distincts : bâtiments, électricité, eau, météo")
    logger.info("🎛️ Génération sélective par type de données")
    logger.info("🗺️ Cartographie interactive intégrée")
    logger.info(f"🌐 URL: http://127.0.0.1:5000")
    logger.info("="*70)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )