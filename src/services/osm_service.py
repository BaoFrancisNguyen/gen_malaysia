#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERVICE OSM - COUCHE SERVICE
============================

Service métier pour les opérations OSM.
Orchestre les appels au OSMHandler et gère la logique métier.
"""

import logging
from typing import Dict, List
from datetime import datetime

from src.core.osm_handler import OSMHandler
from config import MalaysiaConfig
from src.utils.validators import validate_zone_name

logger = logging.getLogger(__name__)


class OSMService:
    """Service métier pour les opérations OpenStreetMap"""
    
    def __init__(self):
        """Initialise le service OSM"""
        self.osm_handler = OSMHandler()
        self.load_count = 0
        logger.info("✅ OSMService initialisé")
    
    def load_buildings_for_zone(self, zone_name: str) -> Dict:
        """
        Charge les bâtiments pour une zone Malaysia
        
        Args:
            zone_name: Nom de la zone (ex: 'kuala_lumpur')
            
        Returns:
            Dict: Résultat avec bâtiments et métadonnées enrichies
        """
        self.load_count += 1
        
        try:
            # Validation de la zone
            if not validate_zone_name(zone_name):
                return {
                    'success': False,
                    'error': f"Zone invalide: {zone_name}",
                    'available_zones': list(MalaysiaConfig.ZONES.keys())
                }
            
            # Récupération de la configuration de zone
            zone_config = MalaysiaConfig.get_zone_config(zone_name)
            logger.info(f"🏢 Chargement OSM zone: {zone_config['name']}")
            
            # Appel au handler OSM
            result = self.osm_handler.fetch_buildings_from_bbox(zone_config['bbox'])
            
            if result['success']:
                # Enrichissement des métadonnées
                buildings = result['buildings']
                enriched_buildings = self._enrich_buildings_metadata(buildings, zone_name)
                
                # Calcul de statistiques
                stats = self._calculate_zone_statistics(enriched_buildings)
                
                logger.info(f"✅ Zone {zone_name}: {len(enriched_buildings)} bâtiments chargés")
                
                return {
                    'success': True,
                    'buildings': enriched_buildings,
                    'buildings_data': enriched_buildings,  # Ajout pour la cartographie
                    'metadata': {
                        'zone_name': zone_name,
                        'zone_display_name': zone_config['name'],
                        'building_count': len(enriched_buildings),
                        'load_time_seconds': result['metadata']['query_time_seconds'],
                        'bbox': zone_config['bbox'],
                        'load_number': self.load_count,
                        'statistics': stats,
                        'loaded_at': datetime.now().isoformat(),
                        'map_recommended': len(enriched_buildings) <= 5000 and zone_name != 'malaysia'
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Erreur service OSM: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _enrich_buildings_metadata(self, buildings: List[Dict], zone_name: str) -> List[Dict]:
        """
        Enrichit les métadonnées des bâtiments
        
        Args:
            buildings: Liste des bâtiments de base
            zone_name: Nom de la zone
            
        Returns:
            List[Dict]: Bâtiments avec métadonnées enrichies
        """
        enriched_buildings = []
        
        for building in buildings:
            # Ajout des métadonnées de zone
            enriched_building = building.copy()
            enriched_building['zone_name'] = zone_name
            
            # Enrichissement du type de bâtiment
            building_type = building['building_type']
            type_config = MalaysiaConfig.get_building_type_config(building_type)
            enriched_building['building_type_info'] = {
                'type': building_type,
                'description': type_config['description'],
                'base_consumption_kwh_m2_day': type_config['base_consumption_kwh_m2_day']
            }
            
            # Validation et nettoyage des coordonnées
            enriched_building['coordinates'] = {
                'latitude': round(building['latitude'], 6),
                'longitude': round(building['longitude'], 6)
            }
            
            # Formatage de la surface
            enriched_building['surface_area_m2'] = round(building['surface_area_m2'], 1)
            
            # Métadonnées de traitement
            enriched_building['processing_metadata'] = {
                'enriched_at': datetime.now().isoformat(),
                'source_system': 'malaysia_electricity_generator_v3',
                'data_quality': self._assess_building_quality(building)
            }
            
            enriched_buildings.append(enriched_building)
        
        return enriched_buildings
    
    def _assess_building_quality(self, building: Dict) -> str:
        """
        Évalue la qualité des données d'un bâtiment
        
        Args:
            building: Données du bâtiment
            
        Returns:
            str: Niveau de qualité ('excellent', 'good', 'acceptable', 'poor')
        """
        score = 100
        
        # Vérification surface
        surface = building.get('surface_area_m2', 0)
        if surface < 20:
            score -= 20  # Surface très petite
        elif surface > 10000:
            score -= 10  # Surface très grande (potentiel outlier)
        
        # Vérification coordonnées
        lat = building.get('latitude', 0)
        lon = building.get('longitude', 0)
        if not (0.5 <= lat <= 7.5 and 99.5 <= lon <= 119.5):
            score -= 30  # Hors limites Malaysia
        
        # Vérification tags OSM
        osm_tags = building.get('osm_tags', {})
        if not osm_tags or len(osm_tags) < 2:
            score -= 15  # Peu de métadonnées OSM
        
        # Classification qualité
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'acceptable'
        else:
            return 'poor'
    
    def _calculate_zone_statistics(self, buildings: List[Dict]) -> Dict:
        """
        Calcule les statistiques d'une zone
        
        Args:
            buildings: Liste des bâtiments
            
        Returns:
            Dict: Statistiques de la zone
        """
        if not buildings:
            return {}
        
        # Distribution par type
        type_counts = {}
        total_surface = 0
        quality_counts = {'excellent': 0, 'good': 0, 'acceptable': 0, 'poor': 0}
        
        for building in buildings:
            # Comptage par type
            btype = building['building_type']
            type_counts[btype] = type_counts.get(btype, 0) + 1
            
            # Surface totale
            total_surface += building['surface_area_m2']
            
            # Qualité
            quality = building['processing_metadata']['data_quality']
            quality_counts[quality] += 1
        
        # Calculs statistiques
        building_count = len(buildings)
        avg_surface = total_surface / building_count if building_count > 0 else 0
        
        return {
            'total_buildings': building_count,
            'total_surface_m2': round(total_surface, 1),
            'average_surface_m2': round(avg_surface, 1),
            'building_types_distribution': type_counts,
            'data_quality_distribution': quality_counts,
            'quality_percentage': {
                'high_quality': round((quality_counts['excellent'] + quality_counts['good']) / building_count * 100, 1),
                'acceptable_quality': round(quality_counts['acceptable'] / building_count * 100, 1),
                'poor_quality': round(quality_counts['poor'] / building_count * 100, 1)
            }
        }
    
    def get_service_statistics(self) -> Dict:
        """
        Retourne les statistiques du service
        
        Returns:
            Dict: Statistiques d'utilisation du service
        """
        osm_handler_stats = self.osm_handler.get_statistics()
        
        return {
            'service_loads': self.load_count,
            'osm_handler_stats': osm_handler_stats,
            'available_zones': list(MalaysiaConfig.ZONES.keys()),
            'supported_building_types': list(MalaysiaConfig.BUILDING_TYPES.keys())
        }