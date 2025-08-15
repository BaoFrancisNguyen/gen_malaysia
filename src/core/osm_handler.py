#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GESTIONNAIRE OSM - CORE MODULE
==============================

Module core pour la gestion des données OpenStreetMap.
VERSION CORRIGÉE: Utilise les relations administratives au lieu des bbox.
"""

import logging
import time
from typing import Dict, List, Optional
import requests
from datetime import datetime

from config import OSMConfig
from src.utils.helpers import calculate_approximate_area, generate_building_id

logger = logging.getLogger(__name__)


class OSMHandler:
    """Gestionnaire des opérations OpenStreetMap avec relations administratives"""
    
    def __init__(self):
        """Initialise le gestionnaire OSM"""
        self.query_count = 0
        self.total_query_time = 0
        self.last_query_time = None
        logger.info("✅ OSMHandler initialisé (méthode relations administratives)")
    
    def fetch_buildings_from_relation(self, osm_relation_id: str, zone_name: str) -> Dict:
        """
        Récupère les bâtiments depuis une relation administrative OSM
        MÉTHODE ORIGINALE CORRECTE
        
        Args:
            osm_relation_id: ID de la relation administrative OSM
            zone_name: Nom de la zone (pour logs)
            
        Returns:
            Dict: Résultat avec bâtiments et métadonnées
        """
        start_time = time.time()
        self.query_count += 1
        
        try:
            logger.info(f"🌐 Requête OSM #{self.query_count}: relation {osm_relation_id} ({zone_name})")
            
            # Construction de la requête Overpass avec relation administrative
            query = self._build_relation_query(osm_relation_id)
            
            # Exécution de la requête
            raw_data = self._execute_overpass_query(query)
            
            if not raw_data:
                return {
                    'success': False,
                    'error': 'Aucune donnée retournée par Overpass API'
                }
            
            # Parsing des données
            buildings = self._parse_osm_buildings(raw_data, zone_name)
            
            # Métadonnées de la requête
            query_time = time.time() - start_time
            self.total_query_time += query_time
            self.last_query_time = datetime.now()
            
            logger.info(f"✅ OSM Query #{self.query_count}: {len(buildings)} bâtiments en {query_time:.1f}s")
            
            return {
                'success': True,
                'buildings': buildings,
                'metadata': {
                    'query_count': self.query_count,
                    'query_time_seconds': query_time,
                    'osm_relation_id': osm_relation_id,
                    'zone_name': zone_name,
                    'buildings_found': len(buildings),
                    'query_timestamp': self.last_query_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur requête OSM: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'query_count': self.query_count,
                    'query_time_seconds': time.time() - start_time
                }
            }
    
    def _build_relation_query(self, osm_relation_id: str) -> str:
        """
        Construit une requête Overpass pour une relation administrative
        APPROCHE ORIGINALE CORRECTE
        
        Args:
            osm_relation_id: ID de la relation OSM
            
        Returns:
            str: Requête Overpass QL
        """
        timeout = OSMConfig.OVERPASS_CONFIG['timeout']
        
        # Requête Overpass avec area() - MÉTHODE ORIGINALE
        query = f"""[out:json][timeout:{timeout}];
