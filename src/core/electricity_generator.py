#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR ÉLECTRICITÉ AMÉLIORÉ - AVEC POLYGONE ET ÉTAGES
=========================================================

Version améliorée qui utilise les polygones OSM pour calculer la surface précise
et prend en compte le nombre d'étages pour la consommation.
"""

import time
import logging
import math
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from config import MalaysiaConfig
from src.utils.helpers import generate_unique_id

logger = logging.getLogger(__name__)


class EnhancedElectricityGenerator:
    """Générateur de données de consommation électrique amélioré"""
    
    def __init__(self):
        """Initialise le générateur électrique amélioré"""
        self.generation_count = 0
        logger.info("✅ EnhancedElectricityGenerator initialisé (polygone + étages)")
    
    def generate_consumption_timeseries(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H'
    ) -> Dict:
        """
        Génère les séries temporelles de consommation électrique avec géométrie précise
        
        Args:
            buildings: Liste des bâtiments avec polygone et floors_count
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            frequency: Fréquence ('15T', '1H', '3H', 'D')
            
        Returns:
            Dict: Résultat avec DataFrame de consommation
        """
        start_time = time.time()
        self.generation_count += 1
        
        try:
            logger.info(f"Génération consommation améliorée: {len(buildings)} bâtiments")
            logger.info(f"Période: {start_date} → {end_date} ({frequency})")
            
            # Prétraitement des bâtiments avec calculs géométriques
            processed_buildings = self._preprocess_buildings_geometry(buildings)
            
            # Création de l'index temporel
            date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)
            logger.info(f"{len(date_range)} points temporels à générer")
            
            # Génération des données
            consumption_data = []
            
            for building in processed_buildings:
                building_consumption = self._generate_enhanced_building_consumption_series(
                    building, date_range, frequency
                )
                consumption_data.extend(building_consumption)
            
            # Création du DataFrame
            df = pd.DataFrame(consumption_data)
            
            generation_time = time.time() - start_time
            logger.info(f"✅ {len(consumption_data)} points générés en {generation_time:.1f}s")
            
            # Statistiques géométriques (CORRIGÉ: utilisation de .get())
            total_precise_area = sum(b.get('precise_surface_area_m2', 100.0) for b in processed_buildings)
            avg_floors = sum(b.get('floors_count', 1) for b in processed_buildings) / len(processed_buildings)
            
            return {
                'success': True,
                'data': df,
                'metadata': {
                    'total_points': len(consumption_data),
                    'buildings_count': len(buildings),
                    'time_range': f"{start_date} → {end_date}",
                    'frequency': frequency,
                    'generation_time_seconds': generation_time,
                    'generation_id': generate_unique_id('gen'),
                    'geometry_statistics': {
                        'total_precise_surface_m2': round(total_precise_area, 1),
                        'average_floors': round(avg_floors, 1),
                        'buildings_with_geometry': sum(1 for b in processed_buildings if b.get('has_precise_geometry', False)),
                        'buildings_with_floor_data': sum(1 for b in processed_buildings if b.get('floors_count', 1) > 1)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération électricité améliorée: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _preprocess_buildings_geometry(self, buildings: List[Dict]) -> List[Dict]:
        """
        Prétraite les bâtiments pour extraire la géométrie précise et les étages
        
        Args:
            buildings: Liste des bâtiments bruts
            
        Returns:
            List[Dict]: Bâtiments avec géométrie calculée
        """
        processed_buildings = []
        
        logger.info("🔧 Prétraitement géométrique des bâtiments...")
        
        for i, building in enumerate(buildings):
            try:
                # Extraction des données de base (CORRIGÉ: utilisation de .get())
                building_id = (building.get('unique_id') or 
                             building.get('id') or 
                             building.get('building_id') or 
                             f'building_{i}')
                
                building_type = building.get('building_type', 'residential')
                
                # === CALCUL SURFACE PRÉCISE DEPUIS POLYGONE ===
                precise_area, has_geometry = self._calculate_precise_area_from_polygon(building)
                
                # Surface de fallback si pas de géométrie précise
                fallback_area = building.get('surface_area_m2', 100.0)
                if fallback_area <= 0:
                    fallback_area = 100.0
                
                # Utilisation de la surface précise si disponible
                final_surface = precise_area if has_geometry else fallback_area
                
                # === EXTRACTION NOMBRE D'ÉTAGES ===
                floors_count = self._extract_floors_count(building)
                
                # === FACTEURS DE FORME DU BÂTIMENT ===
                shape_factor = self._calculate_building_shape_factor(building) if has_geometry else 1.0
                
                # === MÉTADONNÉES GÉOMÉTRIQUES ===
                geometry_metadata = {
                    'has_precise_geometry': has_geometry,
                    'precise_surface_area_m2': precise_area,
                    'fallback_surface_area_m2': fallback_area,
                    'surface_difference_percent': abs(precise_area - fallback_area) / fallback_area * 100 if fallback_area > 0 else 0,
                    'shape_factor': shape_factor
                }
                
                # Construction du bâtiment enrichi (CORRIGÉ: ajout de has_precise_geometry)
                enhanced_building = {
                    'unique_id': building_id,
                    'building_type': building_type,
                    'latitude': building.get('latitude', 3.1390),
                    'longitude': building.get('longitude', 101.6869),
                    'surface_area_m2': final_surface,  # Surface standard pour compatibilité
                    'precise_surface_area_m2': precise_area,  # Surface calculée du polygone
                    'floors_count': floors_count,
                    'zone_name': building.get('zone_name', 'unknown'),
                    'source': building.get('source', 'osm'),
                    'has_precise_geometry': has_geometry,  # AJOUTÉ: clé manquante
                    'geometry_metadata': geometry_metadata,
                    # Données originales conservées
                    'original_geometry': building.get('geometry', []),
                    'osm_tags': building.get('tags', {}),
                    'osm_id': building.get('osm_id')
                }
                
                processed_buildings.append(enhanced_building)
                
            except Exception as e:
                logger.warning(f"Erreur prétraitement bâtiment {i}: {e}")
                # Bâtiment de fallback (CORRIGÉ: ajout de has_precise_geometry)
                fallback_building = {
                    'unique_id': f'fallback_{i}',
                    'building_type': 'residential',
                    'latitude': 3.1390,
                    'longitude': 101.6869,
                    'surface_area_m2': 100.0,
                    'precise_surface_area_m2': 100.0,
                    'floors_count': 1,
                    'zone_name': 'unknown',
                    'source': 'fallback',
                    'has_precise_geometry': False,  # AJOUTÉ: clé manquante
                    'geometry_metadata': {
                        'has_precise_geometry': False,
                        'precise_surface_area_m2': 100.0,
                        'fallback_surface_area_m2': 100.0,
                        'surface_difference_percent': 0,
                        'shape_factor': 1.0
                    }
                }
                processed_buildings.append(fallback_building)
        
        # Statistiques de prétraitement (CORRIGÉ: utilisation de .get())
        with_geometry = sum(1 for b in processed_buildings if b.get('has_precise_geometry', False))
        multi_floor = sum(1 for b in processed_buildings if b.get('floors_count', 1) > 1)
        
        logger.info(f"✅ Prétraitement terminé: {with_geometry}/{len(processed_buildings)} avec géométrie précise")
        logger.info(f"   📏 {multi_floor}/{len(processed_buildings)} bâtiments multi-étages")
        
        return processed_buildings
    
    def _calculate_precise_area_from_polygon(self, building: Dict) -> Tuple[float, bool]:
        """
        Calcule la surface précise depuis le polygone OSM
        
        Args:
            building: Données du bâtiment avec geometry
            
        Returns:
            Tuple[float, bool]: (surface_en_m2, a_geometrie_precise)
        """
        geometry = building.get('geometry', [])
        
        if not geometry or not isinstance(geometry, list) or len(geometry) < 3:
            return 100.0, False  # Pas de géométrie valide
        
        try:
            # Extraction des coordonnées
            coordinates = []
            for point in geometry:
                if isinstance(point, dict) and 'lat' in point and 'lon' in point:
                    lat = float(point['lat'])
                    lon = float(point['lon'])
                    coordinates.append((lat, lon))
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    lat = float(point[0])
                    lon = float(point[1])
                    coordinates.append((lat, lon))
            
            if len(coordinates) < 3:
                return 100.0, False
            
            # Algorithme de Shoelace pour calculer l'aire d'un polygone
            area_deg = self._shoelace_area(coordinates)
            
            # Conversion degrés vers mètres carrés
            # À Malaysia (~3-7°N), 1 degré ≈ 111 km
            lat_center = sum(coord[0] for coord in coordinates) / len(coordinates)
            
            # Correction pour la longitude selon la latitude
            meters_per_degree_lat = 111000
            meters_per_degree_lon = 111000 * math.cos(math.radians(lat_center))
            
            # Surface en m²
            area_m2 = area_deg * meters_per_degree_lat * meters_per_degree_lon
            
            # Limites réalistes pour les bâtiments
            if area_m2 < 10:
                area_m2 = 50.0  # Minimum 50m²
            elif area_m2 > 100000:
                area_m2 = 100000.0  # Maximum 10 hectares
            
            return area_m2, True
            
        except Exception as e:
            logger.debug(f"Erreur calcul surface polygone: {e}")
            return 100.0, False
    
    def _shoelace_area(self, coordinates: List[Tuple[float, float]]) -> float:
        """
        Calcule l'aire d'un polygone avec la formule shoelace
        
        Args:
            coordinates: Liste des coordonnées (lat, lon)
            
        Returns:
            float: Aire en degrés carrés
        """
        n = len(coordinates)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        
        return abs(area) / 2.0
    
    def _extract_floors_count(self, building: Dict) -> int:
        """
        Extrait le nombre d'étages du bâtiment
        
        Args:
            building: Données du bâtiment
            
        Returns:
            int: Nombre d'étages (minimum 1)
        """
        # Essai de plusieurs sources pour le nombre d'étages
        floors_sources = [
            building.get('floors_count'),
            building.get('floors'),
            building.get('levels'),
            building.get('building_levels'),
            building.get('osm_tags', {}).get('building:levels'),
            building.get('tags', {}).get('building:levels'),
            building.get('osm_tags', {}).get('levels'),
            building.get('tags', {}).get('levels')
        ]
        
        for floors_value in floors_sources:
            if floors_value is not None:
                try:
                    floors = int(float(floors_value))
                    if 1 <= floors <= 200:  # Limites raisonnables
                        return floors
                except (ValueError, TypeError):
                    continue
        
        # Estimation basée sur le type de bâtiment
        building_type = building.get('building_type', 'residential')
        
        if building_type == 'residential':
            # Résidentiel Malaysia: souvent 1-3 étages
            return np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
        elif building_type in ['office', 'commercial']:
            # Bureaux/commercial: 1-10 étages
            return np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                                  p=[0.3, 0.2, 0.15, 0.1, 0.08, 0.06, 0.04, 0.03, 0.02, 0.02])
        elif building_type == 'industrial':
            # Industriel: généralement 1-2 étages
            return np.random.choice([1, 2], p=[0.8, 0.2])
        elif building_type == 'hospital':
            # Hôpital: généralement multi-étages
            return np.random.choice([2, 3, 4, 5, 6], p=[0.1, 0.3, 0.3, 0.2, 0.1])
        else:
            return 1  # Par défaut
    
    def _calculate_building_shape_factor(self, building: Dict) -> float:
        """
        Calcule un facteur de forme du bâtiment (compacité)
        
        Args:
            building: Données du bâtiment avec géométrie
            
        Returns:
            float: Facteur de forme (1.0 = carré parfait, >1.0 = plus allongé)
        """
        geometry = building.get('geometry', [])
        
        if not geometry or len(geometry) < 4:
            return 1.0
        
        try:
            # Calcul du périmètre
            perimeter = 0.0
            for i in range(len(geometry)):
                j = (i + 1) % len(geometry)
                if 'lat' in geometry[i] and 'lat' in geometry[j]:
                    p1 = (geometry[i]['lat'], geometry[i]['lon'])
                    p2 = (geometry[j]['lat'], geometry[j]['lon'])
                    perimeter += self._distance_between_points(p1, p2)
            
            # Surface
            area = building.get('precise_surface_area_m2', 100.0)
            
            # Facteur de forme basé sur le rapport périmètre/aire
            # Un cercle a le rapport minimal, un carré a un rapport de 4/√π ≈ 2.26
            if area > 0:
                shape_factor = perimeter / (2 * math.sqrt(math.pi * area))
                return max(1.0, min(shape_factor, 3.0))  # Limité entre 1.0 et 3.0
            else:
                return 1.0
                
        except Exception:
            return 1.0
    
    def _distance_between_points(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calcule la distance entre deux points en mètres"""
        lat1, lon1 = p1
        lat2, lon2 = p2
        
        # Formule approximative pour de petites distances
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = 6371000 * c  # Rayon terre en mètres
        
        return distance
    
    def _generate_enhanced_building_consumption_series(
        self, 
        building: Dict, 
        date_range: pd.DatetimeIndex,
        frequency: str
    ) -> List[Dict]:
        """
        Génère la série de consommation pour un bâtiment avec géométrie précise
        
        Args:
            building: Données du bâtiment enrichi
            date_range: Index temporel
            frequency: Fréquence d'échantillonnage
            
        Returns:
            List[Dict]: Points de consommation
        """
        # CORRIGÉ: utilisation de .get() pour tous les accès
        building_type = building.get('building_type', 'residential')
        precise_surface = building.get('precise_surface_area_m2', 100.0)
        floors_count = building.get('floors_count', 1)
        shape_factor = building.get('geometry_metadata', {}).get('shape_factor', 1.0)
        building_id = building.get('unique_id', 'unknown')
        
        # Consommation de base avec surface précise
        base_consumption = self._calculate_enhanced_base_consumption(
            building_type, precise_surface, floors_count, shape_factor
        )
        
        consumption_points = []
        
        for timestamp in date_range:
            # Facteurs de variation standard
            hour_factor = self._get_hourly_factor(timestamp.hour, building_type)
            day_factor = self._get_daily_factor(timestamp.dayofweek, building_type)
            seasonal_factor = self._get_seasonal_factor(timestamp.month)
            
            # Facteur d'étages selon l'heure (ascenseurs, éclairage, etc.)
            floors_factor = self._get_floors_factor(timestamp.hour, floors_count, building_type)
            
            # Facteur de forme (bâtiments allongés = plus de surface à climatiser)
            shape_efficiency_factor = 1.0 + (shape_factor - 1.0) * 0.1
            
            # Variation aléatoire
            random_factor = np.random.normal(1.0, 0.1)
            
            # Consommation finale enrichie
            consumption = (base_consumption * 
                          hour_factor * 
                          day_factor * 
                          seasonal_factor * 
                          floors_factor * 
                          shape_efficiency_factor *
                          random_factor)
            
            consumption_points.append({
                'unique_id': building_id,
                'timestamp': timestamp,
                'y': max(0, consumption),
                'frequency': frequency
            })
        
        return consumption_points
    
    def _calculate_enhanced_base_consumption(
        self, 
        building_type: str, 
        precise_surface: float, 
        floors_count: int,
        shape_factor: float
    ) -> float:
        """
        Calcule la consommation de base améliorée avec géométrie
        
        Args:
            building_type: Type de bâtiment
            precise_surface: Surface précise en m²
            floors_count: Nombre d'étages
            shape_factor: Facteur de forme du bâtiment
            
        Returns:
            float: Consommation de base horaire en kWh
        """
        # Consommation de base du type
        config = MalaysiaConfig.get_building_type_config(building_type)
        base_consumption_m2_day = config['base_consumption_kwh_m2_day']
        
        # Surface totale (planchers) = surface sol × étages
        total_floor_area = precise_surface * floors_count
        
        # Consommation de base
        daily_consumption = base_consumption_m2_day * total_floor_area
        
        # Facteurs d'ajustement
        
        # 1. Facteur d'étages (efficacité/inefficacité selon type)
        if building_type == 'residential':
            # Résidentiel: légère inefficacité avec les étages (escaliers, distribution)
            floors_efficiency = 1.0 + (floors_count - 1) * 0.05
        elif building_type in ['office', 'commercial']:
            # Bureau: inefficacité plus marquée (ascenseurs, systèmes centralisés)
            floors_efficiency = 1.0 + (floors_count - 1) * 0.08
        elif building_type == 'industrial':
            # Industriel: impact minimal (souvent un seul étage de production)
            floors_efficiency = 1.0 + max(0, floors_count - 1) * 0.02
        else:
            floors_efficiency = 1.0 + (floors_count - 1) * 0.06
        
        # 2. Facteur de forme (bâtiments allongés moins efficaces)
        shape_penalty = 1.0 + (shape_factor - 1.0) * 0.05
        
        # 3. Facteur de taille (économies/déséconomies d'échelle)
        if total_floor_area < 100:
            size_factor = 1.1  # Petits bâtiments moins efficaces
        elif total_floor_area > 10000:
            size_factor = 0.9  # Gros bâtiments plus efficaces
        else:
            size_factor = 1.0
        
        # Application des facteurs
        adjusted_daily = (daily_consumption * 
                         floors_efficiency * 
                         shape_penalty * 
                         size_factor)
        
        # Conversion en horaire
        hourly_consumption = adjusted_daily / 24
        
        return hourly_consumption
    
    def _get_floors_factor(self, hour: int, floors_count: int, building_type: str) -> float:
        """
        Facteur de consommation lié aux étages selon l'heure
        
        Args:
            hour: Heure de la journée (0-23)
            floors_count: Nombre d'étages
            building_type: Type de bâtiment
            
        Returns:
            float: Facteur multiplicateur
        """
        if floors_count <= 1:
            return 1.0  # Pas d'impact pour un seul étage
        
        # Impact des ascenseurs et systèmes verticaux
        base_floors_impact = 1.0 + (floors_count - 1) * 0.02
        
        if building_type in ['office', 'commercial']:
            # Heures de pointe = plus d'utilisation ascenseurs
            if 8 <= hour <= 9 or 17 <= hour <= 18:
                return base_floors_impact * 1.3  # Pic ascenseurs
            elif 9 <= hour <= 17:
                return base_floors_impact * 1.1  # Usage normal
            else:
                return base_floors_impact * 0.7  # Usage réduit
        
        elif building_type == 'residential':
            # Usage ascenseurs résidentiel plus étalé
            if 6 <= hour <= 8 or 18 <= hour <= 20:
                return base_floors_impact * 1.2
            else:
                return base_floors_impact
        
        elif building_type == 'hospital':
            # Hôpital: usage constant 24h/24
            return base_floors_impact * 1.1
        
        else:
            return base_floors_impact
    
    # Méthodes reprises du générateur standard
    def _get_hourly_factor(self, hour: int, building_type: str) -> float:
        """Facteur de variation horaire"""
        if building_type == 'residential':
            if 6 <= hour <= 8 or 18 <= hour <= 22:
                return 1.5
            elif 0 <= hour <= 5:
                return 0.3
            else:
                return 1.0
        elif building_type in ['office', 'commercial']:
            if 8 <= hour <= 18:
                return 1.8
            else:
                return 0.2
        else:
            return 1.0 + 0.3 * np.sin((hour - 6) * np.pi / 12)
    
    def _get_daily_factor(self, day_of_week: int, building_type: str) -> float:
        """Facteur de variation journalière"""
        if building_type == 'residential':
            return 1.2 if day_of_week >= 5 else 1.0
        elif building_type in ['office', 'commercial']:
            return 0.3 if day_of_week >= 5 else 1.0
        else:
            return 1.0
    
    def _get_seasonal_factor(self, month: int) -> float:
        """Facteur saisonnier"""
        if 6 <= month <= 8:
            return 1.3
        elif 11 <= month <= 12 or 1 <= month <= 2:
            return 0.9
        else:
            return 1.0