#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSM SERVICE - UTILISE LA MÉTHODE ADMINISTRATIVE
======================================================


"""

import logging
from typing import Dict, List
from datetime import datetime

from src.core.osm_handler import OSMHandler
from config import MalaysiaConfig
from src.utils.validators import validate_zone_name

logger = logging.getLogger(__name__)


class OSMService:
    """Service métier pour les opérations OpenStreetMap avec méthode administrative"""
    
    def __init__(self):
        """Initialise le service OSM"""
        self.osm_handler = OSMHandler()
        self.load_count = 0
        logger.info("✅ OSMService initialisé avec méthode administrative")
    
    def load_buildings_for_zone(self, zone_name: str) -> Dict:
        """
        MÉTHODE CORRIGÉE: Utilise la méthode administrative au lieu de bbox
        
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
            
            # 🎯 UTILISATION DE LA MÉTHODE ADMINISTRATIVE
            logger.info(f"🎯 Chargement administratif pour: {zone_name}")
            result = self.osm_handler.fetch_buildings_from_relation(zone_name)
            
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
                    'buildings_data': enriched_buildings,  # Pour la cartographie
                    'metadata': {
                        'zone_name': zone_name,
                        'zone_display_name': result.get('metadata', {}).get('zone_name', zone_name),
                        'building_count': len(enriched_buildings),
                        'load_time_seconds': result.get('query_time_seconds', 0),
                        'method': 'administrative',
                        'relation_id': result.get('relation_id'),
                        'load_number': self.load_count,
                        'statistics': stats,
                        'loaded_at': datetime.now().isoformat(),
                        'map_recommended': len(enriched_buildings) <= 5000 and zone_name != 'malaysia'
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Erreur inconnue'),
                    'buildings': []
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur service OSM: {e}")
            return {
                'success': False,
                'error': str(e),
                'buildings': []
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
            building_type = building.get('building_type', 'residential')
            
            # Configuration basique des types si MalaysiaConfig n'a pas la méthode
            try:
                type_config = MalaysiaConfig.get_building_type_config(building_type)
                enriched_building['building_type_info'] = {
                    'type': building_type,
                    'description': type_config['description'],
                    'base_consumption_kwh_m2_day': type_config['base_consumption_kwh_m2_day']
                }
            except:
                # Configuration par défaut
                enriched_building['building_type_info'] = {
                    'type': building_type,
                    'description': f"Bâtiment {building_type}",
                    'base_consumption_kwh_m2_day': 1.0
                }
            
            # Validation et nettoyage des coordonnées
            enriched_building['coordinates'] = {
                'latitude': building.get('latitude'),
                'longitude': building.get('longitude')
            }
            
            # Surface du bâtiment
            enriched_building['surface_area_m2'] = building.get('surface_area_m2', 100.0)
            
            # Identifiants
            enriched_building['building_id'] = building.get('building_id', f"gen_{len(enriched_buildings)}")
            enriched_building['osm_id'] = building.get('osm_id')
            
            enriched_buildings.append(enriched_building)
            
        return enriched_buildings
    
    def _calculate_zone_statistics(self, buildings: List[Dict]) -> Dict:
        """
        Calcule les statistiques de la zone
        
        Args:
            buildings: Liste des bâtiments
            
        Returns:
            Dict: Statistiques calculées
        """
        if not buildings:
            return {
                'total_buildings': 0,
                'building_types': {},
                'total_surface_m2': 0,
                'average_surface_m2': 0
            }
        
        # Comptage par type
        type_counts = {}
        total_surface = 0
        
        for building in buildings:
            building_type = building.get('building_type', 'unknown')
            type_counts[building_type] = type_counts.get(building_type, 0) + 1
            total_surface += building.get('surface_area_m2', 0)
        
        return {
            'total_buildings': len(buildings),
            'building_types': type_counts,
            'total_surface_m2': total_surface,
            'average_surface_m2': total_surface / len(buildings) if buildings else 0,
            'most_common_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else 'unknown'
        }