area(id:{3600000000 + int(osm_relation_id)})->.searchArea;
(
  way["building"](area.searchArea);
  relation["building"](area.searchArea);
);
out geom;"""
        
        return query
    
    def _execute_overpass_query(self, query: str) -> Optional[Dict]:
        """
        Exécute une requête Overpass API
        VERSION AMÉLIORÉE
        
        Args:
            query: Requête Overpass QL
            
        Returns:
            Optional[Dict]: Données JSON ou None si erreur
        """
        overpass_urls = [
            'https://overpass-api.de/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter'
        ]
        
        headers = {
            'User-Agent': OSMConfig.OVERPASS_CONFIG['user_agent'],
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        for url in overpass_urls:
            try:
                logger.debug(f"🌐 Tentative requête: {url}")
                
                response = requests.post(
                    url,
                    data=query.encode('utf-8'),
                    headers=headers,
                    timeout=OSMConfig.OVERPASS_CONFIG['timeout']
                )
                
                if response.status_code == 200:
                    # Vérifier le content-type
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        try:
                            data = response.json()
                            logger.debug(f"✅ Requête réussie: {len(data.get('elements', []))} éléments")
                            return data
                        except ValueError as e:
                            logger.warning(f"⚠️ Erreur JSON {url}: {e}")
                            continue
                    else:
                        logger.warning(f"⚠️ Réponse non-JSON de {url}: {content_type}")
                        logger.debug(f"📝 Contenu: {response.text[:300]}...")
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code}: {url}")
                    if response.status_code == 400:
                        logger.debug(f"📝 Erreur 400: {response.text[:300]}...")
                    
            except requests.RequestException as e:
                logger.warning(f"⚠️ Erreur requête {url}: {e}")
                continue
        
        logger.error("❌ Toutes les tentatives Overpass ont échoué")
        return None
    
    def _parse_osm_buildings(self, osm_data: Dict, zone_name: str) -> List[Dict]:
        """
        Parse les données OSM brutes en bâtiments
        
        Args:
            osm_data: Données JSON d'Overpass API
            zone_name: Nom de la zone
            
        Returns:
            List[Dict]: Liste des bâtiments parsés
        """
        buildings = []
        elements = osm_data.get('elements', [])
        
        logger.info(f"🏗️ Parsing {len(elements)} éléments OSM pour {zone_name}...")
        
        for element in elements:
            try:
                building = self._parse_single_building(element, zone_name)
                if building:
                    buildings.append(building)
                    
            except Exception as e:
                logger.debug(f"⚠️ Erreur parsing élément {element.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ {len(buildings)} bâtiments parsés avec succès pour {zone_name}")
        return buildings
    
    def _parse_single_building(self, element: Dict, zone_name: str) -> Optional[Dict]:
        """
        Parse un seul élément OSM en bâtiment
        
        Args:
            element: Élément OSM (way ou relation)
            zone_name: Nom de la zone
            
        Returns:
            Optional[Dict]: Bâtiment parsé ou None
        """
        # Extraction des métadonnées de base
        osm_id = element.get('id')
        tags = element.get('tags', {})
        
        # Vérification que c'est bien un bâtiment
        if not self._is_building(tags):
            return None
        
        # Extraction de la géométrie
        geometry_result = self._extract_geometry(element)
        if not geometry_result:
            return None
        
        center_lat, center_lon, surface_area = geometry_result
        
        # Validation coordonnées Malaysia
        if not self._is_in_malaysia(center_lat, center_lon):
            return None
        
        # Détermination du type de bâtiment
        building_type = self._determine_building_type(tags)
        
        # Génération ID unique
        building_id = generate_building_id(building_type, zone_name)
        
        # Construction de l'objet bâtiment
        building = {
            'id': building_id,
            'osm_id': str(osm_id),
            'building_type': building_type,
            'latitude': round(center_lat, 6),
            'longitude': round(center_lon, 6),
            'surface_area_m2': round(surface_area, 1),
            'zone_name': zone_name,
            'osm_tags': tags,
            'source': 'openstreetmap',
            'extracted_at': datetime.now().isoformat()
        }
        
        return building
    
    def _is_building(self, tags: Dict) -> bool:
        """Vérifie si l'élément est un bâtiment"""
        # Présence du tag building
        if 'building' in tags and tags['building'] not in ['no', 'false']:
            return True
        
        # Ou certains landuse/amenity
        landuse = tags.get('landuse', '')
        amenity = tags.get('amenity', '')
        
        building_landuses = ['residential', 'commercial', 'industrial', 'retail']
        building_amenities = ['school', 'hospital', 'clinic', 'university']
        
        return landuse in building_landuses or amenity in building_amenities
    
    def _extract_geometry(self, element: Dict) -> Optional[tuple]:
        """
        Extrait la géométrie (centre et surface) d'un élément OSM
        
        Args:
            element: Élément OSM
            
        Returns:
            Optional[tuple]: (lat, lon, surface_m2) ou None
        """
        geometry = element.get('geometry', [])
        
        if not geometry:
            # Fallback pour les éléments sans géométrie détaillée
            if element.get('lat') and element.get('lon'):
                return element['lat'], element['lon'], 100.0
            return None
        
        # Extraction des coordonnées
        coordinates = []
        for node in geometry:
            lat = node.get('lat')
            lon = node.get('lon')
            if lat is not None and lon is not None:
                coordinates.append((lat, lon))
        
        if len(coordinates) < 1:
            return None
        
        # Calcul du centre géométrique
        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
        
        # Calcul de la surface approximative
        if len(coordinates) >= 3:
            surface_area = calculate_approximate_area(coordinates)
        else:
            surface_area = 100.0  # Surface par défaut pour points isolés
        
        return center_lat, center_lon, surface_area
    
    def _is_in_malaysia(self, lat: float, lon: float) -> bool:
        """Vérifie si les coordonnées sont en Malaysia"""
        from config import MalaysiaConfig
        bounds = MalaysiaConfig.BOUNDS
        
        return (bounds['south'] <= lat <= bounds['north'] and 
                bounds['west'] <= lon <= bounds['east'])
    
    def _determine_building_type(self, tags: Dict) -> str:
        """
        Détermine le type de bâtiment depuis les tags OSM
        
        Args:
            tags: Tags OSM
            
        Returns:
            str: Type de bâtiment normalisé
        """
        building_tag = tags.get('building', '').lower()
        amenity_tag = tags.get('amenity', '').lower()
        landuse_tag = tags.get('landuse', '').lower()
        
        # Mapping tags → types
        type_mappings = {
            'residential': ['house', 'residential', 'apartments', 'apartment', 'flat', 'terrace'],
            'commercial': ['commercial', 'retail', 'shop', 'mall', 'store', 'supermarket'],
            'office': ['office', 'government', 'civic', 'public'],
            'industrial': ['industrial', 'warehouse', 'factory', 'manufacturing'],
            'school': ['school', 'university', 'college', 'kindergarten', 'education'],
            'hospital': ['hospital', 'clinic', 'healthcare', 'medical']
        }
        
        # Recherche dans tous les tags
        all_tag_values = f"{building_tag} {amenity_tag} {landuse_tag}".lower()
        
        for building_type, keywords in type_mappings.items():
            if any(keyword in all_tag_values for keyword in keywords):
                return building_type
        
        # Type par défaut
        return 'residential'
    
    def get_statistics(self) -> Dict:
        """
        Retourne les statistiques du gestionnaire
        
        Returns:
            Dict: Statistiques d'utilisation
        """
        avg_query_time = (self.total_query_time / self.query_count 
                         if self.query_count > 0 else 0)
        
        return {
            'total_queries': self.query_count,
            'total_query_time_seconds': round(self.total_query_time, 1),
            'average_query_time_seconds': round(avg_query_time, 1),
            'last_query_time': self.last_query_time.isoformat() if self.last_query_time else None,
            'method': 'administrative_relations',
            'overpass_endpoints': ['overpass-api.de', 'overpass.kumi.systems']
        }