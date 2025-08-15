#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERVICE DE GÉNÉRATION - COUCHE SERVICE
======================================

Service métier pour orchestrer la génération des données électriques, météo et eau.
Coordonne les appels aux générateurs et gère la logique métier.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from src.core.generator import ElectricityGenerator, WeatherGenerator, WaterGenerator
from src.utils.validators import validate_date_range, validate_frequency, validate_building_list
from src.utils.helpers import generate_session_id

logger = logging.getLogger(__name__)


class GenerationService:
    """Service métier pour la génération de données"""
    
    def __init__(self):
        """Initialise le service de génération"""
        self.electricity_generator = ElectricityGenerator()
        self.weather_generator = WeatherGenerator()
        self.water_generator = WaterGenerator()
        self.generation_sessions = []
        logger.info("✅ GenerationService initialisé avec générateurs électricité, météo et eau")
    
    def generate_all_data(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H',
        weather_stations: int = 5,
        generate_electricity: bool = True,
        generate_water: bool = True,
        generate_weather: bool = True
    ) -> Dict:
        """
        Génère les données selon la sélection utilisateur
        
        Args:
            buildings: Liste des bâtiments
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            frequency: Fréquence d'échantillonnage
            weather_stations: Nombre de stations météo
            generate_electricity: Si True, génère consommation électrique
            generate_water: Si True, génère consommation eau
            generate_weather: Si True, génère données météo
            
        Returns:
            Dict: Résultat avec toutes les données générées
        """
        session_id = generate_session_id()
        start_time = datetime.now()
        
        try:
            logger.info(f"🔄 Session génération: {session_id}")
            
            # Types sélectionnés
            selected_types = []
            if generate_electricity:
                selected_types.append('électricité')
            if generate_water:
                selected_types.append('eau')
            if generate_weather:
                selected_types.append('météo')
            
            logger.info(f"📊 Génération: {len(buildings)} bâtiments, types: {', '.join(selected_types)}")
            
            # Validation des paramètres
            validation_result = self._validate_generation_parameters(
                buildings, start_date, end_date, frequency, weather_stations
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'Paramètres invalides',
                    'validation_errors': validation_result['errors'],
                    'session_id': session_id
                }
            
            # Validation qu'au moins un type est sélectionné
            if not any([generate_electricity, generate_water, generate_weather]):
                return {
                    'success': False,
                    'error': 'Aucun type de données sélectionné',
                    'session_id': session_id
                }
            
            # Résultats de génération
            results = {
                'consumption_data': None,
                'water_data': None,
                'weather_data': None
            }
            
            summary = {
                'consumption_points': 0,
                'water_points': 0,
                'weather_points': 0,
                'buildings_count': len(buildings)
            }
            
            # === GÉNÉRATION ÉLECTRICITÉ ===
            if generate_electricity:
                logger.info("⚡ Génération des données électriques...")
                electricity_result = self.electricity_generator.generate_consumption_timeseries(
                    buildings=buildings,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency
                )
                
                if electricity_result['success']:
                    results['consumption_data'] = electricity_result['data']
                    summary['consumption_points'] = electricity_result['metadata']['total_points']
                    logger.info(f"✅ Électricité: {summary['consumption_points']} points générés")
                else:
                    logger.warning(f"⚠️ Erreur génération électricité: {electricity_result['error']}")
            
            # === GÉNÉRATION EAU ===
            if generate_water:
                logger.info("💧 Génération des données de consommation d'eau...")
                water_result = self.water_generator.generate_water_consumption_timeseries(
                    buildings=buildings,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency
                )
                
                if water_result['success']:
                    results['water_data'] = water_result['data']
                    summary['water_points'] = water_result['metadata']['total_points']
                    logger.info(f"✅ Eau: {summary['water_points']} points générés")
                else:
                    logger.warning(f"⚠️ Erreur génération eau: {water_result['error']}")
            
            # === GÉNÉRATION MÉTÉO ===
            if generate_weather:
                logger.info("🌤️ Génération des données météorologiques...")
                weather_result = self.weather_generator.generate_weather_timeseries(
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    station_count=weather_stations
                )
                
                if weather_result['success']:
                    results['weather_data'] = weather_result['data']
                    summary['weather_points'] = weather_result['metadata']['total_observations']
                    logger.info(f"✅ Météo: {summary['weather_points']} points générés")
                else:
                    logger.warning(f"⚠️ Erreur génération météo: {weather_result['error']}")
            
            # Calcul du temps total
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Enregistrement de la session
            session_info = {
                'session_id': session_id,
                'generation_time': start_time.isoformat(),
                'generation_duration_seconds': generation_time,
                'parameters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'frequency': frequency,
                    'weather_stations': weather_stations,
                    'generate_electricity': generate_electricity,
                    'generate_water': generate_water,
                    'generate_weather': generate_weather
                },
                'summary': summary
            }
            
            self.generation_sessions.append(session_info)
            
            # Garde seulement les 20 dernières sessions
            if len(self.generation_sessions) > 20:
                self.generation_sessions = self.generation_sessions[-20:]
            
            # Types générés avec succès
            generated_types = []
            if results['consumption_data'] is not None:
                generated_types.append('électricité')
            if results['water_data'] is not None:
                generated_types.append('eau')
            if results['weather_data'] is not None:
                generated_types.append('météo')
            
            logger.info(f"✅ Session {session_id} terminée: {', '.join(generated_types)} en {generation_time:.1f}s")
            
            return {
                'success': True,
                'session_id': session_id,
                'consumption_data': results['consumption_data'],
                'water_data': results['water_data'],
                'weather_data': results['weather_data'],
                'summary': summary,
                'session_info': session_info,
                'generated_types': generated_types
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur service génération: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def _validate_generation_parameters(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str,
        weather_stations: int
    ) -> Dict:
        """
        Valide les paramètres de génération
        
        Args:
            buildings: Liste des bâtiments
            start_date: Date début
            end_date: Date fin
            frequency: Fréquence
            weather_stations: Nombre de stations météo
            
        Returns:
            Dict: Résultat de validation
        """
        errors = []
        warnings = []
        
        # Validation bâtiments
        if not buildings:
            errors.append("Aucun bâtiment fourni")
        else:
            building_validation = validate_building_list(buildings)
            if not building_validation['valid']:
                errors.extend(building_validation['errors'][:5])  # Limite à 5 erreurs
            
            if building_validation['validation_rate'] < 0.8:
                warnings.append("Taux de validation des bâtiments faible")
        
        # Validation dates
        if not validate_date_range(start_date, end_date):
            errors.append("Plage de dates invalide")
        else:
            # Calcul de la durée
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
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def generate_electricity_only(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H'
    ) -> Dict:
        """
        Génère uniquement les données électriques
        
        Args:
            buildings: Liste des bâtiments
            start_date: Date début
            end_date: Date fin
            frequency: Fréquence
            
        Returns:
            Dict: Résultat avec données électriques
        """
        return self.generate_all_data(
            buildings=buildings,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            generate_electricity=True,
            generate_water=False,
            generate_weather=False
        )
    
    def generate_weather_only(
        self,
        start_date: str,
        end_date: str,
        frequency: str = '1H',
        weather_stations: int = 5
    ) -> Dict:
        """
        Génère uniquement les données météo
        
        Args:
            start_date: Date début
            end_date: Date fin
            frequency: Fréquence
            weather_stations: Nombre de stations
            
        Returns:
            Dict: Résultat avec données météo
        """
        return self.generate_all_data(
            buildings=[],  # Pas de bâtiments nécessaires pour météo
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            weather_stations=weather_stations,
            generate_electricity=False,
            generate_water=False,
            generate_weather=True
        )
    
    def generate_water_only(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H'
    ) -> Dict:
        """
        Génère uniquement les données d'eau
        
        Args:
            buildings: Liste des bâtiments
            start_date: Date début
            end_date: Date fin
            frequency: Fréquence
            
        Returns:
            Dict: Résultat avec données eau
        """
        return self.generate_all_data(
            buildings=buildings,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            generate_electricity=False,
            generate_water=True,
            generate_weather=False
        )
    
    def get_service_statistics(self) -> Dict:
        """
        Retourne les statistiques du service
        
        Returns:
            Dict: Statistiques d'utilisation
        """
        if not self.generation_sessions:
            return {
                'total_sessions': 0,
                'average_generation_time': 0,
                'total_points_generated': 0
            }
        
        # Calculs statistiques
        total_sessions = len(self.generation_sessions)
        total_time = sum(s['generation_duration_seconds'] for s in self.generation_sessions)
        avg_time = total_time / total_sessions
        
        total_consumption = sum(s['summary']['consumption_points'] for s in self.generation_sessions)
        total_water = sum(s['summary']['water_points'] for s in self.generation_sessions)
        total_weather = sum(s['summary']['weather_points'] for s in self.generation_sessions)
        
        # Répartition par type
        type_counts = {'electricity': 0, 'water': 0, 'weather': 0}
        for session in self.generation_sessions:
            params = session['parameters']
            if params.get('generate_electricity'):
                type_counts['electricity'] += 1
            if params.get('generate_water'):
                type_counts['water'] += 1
            if params.get('generate_weather'):
                type_counts['weather'] += 1
        
        return {
            'total_sessions': total_sessions,
            'average_generation_time_seconds': round(avg_time, 2),
            'total_points_generated': {
                'consumption': total_consumption,
                'water': total_water,
                'weather': total_weather,
                'total': total_consumption + total_water + total_weather
            },
            'generation_type_distribution': type_counts,
            'recent_sessions': self.generation_sessions[-5:],
            'generators_status': {
                'electricity_generation_count': self.electricity_generator.generation_count,
                'weather_generation_count': self.weather_generator.generation_count,
                'water_generation_count': self.water_generator.generation_count
            }
        }