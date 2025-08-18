#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MALAYSIA ELECTRICITY GENERATOR - APPLICATION FLASK AMÉLIORÉE
============================================================

Application Flask principale utilisant l'architecture modulaire améliorée avec 
géométrie précise des polygones OSM et données d'étages.

Version: 3.1.0 - Améliorée avec géométrie précise
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file

# Configuration du projet
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Imports des modules améliorés
from src.core.osm_handler import EnhancedOSMHandler  # Version améliorée
from src.services.osm_service import OSMService
from src.services.generation_service import EnhancedGenerationService  # Version améliorée
from src.services.export_service import EnhancedExportService  # Version améliorée
from src.utils.validators import validate_date_range, validate_zone_name
from src.utils.helpers import setup_logging
from config import MalaysiaConfig, AppConfig

# Configuration du logging
logger = setup_logging()

# Création de l'application Flask
app = Flask(__name__)
app.config.from_object(AppConfig)

# Initialisation des services améliorés
osm_service = OSMService()
generation_service = EnhancedGenerationService()  # Version améliorée
export_service = EnhancedExportService()  # Version améliorée

# Cache global amélioré avec support géométrie
app_cache = {
    'buildings': [],
    'consumption_data': None,
    'weather_data': None,
    'water_data': None,
    'geometry_statistics': {},
    'enhanced_features_active': True
}


# ==============================================================================
# ROUTES PRINCIPALES AMÉLIORÉES
# ==============================================================================

@app.route('/')
def index():
    """Page d'accueil améliorée"""
    return render_template('index.html')


