#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSM HANDLER AVEC LA MÉTHODE ADMINISTRATIVE
===================================================


"""

import requests
import json
import time
import logging
import math
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OSMHandler:
    """
    Gestionnaire OSM la méthode administrative
    """
    
    def __init__(self):
        """Initialise le gestionnaire OSM"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Malaysia-Building-Generator-Administrative/2.0'
        })
        
        # APIs Overpass
        self.overpass_apis = [
            'https://overpass-api.de/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter',
            'https://lz4.overpass-api.de/api/interpreter'
        ]
        
        logger.info("✅ OSMHandler initialisé - Méthode administrative SEULEMENT")
    
    def fetch_buildings_administrative(self, zone_name: str) -> Dict:
        """
        MÉTHODE ADMINISTRATIVE: Utilise les relations OSM officielles
        
        Args:
            zone_name: Nom de la zone (ex: 'penang', 'kuala_lumpur')
            
        Returns:
            Dict: Résultat avec bâtiments et métadonnées
        """
        start_time = time.time()
        
        logger.info(f"🎯 Méthode administrative pour: {zone_name}")
        
        # Relations administratives OSM validées (CORRIGÉES)
        administrative_relations = {
            # PAYS
            'malaysia': 2108121,          
            
            # TERRITOIRES FÉDÉRAUX 
            'kuala_lumpur': 2939672,       
            'putrajaya': 4443881,          
            'labuan': 4521286,             
            
            # ÉTATS 
            'selangor': 2932285,           
            'johor': 2939653,              
            'penang': 4445131,            
            'perak': 4445076,              
            'sabah': 3879783,              
            'sarawak': 3879784,            
            'kedah': 4444908,              
            'kelantan': 4443571,           
            'terengganu': 4444411,         
            'pahang': 4444595,             
            'perlis': 4444918,             
            'negeri_sembilan': 2939674,    
            'melaka': 2939673,             
        }
        
        relation_id = administrative_relations.get(zone_name.lower())
        
        if not relation_id:
            logger.error(f"❌ Pas de relation administrative OSM pour {zone_name}")
            logger.info(f"📋 Relations disponibles: {list(administrative_relations.keys())}")
            return {
                'success': False,
                'error': f"Relation administrative non disponible pour {zone_name}",
                'buildings': [],
                'available_zones': list(administrative_relations.keys())
            }
        
        logger.info(f"🎯 Utilisation relation OSM administrative: {relation_id}")
        
        # REQUÊTE OVERPASS
        query = f"""[out:json][timeout:300];
relation({relation_id});
map_to_area->.admin_area;
way["building"](area.admin_area);
out geom;"""
        
        logger.info(f"📝 Requête administrative: relation({relation_id}) → area → buildings")
        
        try:
            osm_data = self._execute_query(query.strip())
            elements = osm_data.get('elements', [])
            
            logger.info(f"📋 Éléments OSM reçus (administrative): {len(elements):,}")
            
            if len(elements) == 0:
                logger.warning("⚠️ Relation administrative trouvée mais aucun bâtiment")
                return {
                    'success': False,
                    'error': "Relation administrative valide mais sans bâtiments",
                    'buildings': [],
                    'relation_id': relation_id
                }
            
            buildings = self._process_buildings_data(elements, zone_name)
            
            logger.info(f"🏗️ Bâtiments traités (administrative): {len(buildings):,}")
            
            return {
                'success': True,
                'buildings': buildings,
                'total_elements': len(elements),
                'query_time_seconds': time.time() - start_time,
                'method_used': 'administrative',
                'relation_id': relation_id,
                'metadata': {
                    'zone_name': zone_name,
                    'method': 'administrative',
                    'relation_id': relation_id,
                    'query_time_seconds': time.time() - start_time
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur méthode administrative: {e}")
            return {
                'success': False,
                'error': f"Erreur administrative: {str(e)}",
                'buildings': [],
                'relation_id': relation_id
            }
    
    def _execute_query(self, query: str, max_retries: int = 3) -> Dict:
        """
        Exécute une requête Overpass avec retry
        
        Args:
            query: Requête Overpass
            max_retries: Nombre maximum de tentatives
            
        Returns:
            Dict: Données OSM
        """
        last_error = None
        
        for api_url in self.overpass_apis:
            for attempt in range(max_retries):
                try:
                    logger.info(f"🌐 Tentative {attempt + 1}/{max_retries} sur {api_url}")
                    
                    response = self.session.post(
                        api_url,
                        data=query,
                        timeout=300,
                        headers={'Content-Type': 'text/plain; charset=utf-8'}
                    )
                    
                    logger.info(f"📡 Statut HTTP: {response.status_code}")
                    logger.info(f"📊 Taille réponse: {len(response.content)} bytes")
                    
                    if response.status_code == 200:
                        result = response.json()
                        elements_count = len(result.get('elements', []))
                        logger.info(f"✅ Succès: {elements_count} éléments reçus")
                        return result
                    else:
                        logger.warning(f"⚠️ HTTP {response.status_code}: {response.text[:200]}")
                        last_error = f"HTTP {response.status_code}"
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Timeout sur {api_url}")
                    last_error = "Timeout"
                    
                except requests.exceptions.RequestException as e:
                    logger.warning(f"🌐 Erreur réseau sur {api_url}: {e}")
                    last_error = f"Erreur réseau: {e}"
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"📝 JSON invalide de {api_url}: {e}")
                    last_error = f"JSON invalide: {e}"
                    
                except Exception as e:
                    logger.warning(f"❌ Erreur inattendue sur {api_url}: {e}")
                    last_error = f"Erreur inattendue: {e}"
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponentiel
        
        raise Exception(f"Toutes les APIs Overpass ont échoué. Dernière erreur: {last_error}")
    
    def _process_buildings_data(self, elements: List[Dict], zone_name: str) -> List[Dict]:
        """
        Traite les éléments OSM et les convertit en bâtiments
        
        Args:
            elements: Éléments OSM bruts
            zone_name: Nom de la zone
            
        Returns:
            List[Dict]: Liste des bâtiments traités
        """
        buildings = []
        processed_count = 0
        skipped_count = 0
        
        logger.info(f"🔄 Traitement de {len(elements):,} éléments OSM")
        
        for element in elements:
            processed_count += 1
            
            # Affichage du progrès pour grandes collections
            if processed_count % 10000 == 0:
                logger.info(f"🔄 Progrès: {processed_count:,}/{len(elements):,} éléments traités")
            
            try:
                # Vérifier le type d'élément
                if element.get('type') != 'way':
                    skipped_count += 1
                    continue
                
                tags = element.get('tags', {})
                building_tag = tags.get('building')
                
                # Vérifier que c'est bien un bâtiment
                if not building_tag or building_tag in ['no', 'false']:
                    skipped_count += 1
                    continue
                
                # Vérifier la géométrie
                geometry = element.get('geometry', [])
                if len(geometry) < 3:  # Besoin d'au moins 3 points pour un polygone
                    skipped_count += 1
                    continue
                
                # Calculer le centre géométrique
                lats = [coord['lat'] for coord in geometry if 'lat' in coord]
                lons = [coord['lon'] for coord in geometry if 'lon' in coord]
                
                if not lats or not lons or len(lats) < 3:
                    skipped_count += 1
                    continue
                
                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)
                
                # Vérifier que les coordonnées sont dans Malaysia
                if not (0.5 <= center_lat <= 7.5 and 99.0 <= center_lon <= 120.0):
                    skipped_count += 1
                    continue
                
                # Calculer la surface approximative
                surface_area = self._calculate_building_area(lats, lons)
                
                # Déterminer le type de bâtiment
                building_type = self._determine_building_type(building_tag, tags)
                
                # Créer l'objet bâtiment
                building = {
                    'building_id': f"osm_{element.get('id', processed_count)}",
                    'osm_id': element.get('id'),
                    'latitude': center_lat,
                    'longitude': center_lon,
                    'building_type': building_type,
                    'surface_area_m2': surface_area,
                    'zone_name': zone_name,
                    'source': 'osm_administrative',
                    'geometry': geometry,
                    'tags': tags
                }
                
                buildings.append(building)
                
            except Exception as e:
                logger.debug(f"Erreur traitement élément {processed_count}: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"✅ Traitement terminé: {len(buildings)} bâtiments, {skipped_count} ignorés")
        
        return buildings
    
    def _calculate_building_area(self, lats: List[float], lons: List[float]) -> float:
        """
        Calcule la surface approximative d'un bâtiment
        
        Args:
            lats: Latitudes des points
            lons: Longitudes des points
            
        Returns:
            float: Surface en m²
        """
        if len(lats) < 3:
            return 50.0  # Surface par défaut
        
        try:
            # Algorithme de Shoelace pour calculer l'aire d'un polygone
            area = 0.0
            n = len(lats)
            
            for i in range(n):
                j = (i + 1) % n
                area += lats[i] * lons[j]
                area -= lats[j] * lons[i]
            
            area = abs(area) / 2.0
            
            # Conversion approximative en m² (1 degré ≈ 111km en Malaysia)
            area_m2 = area * (111000 ** 2)
            
            # Limites réalistes pour les bâtiments
            if area_m2 < 10:
                return 50.0
            elif area_m2 > 50000:
                return 50000.0
            else:
                return area_m2
                
        except:
            return 100.0  # Surface par défaut en cas d'erreur
    
    def _determine_building_type(self, building_tag: str, tags: Dict) -> str:
        """
        Détermine le type de bâtiment à partir des tags OSM
        
        Args:
            building_tag: Tag building principal
            tags: Tous les tags OSM
            
        Returns:
            str: Type de bâtiment normalisé
        """
        # Types spécifiques
        if building_tag in ['house', 'detached', 'terrace', 'apartments', 'residential']:
            return 'residential'
        elif building_tag in ['office', 'commercial', 'retail', 'shop']:
            return 'commercial'
        elif building_tag in ['industrial', 'warehouse', 'factory']:
            return 'industrial'
        elif building_tag in ['school', 'university', 'college']:
            return 'school'
        elif building_tag in ['hospital', 'clinic']:
            return 'hospital'
        elif building_tag in ['hotel', 'accommodation']:
            return 'hotel'
        elif building_tag == 'yes':
            # Analyser les autres tags
            if tags.get('amenity') in ['school', 'university']:
                return 'school'
            elif tags.get('amenity') in ['hospital', 'clinic']:
                return 'hospital'
            elif tags.get('amenity') in ['restaurant', 'cafe', 'shop']:
                return 'commercial'
            elif tags.get('landuse') == 'residential':
                return 'residential'
            elif tags.get('landuse') == 'industrial':
                return 'industrial'
            else:
                return 'residential'  # Par défaut
        else:
            return 'residential'  # Par défaut
        
    def fetch_buildings_from_relation(self, zone_name: str) -> Dict:
        """
        🥇 MÉTHODE ADMINISTRATIVE: Utilise les relations OSM officielles
        
        À ajouter dans la classe OSMHandler existante de gen_malaysia
        """
        import time
        start_time = time.time()
        
        logger.info(f"🎯 Méthode administrative pour: {zone_name}")
        
        # Relations administratives OSM validées (CORRIGÉES)
        administrative_relations = {
            # PAYS
            'malaysia': 2108121,          
            
            # TERRITOIRES FÉDÉRAUX 
            'kuala_lumpur': 2939672,       
            'putrajaya': 4443881,          
            'labuan': 4521286,             
            
            # ÉTATS 
            'selangor': 2932285,           
            'johor': 2939653,              
            'penang': 4445131,             
            'perak': 4445076,              
            'sabah': 3879783,              
            'sarawak': 3879784,            
            'kedah': 4444908,              
            'kelantan': 4443571,           
            'terengganu': 4444411,         
            'pahang': 4444595,             
            'perlis': 4444918,             
            'negeri_sembilan': 2939674,    
            'melaka': 2939673,             
        }
        
        relation_id = administrative_relations.get(zone_name.lower())
        
        if not relation_id:
            logger.error(f"❌ Pas de relation administrative OSM pour {zone_name}")
            logger.info(f"📋 Relations disponibles: {list(administrative_relations.keys())}")
            return {
                'success': False,
                'error': f"Relation administrative non disponible pour {zone_name}",
                'buildings': [],
                'available_zones': list(administrative_relations.keys())
            }
        
        logger.info(f"🎯 Utilisation relation OSM administrative: {relation_id}")
        
        # REQUÊTE OVERPASS CORRIGÉE (syntaxe simplifiée qui FONCTIONNE)
        query = f"""[out:json][timeout:300];
    relation({relation_id});
    map_to_area->.admin_area;
    way["building"](area.admin_area);
    out geom;"""
        
        logger.info(f"📝 Requête administrative: relation({relation_id}) → area → buildings")
        
        try:
            # Utiliser la méthode _execute_query existante si elle existe
            # Sinon utiliser requests directement
            if hasattr(self, '_execute_query'):
                osm_data = self._execute_query(query.strip())
            else:
                osm_data = self._execute_overpass_query_simple(query.strip())
            
            elements = osm_data.get('elements', [])
            
            logger.info(f"📋 Éléments OSM reçus (administrative): {len(elements):,}")
            
            if len(elements) == 0:
                logger.warning("⚠️ Relation administrative trouvée mais aucun bâtiment")
                return {
                    'success': False,
                    'error': "Relation administrative valide mais sans bâtiments",
                    'buildings': [],
                    'relation_id': relation_id
                }
            
            # Utiliser la méthode de traitement existante si elle existe
            if hasattr(self, '_process_buildings_data'):
                buildings = self._process_buildings_data(elements, zone_name)
            else:
                buildings = self._process_elements_simple(elements, zone_name)
            
            logger.info(f"🏗️ Bâtiments traités (administrative): {len(buildings):,}")
            
            return {
                'success': True,
                'buildings': buildings,
                'total_elements': len(elements),
                'query_time_seconds': time.time() - start_time,
                'method_used': 'administrative',
                'relation_id': relation_id,
                'metadata': {
                    'zone_name': zone_name,
                    'method': 'administrative',
                    'relation_id': relation_id,
                    'query_time_seconds': time.time() - start_time
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur méthode administrative: {e}")
            return {
                'success': False,
                'error': f"Erreur administrative: {str(e)}",
                'buildings': [],
                'relation_id': relation_id
            }

    def _execute_overpass_query_simple(self, query: str) -> Dict:
        """
        Méthode simple d'exécution Overpass si _execute_query n'existe pas
        """
        overpass_apis = [
            'https://overpass-api.de/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter'
        ]
        
        for api_url in overpass_apis:
            try:
                response = self.session.post(
                    api_url,
                    data=query,
                    timeout=300,
                    headers={'Content-Type': 'text/plain; charset=utf-8'}
                )
                
                if response.status_code == 200:
                    return response.json()
                    
            except Exception as e:
                logger.warning(f"Erreur API {api_url}: {e}")
                continue
        
        raise Exception("Toutes les APIs Overpass ont échoué")

    def _process_elements_simple(self, elements: List[Dict], zone_name: str) -> List[Dict]:
        """
        Traitement simple des éléments OSM si _process_buildings_data n'existe pas
        """
        buildings = []
        
        for i, element in enumerate(elements):
            try:
                if element.get('type') != 'way':
                    continue
                    
                tags = element.get('tags', {})
                building_tag = tags.get('building')
                
                if not building_tag or building_tag in ['no', 'false']:
                    continue
                    
                geometry = element.get('geometry', [])
                if len(geometry) < 3:
                    continue
                    
                # Centre géométrique
                lats = [coord['lat'] for coord in geometry if 'lat' in coord]
                lons = [coord['lon'] for coord in geometry if 'lon' in coord]
                
                if not lats or not lons:
                    continue
                    
                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)
                
                # Vérifier Malaysia
                if not (0.5 <= center_lat <= 7.5 and 99.0 <= center_lon <= 120.0):
                    continue
                
                # Surface approximative
                surface_area = max(50, min(1000, len(geometry) * 20))
                
                # Type de bâtiment
                if building_tag in ['house', 'residential', 'apartments']:
                    building_type = 'residential'
                elif building_tag in ['commercial', 'retail', 'shop']:
                    building_type = 'commercial'
                elif building_tag in ['office']:
                    building_type = 'office'
                elif building_tag in ['industrial', 'warehouse']:
                    building_type = 'industrial'
                else:
                    building_type = 'residential'
                
                building = {
                    'building_id': f"osm_{element.get('id', i)}",
                    'osm_id': element.get('id'),
                    'latitude': center_lat,
                    'longitude': center_lon,
                    'building_type': building_type,
                    'surface_area_m2': surface_area,
                    'zone_name': zone_name,
                    'source': 'osm_administrative',
                    'tags': tags
                }
                
                buildings.append(building)
                
            except Exception as e:
                continue
        
        return buildings