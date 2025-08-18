#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSM SERVICE AMÉLIORÉ AVEC GÉOMÉTRIE - UTILISE EnhancedOSMHandler
===============================================================

Version améliorée qui utilise l'extraction géométrique complète et les métadonnées d'étages.
Compatible avec electricity_generator.py et water_generator.py.
"""

import logging
from typing import Dict, List
from datetime import datetime

from src.core.osm_handler import EnhancedOSMHandler  # Version améliorée
from config import MalaysiaConfig
from src.utils.validators import validate_zone_name
from src.utils.helpers import robust_building_list_validation, normalize_building_data

logger = logging.getLogger(__name__)


class EnhancedOSMService:
    """Service métier pour les opérations OpenStreetMap améliorées avec géométrie"""
    
    def __init__(self):
        """Initialise le service OSM amélioré"""
        self.osm_handler = EnhancedOSMHandler()  # Version améliorée
        self.load_count = 0
        logger.info("✅ EnhancedOSMService initialisé avec extraction géométrique complète")
    
    def load_buildings_for_zone(self, zone_name: str) -> Dict:
        """
        Charge les bâtiments avec traitement robuste et extraction géométrique complète
        
        Args:
            zone_name: Nom de la zone (ex: 'kuala_lumpur')
            
        Returns:
            Dict: Résultat avec bâtiments enrichis (géométrie + étages + métadonnées)
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
            
            # 🎯 UTILISATION DE LA MÉTHODE ADMINISTRATIVE AMÉLIORÉE
            logger.info(f"🎯 Chargement administratif amélioré pour: {zone_name}")
            
            # Appel à la méthode administrative améliorée
            result = self.osm_handler.fetch_buildings_administrative(zone_name)
            
            if result['success']:
                raw_buildings = result['buildings']
                logger.info(f"📋 Bâtiments OSM améliorés reçus: {len(raw_buildings)}")
                
                # TRAITEMENT ROBUSTE DES BÂTIMENTS AMÉLIORÉS
                processed_buildings = self._process_enhanced_buildings_robust(raw_buildings, zone_name)
                
                # Calcul de statistiques améliorées
                stats = self._calculate_enhanced_zone_statistics(processed_buildings)
                
                # Analyse de la qualité géométrique
                geometry_quality = self._assess_geometry_quality(processed_buildings)
                
                logger.info(f"✅ Zone {zone_name}: {len(processed_buildings)} bâtiments traités")
                logger.info(f"📐 Géométrie: {geometry_quality['with_precise_geometry']} précis, "
                          f"{geometry_quality['with_floors_data']} avec étages")
                
                return {
                    'success': True,
                    'buildings': processed_buildings,
                    'buildings_data': processed_buildings,  # Pour la cartographie
                    'metadata': {
                        'zone_name': zone_name,
                        'zone_display_name': result.get('metadata', {}).get('zone_name', zone_name),
                        'building_count': len(processed_buildings),
                        'load_time_seconds': result.get('query_time_seconds', 0),
                        'method': 'administrative_enhanced',
                        'relation_id': result.get('relation_id'),
                        'load_number': self.load_count,
                        'statistics': stats,
                        'geometry_quality': geometry_quality,
                        'processing_statistics': result.get('processing_statistics', {}),
                        'loaded_at': datetime.now().isoformat(),
                        'map_recommended': self._should_show_map(zone_name, len(processed_buildings)),
                        'enhanced_features': True,
                        'geometry_extraction': True,
                        'floors_extraction': True
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Erreur inconnue'),
                    'buildings': []
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur service OSM amélioré: {e}")
            return {
                'success': False,
                'error': str(e),
                'buildings': []
            }
    
    def _process_enhanced_buildings_robust(self, raw_buildings: List[Dict], zone_name: str) -> List[Dict]:
        """
        Traite les bâtiments améliorés de manière robuste pour gérer les gros volumes
        
        Args:
            raw_buildings: Bâtiments bruts depuis OSM avec géométrie
            zone_name: Nom de la zone
            
        Returns:
            List[Dict]: Bâtiments traités et enrichis avec géométrie
        """
        if not raw_buildings:
            logger.warning("⚠️ Aucun bâtiment brut à traiter")
            return []
        
        logger.info(f"🔄 Traitement robuste amélioré de {len(raw_buildings)} bâtiments...")
        
        # Pour les très gros volumes, traitement par batch
        batch_size = 3000 if len(raw_buildings) > 10000 else len(raw_buildings)
        processed_buildings = []
        
        for i in range(0, len(raw_buildings), batch_size):
            batch = raw_buildings[i:i + batch_size]
            
            logger.info(f"📦 Traitement batch amélioré {i//batch_size + 1}: {len(batch)} bâtiments")
            
            # Traitement robuste du batch avec enrichissement
            batch_processed = self._process_enhanced_building_batch(batch, zone_name)
            processed_buildings.extend(batch_processed)
            
            # Log de progression pour gros volumes
            if len(raw_buildings) > 10000 and (i + batch_size) % 15000 == 0:
                logger.info(f"📊 Progression améliorée: {i + batch_size}/{len(raw_buildings)} bâtiments traités")
        
        logger.info(f"✅ Traitement amélioré terminé: {len(processed_buildings)} bâtiments valides")
        return processed_buildings
    
    def _process_enhanced_building_batch(self, batch: List[Dict], zone_name: str) -> List[Dict]:
        """
        Traite un batch de bâtiments améliorés de manière robuste
        
        Args:
            batch: Batch de bâtiments à traiter
            zone_name: Nom de la zone
            
        Returns:
            List[Dict]: Bâtiments traités avec enrichissement
        """
        processed = []
        
        for building in batch:
            try:
                # Validation de base
                if not self._is_valid_enhanced_building_data(building):
                    continue
                
                # Normalisation robuste avec conservation des données enrichies
                normalized = self._normalize_enhanced_building_data(building, zone_name)
                
                # Validation finale
                if self._validate_enhanced_building_final(normalized):
                    processed.append(normalized)
                
            except Exception as e:
                # En cas d'erreur, on continue avec le suivant
                logger.debug(f"Erreur traitement bâtiment amélioré: {e}")
                continue
        
        return processed
    
    def _is_valid_enhanced_building_data(self, building: Dict) -> bool:
        """
        Vérifie si un bâtiment amélioré a des données de base valides
        
        Args:
            building: Données du bâtiment
            
        Returns:
            bool: True si valide
        """
        # Vérifications de base
        if not isinstance(building, dict) or not building:
            return False
        
        # ID requis
        if not building.get('unique_id') and not building.get('osm_id'):
            return False
        
        # Coordonnées requises
        lat = building.get('latitude')
        lon = building.get('longitude')
        if lat is None or lon is None:
            return False
        
        # Type de bâtiment requis
        if not building.get('building_type'):
            return False
        
        return True
    
    def _normalize_enhanced_building_data(self, building: Dict, zone_name: str) -> Dict:
        """
        Normalise les données d'un bâtiment amélioré en conservant les enrichissements
        
        Args:
            building: Bâtiment brut avec enrichissements
            zone_name: Nom de la zone
            
        Returns:
            Dict: Bâtiment normalisé avec enrichissements conservés
        """
        # Normalisation de base
        normalized = normalize_building_data(building)
        
        # Conservation et enrichissement des données spéciales
        
        # === GÉOMÉTRIE ===
        # Géométrie complète si disponible
        geometry = building.get('geometry', [])
        if geometry:
            normalized['geometry'] = geometry
            normalized['has_precise_geometry'] = building.get('has_precise_geometry', len(geometry) >= 3)
            normalized['geometry_source'] = building.get('geometry_source', 'osm')
            normalized['polygon_area_m2'] = building.get('polygon_area_m2', normalized.get('surface_area_m2', 100))
            normalized['polygon_perimeter_m'] = building.get('polygon_perimeter_m', 0)
            normalized['shape_complexity'] = building.get('shape_complexity', 1.0)
        else:
            normalized['geometry'] = []
            normalized['has_precise_geometry'] = False
            normalized['geometry_source'] = 'estimated'
            normalized['polygon_area_m2'] = normalized.get('surface_area_m2', 100)
            normalized['polygon_perimeter_m'] = 0
            normalized['shape_complexity'] = 1.0
        
        # === ÉTAGES ET STRUCTURE ===
        normalized['floors_count'] = building.get('floors_count', building.get('building_levels', 1))
        normalized['building_levels'] = normalized['floors_count']
        normalized['levels_source'] = building.get('levels_source', 'estimated')
        normalized['levels_confidence'] = building.get('levels_confidence', 'low')
        normalized['height_m'] = building.get('height_m')
        normalized['roof_levels'] = building.get('roof_levels')
        
        # === CONSTRUCTION ===
        normalized['construction_material'] = building.get('construction_material')
        normalized['construction_year'] = building.get('construction_year')
        normalized['roof_material'] = building.get('roof_material')
        normalized['building_subtype'] = building.get('building_subtype')
        normalized['building_use'] = building.get('building_use')
        
        # === MÉTADONNÉES OSM ===
        normalized['osm_type'] = building.get('osm_type', 'way')
        normalized['osm_timestamp'] = building.get('osm_timestamp')
        normalized['osm_version'] = building.get('osm_version')
        normalized['osm_changeset'] = building.get('osm_changeset')
        
        # === QUALITÉ ET VALIDATION ===
        normalized['validation_score'] = building.get('validation_score', 0.5)
        
        # === MÉTADONNÉES DE TRAITEMENT ===
        normalized['zone_name'] = zone_name
        normalized['source'] = 'osm_administrative_enhanced'
        
        # Conservation des métadonnées complètes
        if 'geometry_metadata' in building:
            normalized['geometry_metadata'] = building['geometry_metadata']
        
        if 'floors_metadata' in building:
            normalized['floors_metadata'] = building['floors_metadata']
        
        return normalized
    
    def _validate_enhanced_building_final(self, building: Dict) -> bool:
        """
        Validation finale d'un bâtiment amélioré
        
        Args:
            building: Bâtiment normalisé
            
        Returns:
            bool: True si valide pour utilisation
        """
        # Vérifications critiques
        if not building.get('unique_id'):
            return False
        
        # Coordonnées Malaysia
        lat = building.get('latitude', 0)
        lon = building.get('longitude', 0)
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
    
    def _calculate_enhanced_zone_statistics(self, buildings: List[Dict]) -> Dict:
        """
        Calcule les statistiques de zone améliorées avec géométrie
        
        Args:
            buildings: Liste des bâtiments enrichis
            
        Returns:
            Dict: Statistiques calculées améliorées
        """
        if not buildings:
            return {
                'total_buildings': 0,
                'building_types': {},
                'total_surface_m2': 0,
                'average_surface_m2': 0,
                'enhanced_features': {}
            }
        
        # Calculs efficaces
        type_counts = {}
        total_surface = 0
        total_polygon_surface = 0
        total_floors = 0
        
        # Compteurs enrichis
        with_precise_geometry = 0
        with_floors_data = 0
        with_construction_data = 0
        
        # Échantillonnage pour les gros volumes
        sample_size = min(1000, len(buildings))
        step = max(1, len(buildings) // sample_size)
        
        for i in range(0, len(buildings), step):
            building = buildings[i]
            building_type = building.get('building_type', 'unknown')
            type_counts[building_type] = type_counts.get(building_type, 0) + step
            
            # Surfaces
            surface = building.get('surface_area_m2', 0)
            polygon_surface = building.get('polygon_area_m2', 0)
            if surface > 0:
                total_surface += surface * step
            if polygon_surface > 0:
                total_polygon_surface += polygon_surface * step
            
            # Étages
            floors = building.get('floors_count', 1)
            total_floors += floors * step
            
            # Données enrichies
            if building.get('has_precise_geometry', False):
                with_precise_geometry += step
            
            if building.get('floors_count', 1) > 1:
                with_floors_data += step
            
            if building.get('construction_year') or building.get('construction_material'):
                with_construction_data += step
        
        return {
            'total_buildings': len(buildings),
            'building_types': type_counts,
            'total_surface_m2': total_surface,
            'total_polygon_surface_m2': total_polygon_surface,
            'average_surface_m2': total_surface / len(buildings) if buildings else 0,
            'average_polygon_surface_m2': total_polygon_surface / len(buildings) if buildings else 0,
            'total_floors': total_floors,
            'average_floors': total_floors / len(buildings) if buildings else 0,
            'most_common_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else 'unknown',
            'sample_based': sample_size < len(buildings),
            'enhanced_features': {
                'with_precise_geometry': with_precise_geometry,
                'with_floors_data': with_floors_data,
                'with_construction_data': with_construction_data,
                'geometry_rate': with_precise_geometry / len(buildings),
                'floors_rate': with_floors_data / len(buildings),
                'construction_rate': with_construction_data / len(buildings)
            }
        }
    
    def _assess_geometry_quality(self, buildings: List[Dict]) -> Dict:
        """
        Évalue la qualité géométrique des bâtiments
        
        Args:
            buildings: Liste des bâtiments
            
        Returns:
            Dict: Évaluation de qualité géométrique
        """
        if not buildings:
            return {'quality': 'unknown', 'with_precise_geometry': 0}
        
        # Compteurs
        with_precise_geometry = sum(1 for b in buildings if b.get('has_precise_geometry', False))
        with_floors_data = sum(1 for b in buildings if b.get('floors_count', 1) > 1)
        with_construction_data = sum(1 for b in buildings if b.get('construction_year') or b.get('construction_material'))
        
        # Score de qualité géométrique
        geometry_rate = with_precise_geometry / len(buildings)
        floors_rate = with_floors_data / len(buildings)
        construction_rate = with_construction_data / len(buildings)
        
        # Score global
        overall_score = (geometry_rate * 0.5 + floors_rate * 0.3 + construction_rate * 0.2)
        
        if overall_score > 0.8:
            quality = 'excellent'
        elif overall_score > 0.6:
            quality = 'good'
        elif overall_score > 0.4:
            quality = 'fair'
        else:
            quality = 'poor'
        
        # Validation scores
        validation_scores = [b.get('validation_score', 0) for b in buildings if b.get('validation_score') is not None]
        avg_validation = sum(validation_scores) / len(validation_scores) if validation_scores else 0
        
        return {
            'quality': quality,
            'overall_score': round(overall_score, 3),
            'with_precise_geometry': with_precise_geometry,
            'with_floors_data': with_floors_data,
            'with_construction_data': with_construction_data,
            'geometry_rate': round(geometry_rate, 3),
            'floors_rate': round(floors_rate, 3),
            'construction_rate': round(construction_rate, 3),
            'average_validation_score': round(avg_validation, 3),
            'buildings_analyzed': len(buildings)
        }
    
    def _should_show_map(self, zone_name: str, building_count: int) -> bool:
        """
        Détermine si la carte doit être affichée (toujours True avec échantillonnage)
        
        Args:
            zone_name: Nom de la zone
            building_count: Nombre de bâtiments
            
        Returns:
            bool: True (toujours recommandé avec échantillonnage intelligent)
        """
        return True
    
    def get_service_statistics(self) -> Dict:
        """Retourne les statistiques du service amélioré"""
        return {
            'total_loads': self.load_count,
            'service_status': 'active',
            'method': 'administrative_enhanced_osm',
            'capabilities': {
                'large_datasets': True,
                'robust_processing': True,
                'batch_processing': True,
                'error_recovery': True,
                'geometry_extraction': True,
                'floors_metadata': True,
                'construction_metadata': True,
                'enhanced_validation': True
            },
            'enhanced_features': {
                'precise_geometry_extraction': True,
                'polygon_area_calculation': True,
                'shape_complexity_analysis': True,
                'floors_data_extraction': True,
                'construction_metadata_extraction': True,
                'osm_metadata_preservation': True,
                'quality_scoring': True
            }
        }


# Alias pour compatibilité avec l'ancien nom
OSMService = EnhancedOSMService