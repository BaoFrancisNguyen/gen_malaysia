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