#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSM HANDLER AMÉLIORÉ AVEC EXTRACTION GÉOMÉTRIQUE PRÉCISE
=======================================================

Version améliorée qui extrait les polygones complets et les métadonnées d'étages
pour les générateurs electricity_generator.py et water_generator.py
"""

import requests
import json
import time
import logging
import math
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EnhancedOSMHandler:
    """
    Gestionnaire OSM amélioré avec extraction géométrique précise
    """
    
    def __init__(self):
        """Initialise le gestionnaire OSM amélioré"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Malaysia-Enhanced-Building-Generator/3.0'
        })
        
        # APIs Overpass
        self.overpass_apis = [
            'https://overpass-api.de/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter',
            'https://lz4.overpass-api.de/api/interpreter'
        ]
        
        # Cache pour les relations administratives
        self.administrative_relations = {
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
            
            # VILLES PRINCIPALES
            'shah_alam': 1876116,
            'petaling_jaya': 1876117,
            'subang_jaya': 1876118,
            'klang': 1876119,
            'johor_bahru': 1876100,
            'iskandar_puteri': 1876101,
            'george_town': 4445132,
            'butterworth': 4445133,
            'ipoh': 4445077,
            'taiping': 4445078,
            'alor_setar': 4444909,
            'kota_bharu': 4443572,
            'kuala_terengganu': 4444412,
            'kuantan': 4444596,
            'kangar': 4444919,
            'seremban': 2939675,
            'malacca_city': 2939680,
            'kota_kinabalu': 3879785,
            'kuching': 3879786,
            'sandakan': 3879787,
            'tawau': 3879788,
            'miri': 3879790,
            'sibu': 3879791,
            'bintulu': 3879792
        }
        
        logger.info("✅ EnhancedOSMHandler initialisé - Extraction géométrique complète")
    
    def fetch_buildings_administrative(self, zone_name: str) -> Dict:
        """
        MÉTHODE ADMINISTRATIVE AMÉLIORÉE: Extrait polygones complets et métadonnées étages
        
        Args:
            zone_name: Nom de la zone (ex: 'penang', 'kuala_lumpur')
            
        Returns:
            Dict: Résultat avec bâtiments enrichis (géométrie + étages)
        """
        start_time = time.time()
        
        logger.info(f"🏗️ Méthode administrative améliorée pour: {zone_name}")
        
        relation_id = self.administrative_relations.get(zone_name.lower())
        
        if not relation_id:
            logger.error(f"❌ Pas de relation administrative OSM pour {zone_name}")
            return {
                'success': False,
                'error': f"Relation administrative non disponible pour {zone_name}",
                'buildings': [],
                'available_zones': list(self.administrative_relations.keys())
            }
        
        logger.info(f"🎯 Utilisation relation OSM: {relation_id}")
        
        # REQUÊTE OVERPASS AMÉLIORÉE avec plus de tags
        query = self._build_enhanced_overpass_query(relation_id)
        
        try:
            osm_data = self._execute_query(query.strip())
            elements = osm_data.get('elements', [])
            
            logger.info(f"📋 Éléments OSM reçus: {len(elements):,}")
            
            if len(elements) == 0:
                logger.warning("⚠️ Relation administrative trouvée mais aucun bâtiment")
                return {
                    'success': False,
                    'error': "Relation administrative valide mais sans bâtiments",
                    'buildings': [],
                    'relation_id': relation_id
                }
            
            # Traitement amélioré avec extraction géométrique complète
            buildings = self._process_enhanced_buildings_data(elements, zone_name)
            
            # Statistiques de traitement
            processing_stats = self._calculate_processing_statistics(buildings, elements)
            
            logger.info(f"🏗️ Bâtiments traités (amélioré): {len(buildings):,}")
            logger.info(f"📐 Avec géométrie précise: {processing_stats['with_geometry_count']}")
            logger.info(f"🏢 Avec données d'étages: {processing_stats['with_floors_count']}")
            
            return {
                'success': True,
                'buildings': buildings,
                'total_elements': len(elements),
                'query_time_seconds': time.time() - start_time,
                'method_used': 'administrative_enhanced',
                'relation_id': relation_id,
                'processing_statistics': processing_stats,
                'metadata': {
                    'zone_name': zone_name,
                    'method': 'administrative_enhanced',
                    'relation_id': relation_id,
                    'query_time_seconds': time.time() - start_time,
                    'geometry_extraction': True,
                    'floors_extraction': True
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur méthode administrative améliorée: {e}")
            return {
                'success': False,
                'error': f"Erreur administrative: {str(e)}",
                'buildings': [],
                'relation_id': relation_id
            }
    
    def _build_enhanced_overpass_query(self, relation_id: int) -> str:
        """
        Construit une requête Overpass améliorée pour extraire plus de métadonnées
        
        Args:
            relation_id: ID de la relation OSM
            
        Returns:
            str: Requête Overpass optimisée
        """
        query = f"""[out:json][timeout:300];
relation({relation_id});
map_to_area->.admin_area;
(
  way["building"](area.admin_area);
  relation["building"](area.admin_area);
);
out geom tags;"""
        
        return query
    
    def _execute_query(self, query: str, max_retries: int = 3) -> Dict:
        """
        Exécute une requête Overpass avec retry amélioré
        
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
                    logger.info(f"📊 Taille réponse: {len(response.content):,} bytes")
                    
                    if response.status_code == 200:
                        result = response.json()
                        elements_count = len(result.get('elements', []))
                        logger.info(f"✅ Succès: {elements_count:,} éléments reçus")
                        return result
                    else:
                        logger.warning(f"⚠️ HTTP {response.status_code}: {response.text[:200]}")
                        last_error = f"HTTP {response.status_code}"
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"⏱️ Timeout sur {api_url}")
                    last_error = "Timeout"
                    
                except requests.exceptions.RequestException as e:
                    logger.warning(f"🌐 Erreur réseau sur {api_url}: {e}")
                    last_error = f"Erreur réseau: {e}"
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"📄 JSON invalide de {api_url}: {e}")
                    last_error = f"JSON invalide: {e}"
                    
                except Exception as e:
                    logger.warning(f"❌ Erreur inattendue sur {api_url}: {e}")
                    last_error = f"Erreur inattendue: {e}"
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponentiel
        
        raise Exception(f"Toutes les APIs Overpass ont échoué. Dernière erreur: {last_error}")
    
    def _process_enhanced_buildings_data(self, elements: List[Dict], zone_name: str) -> List[Dict]:
        """
        Traite les éléments OSM avec extraction géométrique complète et métadonnées étages
        
        Args:
            elements: Éléments OSM bruts
            zone_name: Nom de la zone
            
        Returns:
            List[Dict]: Liste des bâtiments enrichis
        """
        buildings = []
        processed_count = 0
        skipped_count = 0
        
        logger.info(f"🔄 Traitement amélioré de {len(elements):,} éléments OSM")
        
        for element in elements:
            processed_count += 1
            
            # Affichage du progrès pour grandes collections
            if processed_count % 5000 == 0:
                logger.info(f"🔄 Progrès: {processed_count:,}/{len(elements):,} éléments traités")
            
            try:
                # Vérifier le type d'élément (way ou relation)
                element_type = element.get('type')
                if element_type not in ['way', 'relation']:
                    skipped_count += 1
                    continue
                
                tags = element.get('tags', {})
                building_tag = tags.get('building')
                
                # Vérifier que c'est bien un bâtiment
                if not building_tag or building_tag in ['no', 'false']:
                    skipped_count += 1
                    continue
                
                # Extraction de la géométrie améliorée
                geometry_data = self._extract_enhanced_geometry(element)
                
                if not geometry_data['valid']:
                    skipped_count += 1
                    continue
                
                # Extraction métadonnées d'étages améliorée
                floors_data = self._extract_enhanced_floors_metadata(tags)
                
                # Déterminer le type de bâtiment amélioré
                building_type = self._determine_enhanced_building_type(building_tag, tags)
                
                # Calcul surface précise du polygone
                precise_surface = self._calculate_precise_polygon_area(geometry_data['coordinates'])
                
                # Création de l'objet bâtiment enrichi
                building = {
                    'unique_id': f"osm_enhanced_{element.get('id', processed_count)}",
                    'osm_id': element.get('id'),
                    'latitude': geometry_data['centroid_lat'],
                    'longitude': geometry_data['centroid_lon'],
                    'building_type': building_type,
                    'surface_area_m2': precise_surface,  # Surface calculée du polygone
                    'floors_count': floors_data['floors_count'],
                    'zone_name': zone_name,
                    'source': 'osm_administrative_enhanced',
                    
                    # GÉOMÉTRIE COMPLÈTE
                    'geometry': geometry_data['geometry_points'],
                    'geometry_type': element_type,
                    'has_precise_geometry': True,
                    'polygon_area_m2': precise_surface,
                    'polygon_perimeter_m': geometry_data.get('perimeter_m', 0),
                    'shape_complexity': geometry_data.get('shape_complexity', 1.0),
                    
                    # MÉTADONNÉES D'ÉTAGES COMPLÈTES
                    'building_levels': floors_data['floors_count'],
                    'levels_source': floors_data['source'],
                    'levels_confidence': floors_data['confidence'],
                    'height_m': floors_data.get('height_m'),
                    'roof_levels': floors_data.get('roof_levels'),
                    
                    # MÉTADONNÉES OSM COMPLÈTES
                    'tags': tags,
                    'osm_type': element_type,
                    'osm_timestamp': element.get('timestamp'),
                    'osm_version': element.get('version'),
                    'osm_changeset': element.get('changeset'),
                    
                    # DONNÉES DÉRIVÉES
                    'building_subtype': self._extract_building_subtype(tags),
                    'construction_material': self._extract_construction_material(tags),
                    'construction_year': self._extract_construction_year(tags),
                    'roof_material': self._extract_roof_material(tags),
                    'building_use': self._extract_building_use(tags),
                    
                    # VALIDATION
                    'validation_score': self._calculate_building_validation_score(
                        geometry_data, floors_data, tags
                    )
                }
                
                buildings.append(building)
                
            except Exception as e:
                logger.debug(f"Erreur traitement élément {processed_count}: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"✅ Traitement amélioré terminé: {len(buildings)} bâtiments, {skipped_count} ignorés")
        
        return buildings
    
    def _extract_enhanced_geometry(self, element: Dict) -> Dict:
        """
        Extrait la géométrie complète d'un élément OSM
        
        Args:
            element: Élément OSM
            
        Returns:
            Dict: Données géométriques complètes
        """
        try:
            geometry = element.get('geometry', [])
            
            if not geometry or len(geometry) < 3:
                return {'valid': False, 'error': 'Géométrie insuffisante'}
            
            # Extraction des coordonnées
            coordinates = []
            lats = []
            lons = []
            
            for point in geometry:
                if isinstance(point, dict) and 'lat' in point and 'lon' in point:
                    lat = float(point['lat'])
                    lon = float(point['lon'])
                    
                    # Validation coordonnées Malaysia
                    if 0.5 <= lat <= 7.5 and 99.0 <= lon <= 120.0:
                        coordinates.append({'lat': lat, 'lon': lon})
                        lats.append(lat)
                        lons.append(lon)
            
            if len(coordinates) < 3:
                return {'valid': False, 'error': 'Moins de 3 points valides'}
            
            # Calcul du centroïde
            centroid_lat = sum(lats) / len(lats)
            centroid_lon = sum(lons) / len(lons)
            
            # Calcul du périmètre approximatif
            perimeter_m = self._calculate_polygon_perimeter(coordinates)
            
            # Calcul de la complexité de forme
            shape_complexity = self._calculate_shape_complexity(coordinates)
            
            return {
                'valid': True,
                'geometry_points': coordinates,
                'coordinates': [(lat, lon) for lat, lon in zip(lats, lons)],
                'centroid_lat': centroid_lat,
                'centroid_lon': centroid_lon,
                'points_count': len(coordinates),
                'perimeter_m': perimeter_m,
                'shape_complexity': shape_complexity
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _extract_enhanced_floors_metadata(self, tags: Dict) -> Dict:
        """
        Extrait les métadonnées d'étages complètes
        
        Args:
            tags: Tags OSM
            
        Returns:
            Dict: Métadonnées d'étages enrichies
        """
        floors_data = {
            'floors_count': 1,
            'source': 'estimated',
            'confidence': 'low',
            'height_m': None,
            'roof_levels': None
        }
        
        # Sources possibles pour les étages
        floors_sources = [
            ('building:levels', 'high'),
            ('levels', 'high'),
            ('building:floors', 'medium'),
            ('floors', 'medium'),
            ('height', 'medium'),  # Sera converti
            ('building:height', 'medium')
        ]
        
        for tag_name, confidence in floors_sources:
            tag_value = tags.get(tag_name)
            if tag_value:
                try:
                    if 'height' in tag_name:
                        # Conversion hauteur en étages (3.5m par étage en moyenne)
                        height_str = str(tag_value).replace('m', '').strip()
                        height_m = float(height_str)
                        floors_data['height_m'] = height_m
                        estimated_floors = max(1, round(height_m / 3.5))
                        floors_data['floors_count'] = estimated_floors
                        floors_data['source'] = f'{tag_name}_converted'
                        floors_data['confidence'] = 'medium'
                    else:
                        # Valeur directe d'étages
                        floors = int(float(tag_value))
                        if 1 <= floors <= 200:
                            floors_data['floors_count'] = floors
                            floors_data['source'] = tag_name
                            floors_data['confidence'] = confidence
                            break  # Priorité à la première source de qualité
                except (ValueError, TypeError):
                    continue
        
        # Étages de toit
        roof_levels = tags.get('roof:levels')
        if roof_levels:
            try:
                floors_data['roof_levels'] = int(float(roof_levels))
            except (ValueError, TypeError):
                pass
        
        return floors_data
    
    def _determine_enhanced_building_type(self, building_tag: str, tags: Dict) -> str:
        """
        Détermine le type de bâtiment de manière améliorée
        
        Args:
            building_tag: Tag building principal
            tags: Tous les tags OSM
            
        Returns:
            str: Type de bâtiment normalisé
        """
        # Mapping détaillé par tag building
        building_type_mapping = {
            # Résidentiel
            'house': 'residential',
            'detached': 'residential', 
            'semi_detached': 'residential',
            'terrace': 'residential',
            'apartments': 'residential',
            'residential': 'residential',
            'dormitory': 'residential',
            'bungalow': 'residential',
            
            # Commercial
            'retail': 'commercial',
            'shop': 'commercial',
            'commercial': 'commercial',
            'supermarket': 'commercial',
            'mall': 'commercial',
            'kiosk': 'commercial',
            
            # Bureau
            'office': 'office',
            'government': 'office',
            'civic': 'office',
            
            # Industriel
            'industrial': 'industrial',
            'warehouse': 'industrial',
            'factory': 'industrial',
            'manufacture': 'industrial',
            
            # Éducation
            'school': 'school',
            'university': 'school',
            'college': 'school',
            'kindergarten': 'school',
            
            # Santé
            'hospital': 'hospital',
            'clinic': 'hospital',
            'healthcare': 'hospital',
            
            # Autres
            'hotel': 'commercial',
            'restaurant': 'commercial',
            'church': 'office',
            'mosque': 'office',
            'temple': 'office'
        }
        
        # Type direct depuis building tag
        if building_tag in building_type_mapping:
            return building_type_mapping[building_tag]
        
        # Analyse des autres tags pour building=yes
        if building_tag == 'yes':
            # Analyse amenity
            amenity = tags.get('amenity', '')
            if amenity in ['school', 'university', 'college', 'kindergarten']:
                return 'school'
            elif amenity in ['hospital', 'clinic', 'doctors']:
                return 'hospital'
            elif amenity in ['restaurant', 'cafe', 'fast_food', 'bar', 'pub']:
                return 'commercial'
            elif amenity in ['bank', 'post_office', 'police', 'fire_station']:
                return 'office'
            
            # Analyse shop
            shop = tags.get('shop', '')
            if shop:
                return 'commercial'
            
            # Analyse office
            office = tags.get('office', '')
            if office:
                return 'office'
            
            # Analyse landuse
            landuse = tags.get('landuse', '')
            if landuse == 'residential':
                return 'residential'
            elif landuse == 'industrial':
                return 'industrial'
            elif landuse == 'commercial':
                return 'commercial'
        
        # Par défaut
        return 'residential'
    
    def _calculate_precise_polygon_area(self, coordinates: List[Tuple[float, float]]) -> float:
        """
        Calcule la surface précise d'un polygone en m²
        
        Args:
            coordinates: Liste des coordonnées (lat, lon)
            
        Returns:
            float: Surface en m²
        """
        if not coordinates or len(coordinates) < 3:
            return 100.0
        
        try:
            # Algorithme de Shoelace
            area_deg = 0.0
            n = len(coordinates)
            
            for i in range(n):
                j = (i + 1) % n
                area_deg += coordinates[i][0] * coordinates[j][1]
                area_deg -= coordinates[j][0] * coordinates[i][1]
            
            area_deg = abs(area_deg) / 2.0
            
            # Conversion en m² selon la latitude
            lat_center = sum(coord[0] for coord in coordinates) / len(coordinates)
            meters_per_degree_lat = 111000
            meters_per_degree_lon = 111000 * math.cos(math.radians(lat_center))
            
            area_m2 = area_deg * meters_per_degree_lat * meters_per_degree_lon
            
            # Limites réalistes
            return max(min(area_m2, 100000), 10.0)
            
        except Exception:
            return 100.0
    
    def _calculate_polygon_perimeter(self, coordinates: List[Dict]) -> float:
        """
        Calcule le périmètre d'un polygone en mètres
        
        Args:
            coordinates: Liste des points {'lat': float, 'lon': float}
            
        Returns:
            float: Périmètre en mètres
        """
        if not coordinates or len(coordinates) < 2:
            return 0.0
        
        try:
            perimeter = 0.0
            
            for i in range(len(coordinates)):
                j = (i + 1) % len(coordinates)
                p1 = (coordinates[i]['lat'], coordinates[i]['lon'])
                p2 = (coordinates[j]['lat'], coordinates[j]['lon'])
                perimeter += self._distance_between_points(p1, p2)
            
            return perimeter
            
        except Exception:
            return 0.0
    
    def _distance_between_points(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calcule la distance entre deux points en mètres (formule haversine)"""
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return 6371000 * c  # Rayon terre en mètres
    
    def _calculate_shape_complexity(self, coordinates: List[Dict]) -> float:
        """
        Calcule un indice de complexité de forme (1.0 = cercle parfait, >1.0 = plus complexe)
        
        Args:
            coordinates: Points du polygone
            
        Returns:
            float: Indice de complexité
        """
        if not coordinates or len(coordinates) < 3:
            return 1.0
        
        try:
            # Calcul périmètre et aire
            perimeter = self._calculate_polygon_perimeter(coordinates)
            
            coord_tuples = [(c['lat'], c['lon']) for c in coordinates]
            area_m2 = self._calculate_precise_polygon_area(coord_tuples)
            
            if area_m2 <= 0 or perimeter <= 0:
                return 1.0
            
            # Indice de compacité basé sur le cercle équivalent
            circle_perimeter = 2 * math.sqrt(math.pi * area_m2)
            complexity = perimeter / circle_perimeter
            
            return max(1.0, min(complexity, 5.0))
            
        except Exception:
            return 1.0
    
    def _extract_building_subtype(self, tags: Dict) -> Optional[str]:
        """Extrait le sous-type de bâtiment depuis les tags"""
        subtypes = [
            tags.get('building:type'),
            tags.get('building:use'),
            tags.get('amenity'),
            tags.get('shop'),
            tags.get('office'),
            tags.get('leisure'),
            tags.get('tourism')
        ]
        
        for subtype in subtypes:
            if subtype and subtype != 'yes':
                return subtype
        
        return None
    
    def _extract_construction_material(self, tags: Dict) -> Optional[str]:
        """Extrait le matériau de construction"""
        materials = [
            tags.get('building:material'),
            tags.get('wall:material'),
            tags.get('construction:material')
        ]
        
        for material in materials:
            if material:
                return material
        
        return None
    
    def _extract_construction_year(self, tags: Dict) -> Optional[int]:
        """Extrait l'année de construction"""
        year_sources = [
            tags.get('start_date'),
            tags.get('construction:date'),
            tags.get('building:year'),
            tags.get('year')
        ]
        
        for year_value in year_sources:
            if year_value:
                try:
                    # Extraction de l'année depuis différents formats
                    year_str = str(year_value)
                    if len(year_str) >= 4:
                        year = int(year_str[:4])
                        if 1800 <= year <= 2030:
                            return year
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_roof_material(self, tags: Dict) -> Optional[str]:
        """Extrait le matériau de toiture"""
        roof_materials = [
            tags.get('roof:material'),
            tags.get('roof:covering'),
            tags.get('roofing:material')
        ]
        
        for material in roof_materials:
            if material:
                return material
        
        return None
    
    def _extract_building_use(self, tags: Dict) -> Optional[str]:
        """Extrait l'usage principal du bâtiment"""
        uses = [
            tags.get('building:use'),
            tags.get('use'),
            tags.get('function'),
            tags.get('amenity'),
            tags.get('landuse')
        ]
        
        for use in uses:
            if use and use != 'yes':
                return use
        
        return None
    
    def _calculate_building_validation_score(
        self, 
        geometry_data: Dict, 
        floors_data: Dict, 
        tags: Dict
    ) -> float:
        """
        Calcule un score de validation de 0 à 1 pour le bâtiment
        
        Args:
            geometry_data: Données géométriques
            floors_data: Données d'étages
            tags: Tags OSM
            
        Returns:
            float: Score de validation (0-1)
        """
        score = 0.0
        max_score = 7.0
        
        # Géométrie valide (+1)
        if geometry_data.get('valid', False):
            score += 1.0
        
        # Nombre suffisant de points (+1)
        if geometry_data.get('points_count', 0) >= 4:
            score += 1.0
        
        # Données d'étages de bonne qualité (+1)
        if floors_data.get('confidence') in ['high', 'medium']:
            score += 1.0
        
        # Tag building spécifique (+1)
        building_tag = tags.get('building', '')
        if building_tag and building_tag != 'yes':
            score += 1.0
        
        # Métadonnées enrichies (+1)
        if any(tags.get(key) for key in ['amenity', 'shop', 'office', 'building:use']):
            score += 1.0
        
        # Données de construction (+1)
        if any(tags.get(key) for key in ['building:material', 'start_date', 'building:levels']):
            score += 1.0
        
        # Surface réaliste (+1)
        area = self._calculate_precise_polygon_area(geometry_data.get('coordinates', []))
        if 20 <= area <= 50000:
            score += 1.0
        
        return min(1.0, score / max_score)
    
    def _calculate_processing_statistics(self, buildings: List[Dict], elements: List[Dict]) -> Dict:
        """
        Calcule les statistiques de traitement
        
        Args:
            buildings: Bâtiments traités
            elements: Éléments OSM bruts
            
        Returns:
            Dict: Statistiques de traitement
        """
        total_buildings = len(buildings)
        total_elements = len(elements)
        
        if total_buildings == 0:
            return {
                'processing_rate': 0.0,
                'with_geometry_count': 0,
                'with_floors_count': 0,
                'average_validation_score': 0.0
            }
        
        # Comptages
        with_geometry = sum(1 for b in buildings if b.get('has_precise_geometry', False))
        with_floors = sum(1 for b in buildings if b.get('floors_count', 1) > 1)
        
        # Scores de validation
        validation_scores = [b.get('validation_score', 0) for b in buildings]
        avg_validation = sum(validation_scores) / len(validation_scores)
        
        # Répartition par type
        type_distribution = {}
        for building in buildings:
            btype = building.get('building_type', 'unknown')
            type_distribution[btype] = type_distribution.get(btype, 0) + 1
        
        # Surface totale
        total_area = sum(b.get('surface_area_m2', 0) for b in buildings)
        
        return {
            'processing_rate': round(total_buildings / total_elements, 3),
            'with_geometry_count': with_geometry,
            'with_floors_count': with_floors,
            'geometry_rate': round(with_geometry / total_buildings, 3),
            'floors_rate': round(with_floors / total_buildings, 3),
            'average_validation_score': round(avg_validation, 3),
            'type_distribution': type_distribution,
            'total_surface_area_m2': round(total_area, 1),
            'average_surface_area_m2': round(total_area / total_buildings, 1)
        }
    
    # Méthode alias pour compatibilité
    def fetch_buildings_from_relation(self, zone_name: str) -> Dict:
        """Alias pour compatibilité avec l'ancien code"""
        return self.fetch_buildings_administrative(zone_name)


# ==============================================================================
# FONCTIONS UTILITAIRES GÉOMÉTRIQUES
# ==============================================================================

def validate_enhanced_building_geometry(building: Dict) -> Dict:
    """
    Valide la géométrie améliorée d'un bâtiment
    
    Args:
        building: Bâtiment avec géométrie enrichie
        
    Returns:
        Dict: Résultat de validation détaillé
    """
    if not building:
        return {'valid': False, 'error': 'Bâtiment vide'}
    
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'geometry_quality': 'unknown',
        'metadata_quality': 'unknown'
    }
    
    # Validation géométrie
    geometry = building.get('geometry', [])
    if not geometry or len(geometry) < 3:
        validation_result['valid'] = False
        validation_result['errors'].append('Géométrie insuffisante (< 3 points)')
    else:
        # Qualité géométrique
        points_count = len(geometry)
        if points_count >= 10:
            validation_result['geometry_quality'] = 'excellent'
        elif points_count >= 6:
            validation_result['geometry_quality'] = 'good'
        elif points_count >= 4:
            validation_result['geometry_quality'] = 'fair'
        else:
            validation_result['geometry_quality'] = 'poor'
            validation_result['warnings'].append('Peu de points géométriques')
    
    # Validation surface
    surface = building.get('surface_area_m2', 0)
    if surface <= 0:
        validation_result['errors'].append('Surface invalide')
    elif surface < 10:
        validation_result['warnings'].append('Surface très petite (< 10m²)')
    elif surface > 100000:
        validation_result['warnings'].append('Surface très grande (> 100,000m²)')
    
    # Validation étages
    floors = building.get('floors_count', 1)
    if floors < 1:
        validation_result['errors'].append('Nombre d\'étages invalide')
    elif floors > 200:
        validation_result['warnings'].append('Nombre d\'étages très élevé')
    
    # Qualité métadonnées
    metadata_score = building.get('validation_score', 0)
    if metadata_score >= 0.8:
        validation_result['metadata_quality'] = 'excellent'
    elif metadata_score >= 0.6:
        validation_result['metadata_quality'] = 'good'
    elif metadata_score >= 0.4:
        validation_result['metadata_quality'] = 'fair'
    else:
        validation_result['metadata_quality'] = 'poor'
    
    # Validation finale
    if validation_result['errors']:
        validation_result['valid'] = False
    
    return validation_result


def calculate_geometry_statistics(buildings: List[Dict]) -> Dict:
    """
    Calcule les statistiques géométriques d'une liste de bâtiments
    
    Args:
        buildings: Liste des bâtiments avec géométrie
        
    Returns:
        Dict: Statistiques géométriques complètes
    """
    if not buildings:
        return {'error': 'Aucun bâtiment à analyser'}
    
    # Initialisation
    total_buildings = len(buildings)
    with_precise_geometry = 0
    total_surface = 0
    total_perimeter = 0
    surfaces = []
    perimeters = []
    complexities = []
    floors_list = []
    
    # Analyse par bâtiment
    for building in buildings:
        # Géométrie précise
        if building.get('has_precise_geometry', False):
            with_precise_geometry += 1
        
        # Surface
        surface = building.get('surface_area_m2', 0)
        if surface > 0:
            total_surface += surface
            surfaces.append(surface)
        
        # Périmètre
        perimeter = building.get('polygon_perimeter_m', 0)
        if perimeter > 0:
            total_perimeter += perimeter
            perimeters.append(perimeter)
        
        # Complexité
        complexity = building.get('shape_complexity', 1.0)
        complexities.append(complexity)
        
        # Étages
        floors = building.get('floors_count', 1)
        floors_list.append(floors)
    
    # Calculs statistiques
    geometry_stats = {
        'overview': {
            'total_buildings': total_buildings,
            'with_precise_geometry': with_precise_geometry,
            'geometry_coverage_rate': round(with_precise_geometry / total_buildings, 3),
            'total_surface_area_m2': round(total_surface, 1),
            'total_perimeter_m': round(total_perimeter, 1)
        },
        
        'surface_statistics': {
            'count': len(surfaces),
            'total_m2': round(total_surface, 1),
            'average_m2': round(sum(surfaces) / len(surfaces), 1) if surfaces else 0,
            'min_m2': round(min(surfaces), 1) if surfaces else 0,
            'max_m2': round(max(surfaces), 1) if surfaces else 0,
            'median_m2': round(sorted(surfaces)[len(surfaces)//2], 1) if surfaces else 0
        },
        
        'perimeter_statistics': {
            'count': len(perimeters),
            'total_m': round(total_perimeter, 1),
            'average_m': round(sum(perimeters) / len(perimeters), 1) if perimeters else 0,
            'min_m': round(min(perimeters), 1) if perimeters else 0,
            'max_m': round(max(perimeters), 1) if perimeters else 0
        },
        
        'complexity_statistics': {
            'average_complexity': round(sum(complexities) / len(complexities), 3) if complexities else 1.0,
            'min_complexity': round(min(complexities), 3) if complexities else 1.0,
            'max_complexity': round(max(complexities), 3) if complexities else 1.0,
            'simple_buildings': sum(1 for c in complexities if c <= 1.2),
            'complex_buildings': sum(1 for c in complexities if c >= 2.0)
        },
        
        'floors_statistics': {
            'total_floors': sum(floors_list),
            'average_floors': round(sum(floors_list) / len(floors_list), 2),
            'min_floors': min(floors_list),
            'max_floors': max(floors_list),
            'single_story': sum(1 for f in floors_list if f == 1),
            'multi_story': sum(1 for f in floors_list if f > 1),
            'high_rise': sum(1 for f in floors_list if f >= 10)
        }
    }
    
    return geometry_stats


def export_enhanced_buildings_summary(buildings: List[Dict]) -> Dict:
    """
    Génère un résumé complet des bâtiments améliorés pour export
    
    Args:
        buildings: Liste des bâtiments améliorés
        
    Returns:
        Dict: Résumé complet avec toutes les améliorations
    """
    if not buildings:
        return {'error': 'Aucun bâtiment à analyser'}
    
    # Statistiques de base
    total_count = len(buildings)
    
    # Répartition par type
    type_distribution = {}
    for building in buildings:
        btype = building.get('building_type', 'unknown')
        type_distribution[btype] = type_distribution.get(btype, 0) + 1
    
    # Statistiques géométriques
    geometry_stats = calculate_geometry_statistics(buildings)
    
    # Qualité des données
    validation_scores = [b.get('validation_score', 0) for b in buildings]
    avg_validation = sum(validation_scores) / len(validation_scores)
    
    high_quality = sum(1 for score in validation_scores if score >= 0.8)
    medium_quality = sum(1 for score in validation_scores if 0.5 <= score < 0.8)
    low_quality = sum(1 for score in validation_scores if score < 0.5)
    
    # Sources de données d'étages
    floors_sources = {}
    for building in buildings:
        levels_source = building.get('levels_source', 'estimated')
        floors_sources[levels_source] = floors_sources.get(levels_source, 0) + 1
    
    # Matériaux de construction
    materials = {}
    for building in buildings:
        material = building.get('construction_material')
        if material:
            materials[material] = materials.get(material, 0) + 1
    
    # Années de construction
    years = []
    for building in buildings:
        year = building.get('construction_year')
        if year:
            years.append(year)
    
    # Temps de traitement
    processing_time = datetime.now().isoformat()
    
    summary = {
        'metadata': {
            'total_buildings': total_count,
            'processing_time': processing_time,
            'data_source': 'osm_administrative_enhanced',
            'geometry_extraction': True,
            'floors_extraction': True,
            'enhanced_features': True
        },
        
        'distribution': {
            'by_type': type_distribution,
            'most_common_type': max(type_distribution.items(), key=lambda x: x[1])[0] if type_distribution else 'unknown'
        },
        
        'geometry_analysis': geometry_stats,
        
        'data_quality': {
            'average_validation_score': round(avg_validation, 3),
            'high_quality_buildings': high_quality,
            'medium_quality_buildings': medium_quality,
            'low_quality_buildings': low_quality,
            'quality_distribution_percent': {
                'high': round(high_quality / total_count * 100, 1),
                'medium': round(medium_quality / total_count * 100, 1),
                'low': round(low_quality / total_count * 100, 1)
            }
        },
        
        'floors_analysis': {
            'sources_distribution': floors_sources,
            'buildings_with_floors_data': sum(1 for b in buildings if b.get('levels_source') != 'estimated'),
            'buildings_with_precise_floors': sum(1 for b in buildings if b.get('levels_confidence') == 'high')
        },
        
        'construction_analysis': {
            'materials_distribution': materials,
            'buildings_with_material_info': len(materials),
            'buildings_with_year_info': len(years),
            'year_range': {
                'oldest': min(years) if years else None,
                'newest': max(years) if years else None,
                'average': round(sum(years) / len(years)) if years else None
            }
        },
        
        'enhanced_features': {
            'precise_geometry_count': sum(1 for b in buildings if b.get('has_precise_geometry')),
            'shape_complexity_analyzed': sum(1 for b in buildings if 'shape_complexity' in b),
            'construction_metadata_count': sum(1 for b in buildings if b.get('construction_material') or b.get('construction_year')),
            'osm_metadata_preserved': sum(1 for b in buildings if b.get('osm_timestamp'))
        }
    }
    
    return summary