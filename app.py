@app.route('/api/generate', methods=['POST'])
def api_generate_data():
    """API: Génère les données selon la sélection utilisateur"""
    global current_consumption, current_weather, current_water
    
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
        #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MALAYSIA ELECTRICITY GENERATOR - APPLICATION FLASK PRINCIPALE
==============================================================

Application Flask principale utilisant l'architecture modulaire factorée.

Version: 3.0.0 - Factorisée
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
from src.core.generator import ElectricityGenerator, WeatherGenerator  
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

# Cache global simple
app_cache = {
    'buildings': [],
    'consumption_data': None,
    'weather_data': None
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
    """API: Génère les données électriques et météo"""
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
        
        # Génération via le service
        result = generation_service.generate_all_data(
            buildings=app_cache['buildings'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            frequency=data.get('frequency', '1H'),
            weather_stations=data.get('weather_stations', 5)
        )
        
        if result['success']:
            app_cache['consumption_data'] = result['consumption_data']
            app_cache['weather_data'] = result['weather_data']
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erreur génération: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export', methods=['POST'])
def api_export_data():
    """API: Exporte les 3 datasets"""
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
        
        # Export via le service
        result = export_service.export_all_datasets(
            buildings=app_cache['buildings'],
            consumption_data=app_cache['consumption_data'],
            weather_data=app_cache['weather_data'],
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
    """API: Statut de l'application"""
    try:
        consumption_points = len(app_cache['consumption_data']) if app_cache['consumption_data'] is not None else 0
        weather_points = len(app_cache['weather_data']) if app_cache['weather_data'] is not None else 0
        
        return jsonify({
            'success': True,
            'status': 'active',
            'version': '3.0.0',
            'cache': {
                'buildings_loaded': len(app_cache['buildings']),
                'consumption_points': consumption_points,
                'weather_points': weather_points
            },
            'config': {
                'available_zones': list(MalaysiaConfig.ZONES.keys()),
                'supported_formats': ['csv', 'parquet', 'xlsx'],
                'export_directory': str(AppConfig.EXPORTS_DIR)
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur statut: {e}")
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


# ==============================================================================
# POINT D'ENTRÉE
# ==============================================================================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🇲🇾 MALAYSIA ELECTRICITY GENERATOR v3.0 - FACTORISÉ")
    logger.info("="*60)
    logger.info("✨ Architecture modulaire avec séparation des responsabilités")
    logger.info("📁 3 fichiers d'export distincts")
    logger.info(f"🌐 URL: http://127.0.0.1:5000")
    logger.info("="*60)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )