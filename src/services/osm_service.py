#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSM SERVICE CORRIGÉ - UTILISE LA MÉTHODE ADMINISTRATIVE
======================================================

Version corrigée plus robuste pour les gros volumes de bâtiments.
"""

import logging
from typing import Dict, List
from datetime import datetime

from src.core.osm_handler import OSMHandler
from config import MalaysiaConfig
from src.utils.validators import validate_zone_name
from src.utils.helpers import robust_building_list_validation, normalize_building_data

logger = logging.getLogger(__name__)


class OSMService:
    """Service métier pour les opérations OpenStreetMap - VERSION CORRIGÉE"""
    
    def __init__(self):
        """Initialise le service OSM"""
        self.osm_handler = OSMHandler()
        self.load_count = 0
        logger.info("✅ OSMService initialisé avec méthode administrative")
    
    def load_buildings_for_zone(self, zone_name: str) -> Dict:
        """
        Charge les bâtiments avec traitement robuste des gros volumes
        
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
            
            # Appel à la méthode administrative correcte
            if hasattr(self.osm_handler, 'fetch_buildings_from_relation'):
                result = self.osm_handler.fetch_buildings_from_relation(zone_name)
            else:
                result = self.osm_handler.fetch_buildings_administrative(zone_name)
            
            if result['success']:
                raw_buildings = result['buildings']
                logger.info(f"📋 Bâtiments OSM bruts reçus: {len(raw_buildings)}")
                
                # TRAITEMENT ROBUSTE DES BÂTIMENTS
                processed_buildings = self._process_buildings_robust(raw_buildings, zone_name)
                
                # Calcul de statistiques
                stats = self._calculate_zone_statistics_efficient(processed_buildings)
                
                logger.info(f"✅ Zone {zone_name}: {len(processed_buildings)} bâtiments traités")
                
                return {
                    'success': True,
                    'buildings': processed_buildings,
                    'buildings_data': processed_buildings,  # Pour la cartographie
                    'metadata': {
                        'zone_name': zone_name,
                        'zone_display_name': result.get('metadata', {}).get('zone_name', zone_name),
                        'building_count': len(processed_buildings),
                        'load_time_seconds': result.get('query_time_seconds', 0),
                        'method': 'administrative',
                        'relation_id': result.get('relation_id'),
                        'load_number': self.load_count,
                        'statistics': stats,
                        'loaded_at': datetime.now().isoformat(),
                        'map_recommended': self._should_show_map(zone_name, len(processed_buildings)),
                        'data_quality': self._assess_data_quality(raw_buildings, processed_buildings)
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
    
    def _process_buildings_robust(self, raw_buildings: List[Dict], zone_name: str) -> List[Dict]:
        """
        Traite les bâtiments de manière robuste pour gérer les gros volumes
        
        Args:
            raw_buildings: Bâtiments bruts depuis OSM
            zone_name: Nom de la zone
            
        Returns:
            List[Dict]: Bâtiments traités et enrichis
        """
        if not raw_buildings:
            logger.warning("⚠️ Aucun bâtiment brut à traiter")
            return []
        
        logger.info(f"🔄 Traitement robuste de {len(raw_buildings)} bâtiments...")
        
        # Pour les très gros volumes, traitement par batch
        batch_size = 5000 if len(raw_buildings) > 10000 else len(raw_buildings)
        processed_buildings = []
        
        for i in range(0, len(raw_buildings), batch_size):
            batch = raw_buildings[i:i + batch_size]
            
            logger.info(f"📦 Traitement batch {i//batch_size + 1}: {len(batch)} bâtiments")
            
            # Traitement robuste du batch
            batch_processed = self._process_building_batch(batch, zone_name)
            processed_buildings.extend(batch_processed)
            
            # Log de progression pour gros volumes
            if len(raw_buildings) > 10000 and (i + batch_size) % 20000 == 0:
                logger.info(f"📊 Progression: {i + batch_size}/{len(raw_buildings)} bâtiments traités")
        
        logger.info(f"✅ Traitement terminé: {len(processed_buildings)} bâtiments valides")
        return processed_buildings
    
    def _process_building_batch(self, batch: List[Dict], zone_name: str) -> List[Dict]:
        """
        Traite un batch de bâtiments de manière robuste
        
        Args:
            batch: Batch de bâtiments à traiter
            zone_name: Nom de la zone
            
        Returns:
            List[Dict]: Bâtiments traités
        """
        processed = []
        
        for building in batch:
            try:
                # Normalisation robuste
                normalized = normalize_building_data(building)
                
                # Ajout des métadonnées de zone
                normalized['zone_name'] = zone_name
                
                # Enrichissement minimal mais robuste
                normalized = self._enrich_building_metadata_minimal(normalized)
                
                processed.append(normalized)
                
            except Exception as e:
                # En cas d'erreur, on continue avec un bâtiment par défaut
                logger.debug(f"Erreur traitement bâtiment: {e}")
                continue
        
        return processed
    
    def _enrich_building_metadata_minimal(self, building: Dict) -> Dict:
        """
        Enrichit les métadonnées de manière minimale et robuste
        
        Args:
            building: Bâtiment de base
            
        Returns:
            Dict: Bâtiment enrichi
        """
        enriched = building.copy()
        
        # Ajout des informations de type si disponibles
        building_type = building.get('building_type', 'residential')
        
        try:
            type_config = MalaysiaConfig.get_building_type_config(building_type)
            enriched['building_type_info'] = {
                'type': building_type,
                'description': type_config.get('description', f"Bâtiment {building_type}"),
                'base_consumption_kwh_m2_day': type_config.get('base_consumption_kwh_m2_day', 1.0)
            }
        except Exception:
            # Fallback robuste
            enriched['building_type_info'] = {
                'type': building_type,
                'description': f"Bâtiment {building_type}",
                'base_consumption_kwh_m2_day': 1.0
            }
        
        # Coordonnées standardisées
        enriched['coordinates'] = {
            'latitude': building.get('latitude'),
            'longitude': building.get('longitude')
        }
        
        return enriched
    
    def _calculate_zone_statistics_efficient(self, buildings: List[Dict]) -> Dict:
        """
        Calcule les statistiques de zone de manière efficace
        
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
        
        # Calculs efficaces
        type_counts = {}
        total_surface = 0
        
        # Échantillonnage pour les gros volumes
        sample_size = min(1000, len(buildings))
        step = max(1, len(buildings) // sample_size)
        
        for i in range(0, len(buildings), step):
            building = buildings[i]
            building_type = building.get('building_type', 'unknown')
            type_counts[building_type] = type_counts.get(building_type, 0) + step
            
            surface = building.get('surface_area_m2', 0)
            if isinstance(surface, (int, float)) and surface > 0:
                total_surface += surface * step
        
        return {
            'total_buildings': len(buildings),
            'building_types': type_counts,
            'total_surface_m2': total_surface,
            'average_surface_m2': total_surface / len(buildings) if buildings else 0,
            'most_common_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else 'unknown',
            'sample_based': sample_size < len(buildings)
        }
    
    def _should_show_map(self, zone_name: str, building_count: int) -> bool:
        """
        Détermine si la carte doit être affichée
        
        Args:
            zone_name: Nom de la zone
            building_count: Nombre de bâtiments
            
        Returns:
            bool: True si la carte est recommandée
        """
        # Maintenant on recommande toujours la carte car on a l'échantillonnage intelligent
        return True
    
    def _assess_data_quality(self, raw_buildings: List[Dict], processed_buildings: List[Dict]) -> Dict:
        """
        Évalue la qualité des données
        
        Args:
            raw_buildings: Bâtiments bruts
            processed_buildings: Bâtiments traités
            
        Returns:
            Dict: Évaluation de qualité
        """
        if not raw_buildings:
            return {'quality': 'unknown', 'processing_rate': 0}
        
        processing_rate = len(processed_buildings) / len(raw_buildings)
        
        if processing_rate > 0.9:
            quality = 'excellent'
        elif processing_rate > 0.7:
            quality = 'good'
        elif processing_rate > 0.5:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'quality': quality,
            'processing_rate': round(processing_rate, 3),
            'raw_count': len(raw_buildings),
            'processed_count': len(processed_buildings),
            'discarded_count': len(raw_buildings) - len(processed_buildings)
        }
    
    def get_service_statistics(self) -> Dict:
        """Retourne les statistiques du service"""
        return {
            'total_loads': self.load_count,
            'service_status': 'active',
            'method': 'administrative_osm',
            'capabilities': {
                'large_datasets': True,
                'robust_processing': True,
                'batch_processing': True,
                'error_recovery': True
            }
        }