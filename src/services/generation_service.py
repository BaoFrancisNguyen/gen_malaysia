#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERVICE DE GÉNÉRATION AMÉLIORÉ AVEC GÉOMÉTRIE - COUCHE SERVICE
=============================================================

Version améliorée compatible avec electricity_generator.py et water_generator.py
qui utilise la géométrie précise des polygones OSM et les données d'étages.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from src.core.electricity_generator import EnhancedElectricityGenerator
from src.core.water_generator import WaterGenerator
from src.core.generator import WeatherGenerator  # Météo reste standard
from src.utils.validators import validate_date_range, validate_frequency
from src.utils.helpers import (generate_session_id, robust_building_list_validation, 
                              normalize_building_data, safe_float_parse)

logger = logging.getLogger(__name__)


class EnhancedGenerationService:
    """Service métier pour la génération de données amélioré avec géométrie précise"""
    
    def __init__(self):
        """Initialise le service de génération amélioré"""
        self.electricity_generator = EnhancedElectricityGenerator()  # Version améliorée
        self.water_generator = WaterGenerator()  # Version améliorée
        self.weather_generator = WeatherGenerator()  # Version standard
        self.generation_sessions = []
        logger.info("✅ EnhancedGenerationService initialisé avec générateurs géométriques")
    
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
        Génère les données selon la sélection utilisateur - VERSION GÉOMÉTRIQUE AMÉLIORÉE
        
        Args:
            buildings: Liste des bâtiments avec géométrie précise et étages
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
            logger.info(f"🔄 Session génération améliorée: {session_id}")
            
            # Types sélectionnés
            selected_types = []
            if generate_electricity:
                selected_types.append('électricité (géométrique)')
            if generate_water:
                selected_types.append('eau (géométrique)')
            if generate_weather:
                selected_types.append('météo')
            
            logger.info(f"📊 Génération améliorée: {len(buildings)} bâtiments, types: {', '.join(selected_types)}")
            
            # VALIDATION ROBUSTE avec analyse géométrique
            validation_result = self._validate_enhanced_generation_parameters(
                buildings, start_date, end_date, frequency, weather_stations
            )
            
            if not validation_result['valid']:
                logger.error(f"❌ Validation échouée: {validation_result['errors']}")
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
            
            # PRÉTRAITEMENT DES BÂTIMENTS AMÉLIORÉ
            if buildings and (generate_electricity or generate_water):
                logger.info("🏗️ Prétraitement géométrique des bâtiments...")
                processed_buildings = self._preprocess_enhanced_buildings(buildings)
                logger.info(f"✅ {len(processed_buildings)} bâtiments prétraités avec géométrie")
                
                # Statistiques géométriques
                geometry_stats = self._analyze_buildings_geometry(processed_buildings)
                logger.info(f"📐 Géométrie: {geometry_stats['with_precise_geometry']} précis, "
                          f"{geometry_stats['with_floors_data']} avec étages")
            else:
                processed_buildings = []
                geometry_stats = {}
            
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
                'buildings_count': len(processed_buildings),
                'geometry_statistics': geometry_stats
            }
            
            # === GÉNÉRATION ÉLECTRICITÉ AMÉLIORÉE ===
            if generate_electricity and processed_buildings:
                logger.info("⚡ Génération électricité avec géométrie précise...")
                try:
                    electricity_result = self.electricity_generator.generate_consumption_timeseries(
                        buildings=processed_buildings,
                        start_date=start_date,
                        end_date=end_date,
                        frequency=frequency
                    )
                    
                    if electricity_result['success']:
                        results['consumption_data'] = electricity_result['data']
                        summary['consumption_points'] = electricity_result['metadata']['total_points']
                        summary['electricity_geometry_stats'] = electricity_result['metadata'].get('geometry_statistics', {})
                        logger.info(f"✅ Électricité géométrique: {summary['consumption_points']} points générés")
                    else:
                        logger.warning(f"⚠️ Erreur génération électricité: {electricity_result['error']}")
                        
                except Exception as e:
                    logger.error(f"❌ Exception génération électricité: {e}")
            
            # === GÉNÉRATION EAU AMÉLIORÉE ===
            if generate_water and processed_buildings:
                logger.info("💧 Génération eau avec géométrie précise...")
                try:
                    water_result = self.water_generator.generate_water_consumption_timeseries(
                        buildings=processed_buildings,
                        start_date=start_date,
                        end_date=end_date,
                        frequency=frequency
                    )
                    
                    if water_result['success']:
                        results['water_data'] = water_result['data']
                        summary['water_points'] = water_result['metadata']['total_points']
                        summary['water_geometry_stats'] = water_result['metadata'].get('water_statistics', {})
                        logger.info(f"✅ Eau géométrique: {summary['water_points']} points générés")
                    else:
                        logger.warning(f"⚠️ Erreur génération eau: {water_result['error']}")
                        
                except Exception as e:
                    logger.error(f"❌ Exception génération eau: {e}")
            
            # === GÉNÉRATION MÉTÉO (STANDARD) ===
            if generate_weather:
                logger.info("🌤️ Génération données météorologiques...")
                try:
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
                        
                except Exception as e:
                    logger.error(f"❌ Exception génération météo: {e}")
            
            # Calcul du temps total
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Enregistrement de la session améliorée
            session_info = {
                'session_id': session_id,
                'generation_time': start_time.isoformat(),
                'generation_duration_seconds': generation_time,
                'enhanced_features': True,
                'geometry_processing': True,
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
                generated_types.append('électricité (géométrique)')
            if results['water_data'] is not None:
                generated_types.append('eau (géométrique)')
            if results['weather_data'] is not None:
                generated_types.append('météo')
            
            # Vérification qu'au moins quelque chose a été généré
            total_generated = summary['consumption_points'] + summary['water_points'] + summary['weather_points']
            
            if total_generated == 0:
                logger.warning("⚠️ Aucune donnée générée")
                return {
                    'success': False,
                    'error': 'Aucune donnée générée - vérifiez les paramètres',
                    'session_id': session_id,
                    'summary': summary
                }
            
            logger.info(f"✅ Session améliorée {session_id} terminée: {', '.join(generated_types)} en {generation_time:.1f}s")
            
            return {
                'success': True,
                'session_id': session_id,
                'consumption_data': results['consumption_data'],
                'water_data': results['water_data'],
                'weather_data': results['weather_data'],
                'summary': summary,
                'session_info': session_info,
                'generated_types': generated_types,
                'enhanced_features_used': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur service génération amélioré: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def _validate_enhanced_generation_parameters(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str,
        weather_stations: int
    ) -> Dict:
        """
        Valide les paramètres de génération avec vérification géométrique
        
        Args:
            buildings: Liste des bâtiments avec géométrie
            start_date: Date début
            end_date: Date fin
            frequency: Fréquence
            weather_stations: Nombre de stations météo
            
        Returns:
            Dict: Résultat de validation améliorée
        """
        errors = []
        warnings = []
        
        # Validation bâtiments avec analyse géométrique
        if not buildings or not isinstance(buildings, list):
            warnings.append("Aucun bâtiment fourni - seule météo sera générée")
        elif len(buildings) == 0:
            warnings.append("Liste de bâtiments vide - seule météo sera générée")
        else:
            # Validation géométrique des bâtiments
            geometry_analysis = self._quick_geometry_analysis(buildings)
            
            if geometry_analysis['valid_buildings'] == 0:
                errors.append("Aucun bâtiment valide avec géométrie")
            elif geometry_analysis['geometry_rate'] < 0.5:
                warnings.append(f"Peu de bâtiments avec géométrie précise ({geometry_analysis['geometry_rate']:.1%})")
            
            if geometry_analysis['floors_rate'] < 0.3:
                warnings.append(f"Peu de données d'étages disponibles ({geometry_analysis['floors_rate']:.1%})")
        
        # Validation dates (stricte - c'est critique)
        if not start_date or not end_date:
            errors.append("Dates de début et fin requises")
        elif not validate_date_range(start_date, end_date):
            errors.append("Plage de dates invalide")
        else:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                duration_days = (end - start).days
                
                if duration_days > 365:
                    warnings.append("Période très longue (>1 an)")
                elif duration_days < 0:
                    errors.append("Date de fin avant date de début")
            except ValueError:
                errors.append("Format de dates invalide (YYYY-MM-DD requis)")
        
        # Validation fréquence (stricte)
        if not frequency:
            errors.append("Fréquence requise")
        elif not validate_frequency(frequency):
            errors.append(f"Fréquence non supportée: {frequency}")
        
        # Validation stations météo (permissive)
        try:
            stations = int(weather_stations)
            if stations < 1:
                warnings.append("Nombre de stations météo < 1 - utilisation de 1")
            elif stations > 50:
                warnings.append("Nombre très élevé de stations météo")
        except (ValueError, TypeError):
            warnings.append("Nombre de stations météo invalide - utilisation de 5")
        
        return {
            'valid': len(errors) == 0,  # Seules les erreurs critiques bloquent
            'errors': errors,
            'warnings': warnings
        }
    
    def _quick_geometry_analysis(self, buildings: List[Dict]) -> Dict:
        """
        Analyse rapide de la qualité géométrique des bâtiments
        
        Args:
            buildings: Liste des bâtiments
            
        Returns:
            Dict: Analyse de qualité géométrique
        """
        if not buildings:
            return {
                'valid_buildings': 0,
                'geometry_rate': 0.0,
                'floors_rate': 0.0
            }
        
        # Échantillonnage pour performance
        sample_size = min(50, len(buildings))
        sample = buildings[:sample_size]
        
        valid_buildings = 0
        with_geometry = 0
        with_floors = 0
        
        for building in sample:
            if isinstance(building, dict) and building:
                valid_buildings += 1
                
                # Vérification géométrie
                geometry = building.get('geometry', [])
                if geometry and len(geometry) >= 3:
                    with_geometry += 1
                
                # Vérification étages
                floors = building.get('floors_count') or building.get('building_levels')
                if floors and floors > 1:
                    with_floors += 1
        
        # Extrapolation si échantillon
        if sample_size < len(buildings):
            factor = len(buildings) / sample_size
            valid_buildings = int(valid_buildings * factor)
            with_geometry = int(with_geometry * factor)
            with_floors = int(with_floors * factor)
        
        return {
            'valid_buildings': valid_buildings,
            'geometry_rate': with_geometry / len(buildings) if buildings else 0,
            'floors_rate': with_floors / len(buildings) if buildings else 0,
            'sample_size': sample_size
        }
    
    def _preprocess_enhanced_buildings(self, buildings: List[Dict]) -> List[Dict]:
        """
        Prétraite les bâtiments pour la génération géométrique améliorée
        
        Args:
            buildings: Liste des bâtiments bruts
            
        Returns:
            List[Dict]: Bâtiments prétraités et enrichis
        """
        processed_buildings = []
        
        for i, building in enumerate(buildings):
            try:
                # Normalisation de base
                normalized = normalize_building_data(building)
                
                # Enrichissement géométrique
                enhanced = self._enhance_building_geometry(normalized, i)
                
                # Enrichissement métadonnées étages
                enhanced = self._enhance_building_floors(enhanced)
                
                # Validation finale
                if self._is_valid_enhanced_building(enhanced):
                    processed_buildings.append(enhanced)
                
            except Exception as e:
                logger.debug(f"Erreur prétraitement bâtiment {i}: {e}")
                # Bâtiment de fallback minimal
                fallback = self._create_fallback_building(i)
                processed_buildings.append(fallback)
        
        return processed_buildings
    
    def _enhance_building_geometry(self, building: Dict, index: int) -> Dict:
        """
        Enrichit les données géométriques d'un bâtiment
        
        Args:
            building: Bâtiment normalisé
            index: Index du bâtiment
            
        Returns:
            Dict: Bâtiment avec géométrie enrichie
        """
        enhanced = building.copy()
        
        # Vérification géométrie existante
        geometry = building.get('geometry', [])
        
        if geometry and len(geometry) >= 3:
            # Géométrie précise disponible
            enhanced['has_precise_geometry'] = True
            enhanced['geometry_source'] = 'osm_polygon'
            
            # Calcul surface précise si pas déjà fait
            if 'polygon_area_m2' not in enhanced:
                enhanced['polygon_area_m2'] = self._calculate_polygon_area_simple(geometry)
            
            # Utilise la surface du polygone si disponible
            if enhanced['polygon_area_m2'] > 0:
                enhanced['surface_area_m2'] = enhanced['polygon_area_m2']
            
        else:
            # Pas de géométrie précise - créer géométrie approximative
            enhanced['has_precise_geometry'] = False
            enhanced['geometry_source'] = 'estimated'
            enhanced['geometry'] = self._create_approximate_geometry(building)
            enhanced['polygon_area_m2'] = enhanced.get('surface_area_m2', 100.0)
        
        # Métadonnées géométriques
        enhanced['geometry_metadata'] = {
            'has_precise_geometry': enhanced['has_precise_geometry'],
            'geometry_source': enhanced['geometry_source'],
            'points_count': len(enhanced.get('geometry', [])),
            'polygon_area_m2': enhanced.get('polygon_area_m2', 0)
        }
        
        return enhanced
    
    def _enhance_building_floors(self, building: Dict) -> Dict:
        """
        Enrichit les données d'étages d'un bâtiment
        
        Args:
            building: Bâtiment avec géométrie
            
        Returns:
            Dict: Bâtiment avec données d'étages enrichies
        """
        enhanced = building.copy()
        
        # Extraction étages depuis diverses sources
        floors_count = None
        floors_source = 'estimated'
        floors_confidence = 'low'
        
        # Sources prioritaires
        floors_sources = [
            (building.get('building_levels'), 'building_levels', 'high'),
            (building.get('floors_count'), 'floors_count', 'high'),
            (building.get('levels'), 'levels', 'medium'),
            (building.get('osm_tags', {}).get('building:levels'), 'osm:building:levels', 'high'),
            (building.get('tags', {}).get('building:levels'), 'tags:building:levels', 'high'),
            (building.get('osm_tags', {}).get('levels'), 'osm:levels', 'medium'),
            (building.get('tags', {}).get('levels'), 'tags:levels', 'medium')
        ]
        
        for value, source, confidence in floors_sources:
            if value is not None:
                try:
                    floors = int(float(value))
                    if 1 <= floors <= 200:
                        floors_count = floors
                        floors_source = source
                        floors_confidence = confidence
                        break
                except (ValueError, TypeError):
                    continue
        
        # Estimation si pas de données
        if floors_count is None:
            building_type = building.get('building_type', 'residential')
            floors_count = self._estimate_floors_by_type(building_type)
            floors_source = 'type_estimation'
            floors_confidence = 'low'
        
        # Application des données d'étages
        enhanced['floors_count'] = floors_count
        enhanced['building_levels'] = floors_count
        enhanced['levels_source'] = floors_source
        enhanced['levels_confidence'] = floors_confidence
        
        # Métadonnées d'étages
        enhanced['floors_metadata'] = {
            'floors_count': floors_count,
            'source': floors_source,
            'confidence': floors_confidence,
            'estimated': floors_source.endswith('estimation')
        }
        
        return enhanced
    
    def _estimate_floors_by_type(self, building_type: str) -> int:
        """
        Estime le nombre d'étages selon le type de bâtiment
        
        Args:
            building_type: Type de bâtiment
            
        Returns:
            int: Nombre d'étages estimé
        """
        import numpy as np
        
        if building_type == 'residential':
            return np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
        elif building_type in ['office', 'commercial']:
            return np.random.choice([1, 2, 3, 4, 5, 6], p=[0.2, 0.3, 0.2, 0.15, 0.1, 0.05])
        elif building_type == 'industrial':
            return np.random.choice([1, 2], p=[0.8, 0.2])
        elif building_type == 'hospital':
            return np.random.choice([2, 3, 4, 5], p=[0.2, 0.4, 0.3, 0.1])
        else:
            return 1
    
    def _calculate_polygon_area_simple(self, geometry: List[Dict]) -> float:
        """
        Calcule la surface d'un polygone de manière simplifiée
        
        Args:
            geometry: Points du polygone
            
        Returns:
            float: Surface en m²
        """
        if not geometry or len(geometry) < 3:
            return 100.0
        
        try:
            # Extraction coordonnées
            coordinates = []
            for point in geometry:
                if isinstance(point, dict) and 'lat' in point and 'lon' in point:
                    coordinates.append((point['lat'], point['lon']))
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    coordinates.append((point[0], point[1]))
            
            if len(coordinates) < 3:
                return 100.0
            
            # Shoelace simple
            area = 0.0
            n = len(coordinates)
            for i in range(n):
                j = (i + 1) % n
                area += coordinates[i][0] * coordinates[j][1]
                area -= coordinates[j][0] * coordinates[i][1]
            
            area = abs(area) / 2.0
            
            # Conversion approximative en m²
            area_m2 = area * (111000 ** 2)
            
            return max(min(area_m2, 100000), 10.0)
            
        except Exception:
            return 100.0
    
    def _create_approximate_geometry(self, building: Dict) -> List[Dict]:
        """
        Crée une géométrie approximative pour un bâtiment sans polygone
        
        Args:
            building: Données du bâtiment
            
        Returns:
            List[Dict]: Géométrie approximative (carré)
        """
        lat = building.get('latitude', 3.1390)
        lon = building.get('longitude', 101.6869)
        surface = building.get('surface_area_m2', 100.0)
        
        # Calcul côté du carré équivalent
        side_m = (surface ** 0.5)
        
        # Conversion en degrés (approximatif)
        side_deg = side_m / 111000
        
        # Carré centré sur les coordonnées
        geometry = [
            {'lat': lat - side_deg/2, 'lon': lon - side_deg/2},
            {'lat': lat - side_deg/2, 'lon': lon + side_deg/2},
            {'lat': lat + side_deg/2, 'lon': lon + side_deg/2},
            {'lat': lat + side_deg/2, 'lon': lon - side_deg/2},
            {'lat': lat - side_deg/2, 'lon': lon - side_deg/2}  # Fermeture
        ]
        
        return geometry
    
    def _is_valid_enhanced_building(self, building: Dict) -> bool:
        """
        Vérifie si un bâtiment enrichi est valide
        
        Args:
            building: Bâtiment enrichi
            
        Returns:
            bool: True si valide
        """
        # Vérifications de base
        if not isinstance(building, dict):
            return False
        
        # ID requis
        if not building.get('unique_id'):
            return False
        
        # Coordonnées requises
        lat = building.get('latitude')
        lon = building.get('longitude')
        if lat is None or lon is None:
            return False
        
        # Coordonnées Malaysia
        if not (0.5 <= lat <= 7.5 and 99.0 <= lon <= 120.0):
            return False
        
        # Surface positive
        surface = building.get('surface_area_m2', 0)
        if surface <= 0:
            return False
        
        # Étages positifs
        floors = building.get('floors_count', 0)
        if floors < 1:
            return False
        
        return True
    
    def _create_fallback_building(self, index: int) -> Dict:
        """
        Crée un bâtiment de fallback minimal
        
        Args:
            index: Index du bâtiment
            
        Returns:
            Dict: Bâtiment de fallback
        """
        return {
            'unique_id': f'fallback_enhanced_{index}',
            'building_type': 'residential',
            'latitude': 3.1390 + (index % 10) * 0.001,
            'longitude': 101.6869 + (index % 10) * 0.001,
            'surface_area_m2': 100.0,
            'floors_count': 1,
            'zone_name': 'unknown',
            'source': 'fallback_enhanced',
            'has_precise_geometry': False,
            'geometry': self._create_approximate_geometry({
                'latitude': 3.1390 + (index % 10) * 0.001,
                'longitude': 101.6869 + (index % 10) * 0.001,
                'surface_area_m2': 100.0
            }),
            'polygon_area_m2': 100.0,
            'building_levels': 1,
            'levels_source': 'fallback',
            'levels_confidence': 'low',
            'geometry_metadata': {
                'has_precise_geometry': False,
                'geometry_source': 'fallback',
                'points_count': 5,
                'polygon_area_m2': 100.0
            },
            'floors_metadata': {
                'floors_count': 1,
                'source': 'fallback',
                'confidence': 'low',
                'estimated': True
            }
        }
    
    def _analyze_buildings_geometry(self, buildings: List[Dict]) -> Dict:
        """
        Analyse la géométrie des bâtiments prétraités
        
        Args:
            buildings: Bâtiments prétraités
            
        Returns:
            Dict: Statistiques géométriques
        """
        if not buildings:
            return {}
        
        total = len(buildings)
        with_precise_geometry = sum(1 for b in buildings if b.get('has_precise_geometry', False))
        with_floors_data = sum(1 for b in buildings if b.get('levels_confidence', 'low') != 'low')
        multi_floor = sum(1 for b in buildings if b.get('floors_count', 1) > 1)
        
        total_surface = sum(b.get('surface_area_m2', 0) for b in buildings)
        total_floors = sum(b.get('floors_count', 1) for b in buildings)
        
        return {
            'total_buildings': total,
            'with_precise_geometry': with_precise_geometry,
            'with_floors_data': with_floors_data,
            'multi_floor_buildings': multi_floor,
            'geometry_rate': round(with_precise_geometry / total, 3),
            'floors_data_rate': round(with_floors_data / total, 3),
            'multi_floor_rate': round(multi_floor / total, 3),
            'total_surface_area_m2': round(total_surface, 1),
            'average_surface_area_m2': round(total_surface / total, 1),
            'total_floors': total_floors,
            'average_floors': round(total_floors / total, 2)
        }
    
    # Méthodes de génération spécialisées
    def generate_electricity_only(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H'
    ) -> Dict:
        """Génère uniquement les données électriques avec géométrie"""
        return self.generate_all_data(
            buildings=buildings,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            generate_electricity=True,
            generate_water=False,
            generate_weather=False
        )
    
    def generate_water_only(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H'
    ) -> Dict:
        """Génère uniquement les données d'eau avec géométrie"""
        return self.generate_all_data(
            buildings=buildings,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            generate_electricity=False,
            generate_water=True,
            generate_weather=False
        )
    
    def generate_weather_only(
        self,
        start_date: str,
        end_date: str,
        frequency: str = '1H',
        weather_stations: int = 5
    ) -> Dict:
        """Génère uniquement les données météo (standard)"""
        return self.generate_all_data(
            buildings=[],
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            weather_stations=weather_stations,
            generate_electricity=False,
            generate_water=False,
            generate_weather=True
        )
    
    def get_service_statistics(self) -> Dict:
        """Retourne les statistiques du service amélioré"""
        if not self.generation_sessions:
            return {
                'total_sessions': 0,
                'average_generation_time': 0,
                'total_points_generated': 0,
                'enhanced_features': True
            }
        
        # Calculs statistiques
        total_sessions = len(self.generation_sessions)
        total_time = sum(s['generation_duration_seconds'] for s in self.generation_sessions)
        avg_time = total_time / total_sessions
        
        total_consumption = sum(s['summary']['consumption_points'] for s in self.generation_sessions)
        total_water = sum(s['summary']['water_points'] for s in self.generation_sessions)
        total_weather = sum(s['summary']['weather_points'] for s in self.generation_sessions)
        
        # Sessions avec fonctionnalités améliorées
        enhanced_sessions = sum(1 for s in self.generation_sessions if s.get('enhanced_features', False))
        
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
            'enhanced_sessions': enhanced_sessions,
            'enhancement_rate': round(enhanced_sessions / total_sessions, 3),
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
            },
            'enhanced_features': {
                'geometry_processing': True,
                'floors_extraction': True,
                'precise_surface_calculation': True,
                'shape_analysis': True
            }
        }