@app.route('/api/zones', methods=['GET'])
def api_get_zones():
    """API: Liste des zones Malaysia avec relations OSM"""
    try:
        zones = MalaysiaConfig.get_all_zones_list()
        return jsonify({
            'success': True,
            'zones': zones,
            'total_zones': len(zones),
            'enhanced_features': True,
            'administrative_relations': True
        })
    except Exception as e:
        logger.error(f"Erreur API zones: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/buildings/<zone_name>', methods=['POST'])
def api_load_buildings(zone_name):
    """API: Charge les bâtiments OSM avec géométrie précise et métadonnées d'étages"""
    try:
        # Validation
        if not validate_zone_name(zone_name):
            return jsonify({
                'success': False, 
                'error': f'Zone invalide: {zone_name}'
            }), 400
        
        # Chargement via le service avec extraction améliorée
        result = osm_service.load_buildings_for_zone(zone_name)
        
        if result['success']:
            app_cache['buildings'] = result['buildings']
            
            # Extraction des statistiques géométriques
            geometry_stats = _analyze_cache_geometry_statistics(result['buildings'])
            app_cache['geometry_statistics'] = geometry_stats
            
            logger.info(f"Cache amélioré: {len(result['buildings'])} bâtiments stockés")
            logger.info(f"Géométrie: {geometry_stats.get('with_precise_geometry', 0)} précis, "
                       f"{geometry_stats.get('with_floors_data', 0)} avec étages")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur chargement bâtiments amélioré: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def api_generate_data():
    """API: Génère les données avec géométrie précise - VERSION AMÉLIORÉE"""
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
        
        # Récupération des choix utilisateur
        generate_electricity = data.get('generate_electricity', True)
        generate_water = data.get('generate_water', True)
        generate_weather = data.get('generate_weather', True)
        
        # Validation qu'au moins un type est sélectionné
        if not any([generate_electricity, generate_water, generate_weather]):
            return jsonify({
                'success': False,
                'error': 'Aucun type de données sélectionné'
            }), 400
        
        # Génération via le service amélioré
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
            
            logger.info(f"Cache amélioré mis à jour: "
                       f"{result['summary']['consumption_points']} points électricité, "
                       f"{result['summary']['water_points']} points eau, "
                       f"{result['summary']['weather_points']} points météo")
            
            # Préparation de la réponse JSON sans les DataFrames
            response_data = {
                'success': True,
                'session_id': result['session_id'],
                'summary': result['summary'],
                'generated_types': result['generated_types'],
                'enhanced_features_used': result.get('enhanced_features_used', True),
                'session_info': {
                    'session_id': result['session_info']['session_id'],
                    'generation_time': result['session_info']['generation_time'],
                    'generation_duration_seconds': result['session_info']['generation_duration_seconds'],
                    'enhanced_features': result['session_info'].get('enhanced_features', True),
                    'geometry_processing': result['session_info'].get('geometry_processing', True),
                    'parameters': result['session_info']['parameters'],
                    'summary': result['session_info']['summary']
                }
            }
            
            return jsonify(response_data)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Erreur génération améliorée: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def api_export_data():
    """API: Exporte les données avec métadonnées géométriques"""
    try:
        data = request.get_json()
        export_format = data.get('format', 'csv')
        base_filename = data.get('filename')
        
        # Vérifier qu'il y a des données à exporter
        has_buildings = len(app_cache['buildings']) > 0
        has_consumption = app_cache['consumption_data'] is not None
        has_weather = app_cache['weather_data'] is not None
        has_water = app_cache['water_data'] is not None
        
        if not has_buildings:
            return jsonify({
                'success': False,
                'error': 'Aucun bâtiment à exporter'
            }), 400
        
        # Export via le service amélioré
        result = export_service.export_all_datasets(
            buildings=app_cache['buildings'],
            consumption_data=app_cache['consumption_data'] if has_consumption else None,
            weather_data=app_cache['weather_data'] if has_weather else None,
            water_data=app_cache['water_data'] if has_water else None,
            export_format=export_format,
            base_filename=base_filename
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Erreur export amélioré: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/<filename>')
def api_download_file(filename):
    """API: Télécharge un fichier exporté"""
    try:
        file_path = AppConfig.EXPORTS_DIR / filename
        
        if not file_path.exists():
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def api_get_status():
    """API: Statut de l'application améliorée"""
    try:
        status = {
            'success': True,
            'version': '3.1.0-enhanced',
            'enhanced_features': True,
            'geometry_processing': True,
            'cache': {
                'buildings_loaded': len(app_cache['buildings']),
                'consumption_points': len(app_cache['consumption_data']) if app_cache['consumption_data'] is not None else 0,
                'weather_points': len(app_cache['weather_data']) if app_cache['weather_data'] is not None else 0,
                'water_points': len(app_cache['water_data']) if app_cache['water_data'] is not None else 0
            },
            'geometry_statistics': app_cache.get('geometry_statistics', {}),
            'services': {
                'osm_service': 'active',
                'generation_service': 'active', 
                'export_service': 'active'
            },
            'capabilities': {
                'administrative_relations': True,
                'precise_geometry_extraction': True,
                'floors_metadata': True,
                'enhanced_validation': True
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Erreur statut: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def _analyze_cache_geometry_statistics(buildings):
    """Analyse les statistiques géométriques du cache"""
    if not buildings:
        return {
            'with_precise_geometry': 0,
            'with_floors_data': 0,
            'total_buildings': 0
        }
    
    with_geometry = sum(1 for b in buildings if b.get('has_precise_geometry', False))
    with_floors = sum(1 for b in buildings if b.get('floors_count', 1) > 1)
    
    return {
        'total_buildings': len(buildings),
        'with_precise_geometry': with_geometry,
        'with_floors_data': with_floors,
        'geometry_rate': round(with_geometry / len(buildings), 3),
        'floors_rate': round(with_floors / len(buildings), 3)
    }


def _cache_health_check():
    """Vérifie la santé du cache"""
    return {
        'buildings_loaded': len(app_cache['buildings']),
        'consumption_cached': app_cache['consumption_data'] is not None,
        'weather_cached': app_cache['weather_data'] is not None,
        'water_cached': app_cache['water_data'] is not None,
        'enhanced_features_active': app_cache['enhanced_features_active']
    }


# ==============================================================================
# GESTION D'ERREURS
# ==============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint non trouvé'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur interne: {error}")
    return jsonify({'error': 'Erreur interne du serveur'}), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Requête invalide'}), 400


# ==============================================================================
# DÉMARRAGE DE L'APPLICATION
# ==============================================================================

if __name__ == '__main__':
    logger.info("🚀 Démarrage Malaysia Electricity Generator v3.1.0 Enhanced")
    logger.info("🏗️ Architecture: modulaire avec géométrie précise")
    logger.info("📐 Fonctionnalités: extraction polygones OSM + métadonnées étages")
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )