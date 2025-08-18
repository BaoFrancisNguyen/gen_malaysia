#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR CONSOMMATION D'EAU
================================================================

Version qui utilise les polygones OSM et le nombre d'étages
pour une génération plus précise de la consommation d'eau.
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


class WaterGenerator:
    """Générateur de consommation d'eau amélioré avec géométrie précise"""
    
    def __init__(self):
        """Initialise le générateur d'eau amélioré"""
        self.generation_count = 0
        logger.info("✅ WaterGenerator initialisé (polygone + étages)")
    
    def generate_water_consumption_timeseries(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H'
    ) -> Dict:
        """
        Génère les séries temporelles de consommation d'eau avec géométrie précise
        
        Args:
            buildings: Liste des bâtiments avec polygone et floors_count
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            frequency: Fréquence ('15T', '1H', '3H', 'D')
            
        Returns:
            Dict: Résultat avec DataFrame de consommation d'eau
        """
        start_time = time.time()
        self.generation_count += 1
        
        try:
            logger.info(f"Génération consommation eau améliorée: {len(buildings)} bâtiments")
            logger.info(f"Période: {start_date} → {end_date} ({frequency})")
            
            # Prétraitement des bâtiments (réutilise la logique du générateur électrique)
            processed_buildings = self._preprocess_buildings_for_water(buildings)
            
            # Création de l'index temporel
            date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)
            logger.info(f"{len(date_range)} points temporels à générer")
            
            # Génération des données
            water_data = []
            
            for building in processed_buildings:
                building_water = self._generate_enhanced_building_water_series(
                    building, date_range, frequency
                )
                water_data.extend(building_water)
            
            # Création du DataFrame
            df = pd.DataFrame(water_data)
            
            generation_time = time.time() - start_time
            logger.info(f"✅ {len(water_data)} points eau générés en {generation_time:.1f}s")
            
            # Statistiques géométriques eau
            total_water_capacity = sum(self._calculate_building_water_capacity(b) for b in processed_buildings)
            avg_floors = sum(b['floors_count'] for b in processed_buildings) / len(processed_buildings)
            
            return {
                'success': True,
                'data': df,
                'metadata': {
                    'total_points': len(water_data),
                    'buildings_count': len(buildings),
                    'time_range': f"{start_date} → {end_date}",
                    'frequency': frequency,
                    'generation_time_seconds': generation_time,
                    'generation_id': generate_unique_id('water'),
                    'water_statistics': {
                        'total_daily_capacity_liters': round(total_water_capacity, 1),
                        'average_floors': round(avg_floors, 1),
                        'buildings_with_geometry': sum(1 for b in processed_buildings if b['has_precise_geometry']),
                        'buildings_with_floor_data': sum(1 for b in processed_buildings if b['floors_count'] > 1)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération eau améliorée: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _preprocess_buildings_for_water(self, buildings: List[Dict]) -> List[Dict]:
        """
        Prétraite les bâtiments pour l'eau (simplifié par rapport à l'électricité)
        
        Args:
            buildings: Liste des bâtiments bruts
            
        Returns:
            List[Dict]: Bâtiments avec géométrie calculée pour l'eau
        """
        processed_buildings = []
        
        logger.info("🔧 Prétraitement géométrique des bâtiments pour l'eau...")
        
        for i, building in enumerate(buildings):
            try:
                # Extraction des données de base
                building_id = (building.get('unique_id') or 
                             building.get('id') or 
                             building.get('building_id') or 
                             f'water_building_{i}')
                
                building_type = building.get('building_type', 'residential')
                
                # === CALCUL SURFACE PRÉCISE DEPUIS POLYGONE ===
                precise_area, has_geometry = self._calculate_precise_area_from_polygon(building)
                fallback_area = building.get('surface_area_m2', 100.0)
                if fallback_area <= 0:
                    fallback_area = 100.0
                
                final_surface = precise_area if has_geometry else fallback_area
                
                # === EXTRACTION NOMBRE D'ÉTAGES ===
                floors_count = self._extract_floors_count(building)
                
                # === CALCULS SPÉCIFIQUES À L'EAU ===
                water_pressure_floors = self._calculate_water_pressure_needs(floors_count)
                water_distribution_complexity = self._calculate_distribution_complexity(building, has_geometry)
                
                # Construction du bâtiment enrichi pour l'eau
                enhanced_building = {
                    'unique_id': building_id,
                    'building_type': building_type,
                    'latitude': building.get('latitude', 3.1390),
                    'longitude': building.get('longitude', 101.6869),
                    'surface_area_m2': final_surface,
                    'precise_surface_area_m2': precise_area,
                    'floors_count': floors_count,
                    'zone_name': building.get('zone_name', 'unknown'),
                    'source': building.get('source', 'osm'),
                    'has_precise_geometry': has_geometry,
                    # Spécifiques à l'eau
                    'water_pressure_needs': water_pressure_floors,
                    'distribution_complexity': water_distribution_complexity,
                    'original_geometry': building.get('geometry', []),
                    'osm_tags': building.get('tags', {}),
                    'osm_id': building.get('osm_id')
                }
                
                processed_buildings.append(enhanced_building)
                
            except Exception as e:
                logger.warning(f"Erreur prétraitement bâtiment eau {i}: {e}")
                # Bâtiment de fallback pour l'eau
                fallback_building = {
                    'unique_id': f'water_fallback_{i}',
                    'building_type': 'residential',
                    'latitude': 3.1390,
                    'longitude': 101.6869,
                    'surface_area_m2': 100.0,
                    'precise_surface_area_m2': 100.0,
                    'floors_count': 1,
                    'zone_name': 'unknown',
                    'source': 'fallback',
                    'has_precise_geometry': False,
                    'water_pressure_needs': 1.0,
                    'distribution_complexity': 1.0
                }
                processed_buildings.append(fallback_building)
        
        logger.info(f"✅ Prétraitement eau terminé: {len(processed_buildings)} bâtiments")
        
        return processed_buildings
    
    def _calculate_precise_area_from_polygon(self, building: Dict) -> Tuple[float, bool]:
        """
        Calcule la surface précise depuis le polygone OSM (identique au générateur électricité)
        """
        geometry = building.get('geometry', [])
        
        if not geometry or not isinstance(geometry, list) or len(geometry) < 3:
            return 100.0, False
        
        try:
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
            
            # Algorithme de Shoelace
            area_deg = self._shoelace_area(coordinates)
            
            # Conversion en m²
            lat_center = sum(coord[0] for coord in coordinates) / len(coordinates)
            meters_per_degree_lat = 111000
            meters_per_degree_lon = 111000 * math.cos(math.radians(lat_center))
            area_m2 = area_deg * meters_per_degree_lat * meters_per_degree_lon
            
            # Limites réalistes
            if area_m2 < 10:
                area_m2 = 50.0
            elif area_m2 > 100000:
                area_m2 = 100000.0
            
            return area_m2, True
            
        except Exception as e:
            logger.debug(f"Erreur calcul surface polygone eau: {e}")
            return 100.0, False
    
    def _shoelace_area(self, coordinates: List[Tuple[float, float]]) -> float:
        """Calcule l'aire avec la formule shoelace"""
        n = len(coordinates)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        
        return abs(area) / 2.0
    
    def _extract_floors_count(self, building: Dict) -> int:
        """
        Extrait le nombre d'étages (identique au générateur électricité)
        """
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
                    if 1 <= floors <= 200:
                        return floors
                except (ValueError, TypeError):
                    continue
        
        # Estimation basée sur le type
        building_type = building.get('building_type', 'residential')
        
        if building_type == 'residential':
            return np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
        elif building_type in ['office', 'commercial']:
            return np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                                  p=[0.3, 0.2, 0.15, 0.1, 0.08, 0.06, 0.04, 0.03, 0.02, 0.02])
        elif building_type == 'industrial':
            return np.random.choice([1, 2], p=[0.8, 0.2])
        elif building_type == 'hospital':
            return np.random.choice([2, 3, 4, 5, 6], p=[0.1, 0.3, 0.3, 0.2, 0.1])
        else:
            return 1
    
    def _calculate_water_pressure_needs(self, floors_count: int) -> float:
        """
        Calcule les besoins en pression d'eau selon les étages
        
        Args:
            floors_count: Nombre d'étages
            
        Returns:
            float: Facteur de pression (1.0 = base, >1.0 = plus de pression)
        """
        if floors_count <= 1:
            return 1.0
        
        # Pression supplémentaire nécessaire par étage
        # En Malaysia, environ 0.1 bar par mètre (3m par étage)
        pressure_factor = 1.0 + (floors_count - 1) * 0.05
        
        # Seuils pour pompes de surpression
        if floors_count > 5:
            pressure_factor *= 1.1  # Système de pompage plus complexe
        if floors_count > 10:
            pressure_factor *= 1.15  # Système haute pression
        
        return pressure_factor
    
    def _calculate_distribution_complexity(self, building: Dict, has_geometry: bool) -> float:
        """
        Calcule la complexité de distribution d'eau selon la forme du bâtiment
        
        Args:
            building: Données du bâtiment
            has_geometry: Si la géométrie précise est disponible
            
        Returns:
            float: Facteur de complexité (1.0 = simple, >1.0 = plus complexe)
        """
        if not has_geometry:
            return 1.0
        
        geometry = building.get('geometry', [])
        if len(geometry) < 4:
            return 1.0
        
        try:
            # Calcul du facteur de forme (périmètre/aire)
            coordinates = []
            for point in geometry:
                if 'lat' in point and 'lon' in point:
                    coordinates.append((point['lat'], point['lon']))
            
            if len(coordinates) < 3:
                return 1.0
            
            # Calcul périmètre
            perimeter = 0.0
            for i in range(len(coordinates)):
                j = (i + 1) % len(coordinates)
                dx = coordinates[j][0] - coordinates[i][0]
                dy = coordinates[j][1] - coordinates[i][1]
                perimeter += math.sqrt(dx*dx + dy*dy)
            
            # Calcul aire
            area = self._shoelace_area(coordinates)
            
            if area <= 0:
                return 1.0
            
            # Facteur de forme (bâtiments allongés = distribution plus complexe)
            shape_factor = perimeter / (2 * math.sqrt(math.pi * area))
            
            # Complexité distribution basée sur la forme
            # Formes allongées nécessitent plus de tuyauterie
            complexity = 1.0 + (shape_factor - 1.0) * 0.08
            
            return max(1.0, min(complexity, 2.0))
            
        except Exception:
            return 1.0
    
    def _calculate_building_water_capacity(self, building: Dict) -> float:
        """
        Calcule la capacité journalière d'eau du bâtiment
        
        Args:
            building: Données du bâtiment enrichi
            
        Returns:
            float: Capacité journalière en litres
        """
        building_type = building['building_type']
        precise_surface = building['precise_surface_area_m2']
        floors_count = building['floors_count']
        
        # Consommation de base du type
        config = MalaysiaConfig.get_building_type_config(building_type)
        base_consumption_m2_day = config.get('base_water_consumption_l_m2_day', 150)
        
        # Surface totale = surface sol × étages
        total_floor_area = precise_surface * floors_count
        
        # Capacité de base
        daily_capacity = base_consumption_m2_day * total_floor_area
        
        return daily_capacity
    
    def _generate_enhanced_building_water_series(
        self, 
        building: Dict, 
        date_range: pd.DatetimeIndex,
        frequency: str
    ) -> List[Dict]:
        """
        Génère la série de consommation d'eau pour un bâtiment avec géométrie précise
        
        Args:
            building: Données du bâtiment enrichi
            date_range: Index temporel
            frequency: Fréquence d'échantillonnage
            
        Returns:
            List[Dict]: Points de consommation d'eau
        """
        building_type = building['building_type']
        precise_surface = building['precise_surface_area_m2']
        floors_count = building['floors_count']
        pressure_needs = building['water_pressure_needs']
        distribution_complexity = building['distribution_complexity']
        building_id = building['unique_id']
        
        # Consommation de base avec géométrie précise
        base_water_consumption = self._calculate_enhanced_base_water_consumption(
            building_type, precise_surface, floors_count, pressure_needs, distribution_complexity
        )
        
        water_points = []
        
        for timestamp in date_range:
            # Facteurs de variation eau
            hour_factor = self._get_water_hourly_factor(timestamp.hour, building_type)
            day_factor = self._get_water_daily_factor(timestamp.dayofweek, building_type)
            seasonal_factor = self._get_water_seasonal_factor(timestamp.month)
            
            # Facteurs spécifiques à l'eau multi-étages
            floors_water_factor = self._get_floors_water_factor(timestamp.hour, floors_count, building_type)
            
            # Facteur de pression (pertes dans les systèmes complexes)
            pressure_efficiency_factor = 1.0 + (pressure_needs - 1.0) * 0.02
            
            # Facteur de distribution (pertes dans les systèmes complexes)
            distribution_loss_factor = distribution_complexity
            
            # Variation aléatoire (plus élevée pour l'eau)
            random_factor = np.random.normal(1.0, 0.15)
            
            # Consommation finale eau enrichie
            water_consumption = (base_water_consumption * 
                               hour_factor * 
                               day_factor * 
                               seasonal_factor * 
                               floors_water_factor * 
                               pressure_efficiency_factor * 
                               distribution_loss_factor *
                               random_factor)
            
            water_points.append({
                'unique_id': building_id,
                'timestamp': timestamp,
                'y': max(0, water_consumption),
                'frequency': frequency
            })
        
        return water_points
    
    def _calculate_enhanced_base_water_consumption(
        self, 
        building_type: str, 
        precise_surface: float, 
        floors_count: int,
        pressure_needs: float,
        distribution_complexity: float
    ) -> float:
        """
        Calcule la consommation d'eau de base améliorée avec géométrie
        
        Args:
            building_type: Type de bâtiment
            precise_surface: Surface précise en m²
            floors_count: Nombre d'étages
            pressure_needs: Besoins en pression
            distribution_complexity: Complexité de distribution
            
        Returns:
            float: Consommation de base horaire en litres
        """
        # Consommation de base du type
        config = MalaysiaConfig.get_building_type_config(building_type)
        base_consumption_m2_day = config.get('base_water_consumption_l_m2_day', 150)
        
        # Surface totale (planchers) = surface sol × étages
        total_floor_area = precise_surface * floors_count
        
        # Consommation de base
        daily_consumption = base_consumption_m2_day * total_floor_area
        
        # Facteurs d'ajustement spécifiques à l'eau
        
        # 1. Facteur d'étages pour l'eau (différent de l'électricité)
        if building_type == 'residential':
            # Résidentiel: plus d'étages = plus de points d'eau
            floors_efficiency = 1.0 + (floors_count - 1) * 0.1
        elif building_type in ['office', 'commercial']:
            # Bureau: plus d'étages = systèmes plus efficaces mais plus de points d'eau
            floors_efficiency = 1.0 + (floors_count - 1) * 0.12
        elif building_type == 'hospital':
            # Hôpital: besoins très élevés par étage
            floors_efficiency = 1.0 + (floors_count - 1) * 0.15
        else:
            floors_efficiency = 1.0 + (floors_count - 1) * 0.08
        
        # 2. Facteur de pression (surpression nécessaire)
        pressure_factor = pressure_needs
        
        # 3. Facteur de distribution (pertes selon complexité)
        distribution_factor = distribution_complexity
        
        # 4. Facteur de taille (économies d'échelle moins marquées pour l'eau)
        if total_floor_area < 100:
            size_factor = 1.05  # Petits bâtiments légèrement moins efficaces
        elif total_floor_area > 10000:
            size_factor = 0.95  # Gros bâtiments légèrement plus efficaces
        else:
            size_factor = 1.0
        
        # Application des facteurs
        adjusted_daily = (daily_consumption * 
                         floors_efficiency * 
                         pressure_factor * 
                         distribution_factor * 
                         size_factor)
        
        # Conversion en horaire
        hourly_consumption = adjusted_daily / 24
        
        return hourly_consumption
    
    def _get_floors_water_factor(self, hour: int, floors_count: int, building_type: str) -> float:
        """
        Facteur de consommation d'eau lié aux étages selon l'heure
        
        Args:
            hour: Heure de la journée (0-23)
            floors_count: Nombre d'étages
            building_type: Type de bâtiment
            
        Returns:
            float: Facteur multiplicateur
        """
        if floors_count <= 1:
            return 1.0
        
        # Impact des systèmes verticaux d'eau
        base_floors_impact = 1.0 + (floors_count - 1) * 0.03
        
        if building_type in ['office', 'commercial']:
            # Heures de pointe = plus d'utilisation toilettes, fontaines
            if 8 <= hour <= 9 or 12 <= hour <= 13 or 17 <= hour <= 18:
                return base_floors_impact * 1.4  # Pics d'usage
            elif 9 <= hour <= 17:
                return base_floors_impact * 1.2  # Usage normal
            else:
                return base_floors_impact * 0.5  # Usage réduit
        
        elif building_type == 'residential':
            # Usage eau résidentiel étalé mais avec pics
            if 6 <= hour <= 8 or 18 <= hour <= 21:  # Douches, bains
                return base_floors_impact * 1.3
            elif 11 <= hour <= 13:  # Cuisine
                return base_floors_impact * 1.1
            else:
                return base_floors_impact
        
        elif building_type == 'hospital':
            # Hôpital: usage constant mais plus élevé la journée
            return base_floors_impact * (1.0 + 0.2 * math.sin((hour - 6) * math.pi / 12))
        
        else:
            return base_floors_impact
    
    # Méthodes reprises du générateur eau standard
    def _get_water_hourly_factor(self, hour: int, building_type: str) -> float:
        """Facteur de variation horaire pour l'eau"""
        if building_type == 'residential':
            if 6 <= hour <= 8:    # Matin
                return 2.0
            elif 11 <= hour <= 13:  # Midi
                return 1.5
            elif 18 <= hour <= 21:  # Soir
                return 1.8
            elif 22 <= hour <= 6:   # Nuit
                return 0.2
            else:
                return 1.0
        elif building_type in ['office', 'commercial']:
            if 8 <= hour <= 18:
                return 1.5
            else:
                return 0.1
        elif building_type == 'hospital':
            return 1.0 + 0.2 * np.sin((hour - 6) * np.pi / 12)
        else:
            if 7 <= hour <= 19:
                return 1.8
            else:
                return 0.3
    
    def _get_water_daily_factor(self, day_of_week: int, building_type: str) -> float:
        """Facteur de variation journalière pour l'eau"""
        if building_type == 'residential':
            return 1.3 if day_of_week >= 5 else 1.0  # Plus d'eau weekend
        elif building_type in ['office', 'commercial', 'school']:
            return 0.2 if day_of_week >= 5 else 1.0  # Beaucoup moins weekend
        else:
            return 1.0  # Constant pour industriel/hôpital
    
    def _get_water_seasonal_factor(self, month: int) -> float:
        """Facteur saisonnier eau (climat tropical Malaysia)"""
        if 6 <= month <= 8:  # Saison sèche
            return 1.4
        elif 11 <= month <= 12 or 1 <= month <= 2:  # Saison des pluies
            return 0.8
        else:
            return 1.0


# ==============================================================================
# FONCTIONS UTILITAIRES POUR L'EAU
# ==============================================================================

def calculate_building_water_efficiency(building: Dict) -> Dict:
    """
    Calcule l'efficacité hydrique d'un bâtiment
    
    Args:
        building: Données du bâtiment avec géométrie
        
    Returns:
        Dict: Analyse d'efficacité hydrique
    """
    if not building:
        return {'error': 'Bâtiment invalide'}
    
    building_type = building.get('building_type', 'residential')
    floors_count = building.get('floors_count', 1)
    precise_surface = building.get('precise_surface_area_m2', 100)
    has_geometry = building.get('has_precise_geometry', False)
    
    # Calcul de l'intensité d'eau théorique
    config = MalaysiaConfig.get_building_type_config(building_type)
    base_water_m2_day = config.get('base_water_consumption_l_m2_day', 150)
    
    # Surface totale des planchers
    total_floor_area = precise_surface * floors_count
    theoretical_daily_consumption = base_water_m2_day * total_floor_area
    
    # Facteurs d'efficacité
    # 1. Efficacité géométrique
    if has_geometry:
        distribution_complexity = building.get('distribution_complexity', 1.0)
        geometry_efficiency = 1.0 / distribution_complexity
    else:
        geometry_efficiency = 1.0
    
    # 2. Efficacité verticale (étages)
    if floors_count <= 2:
        vertical_efficiency = 1.0  # Optimal
    elif floors_count <= 5:
        vertical_efficiency = 0.95  # Légères pertes
    elif floors_count <= 10:
        vertical_efficiency = 0.90  # Pertes modérées
    else:
        vertical_efficiency = 0.85  # Pertes importantes
    
    # 3. Efficacité de type de bâtiment
    type_efficiency = {
        'residential': 0.85,    # Usage varié, moins optimisé
        'office': 0.90,        # Usage prévisible
        'commercial': 0.80,    # Usage intensif
        'industrial': 0.75,    # Besoins process
        'hospital': 0.70,      # Besoins sanitaires stricts
        'school': 0.85         # Usage modéré et prévisible
    }.get(building_type, 0.80)
    
    # Efficacité globale
    overall_efficiency = geometry_efficiency * vertical_efficiency * type_efficiency
    
    # Consommation réelle estimée
    actual_daily_consumption = theoretical_daily_consumption / overall_efficiency
    
    # Classification efficacité
    if overall_efficiency > 0.9:
        efficiency_class = 'Excellent'
    elif overall_efficiency > 0.8:
        efficiency_class = 'Bon'
    elif overall_efficiency > 0.7:
        efficiency_class = 'Moyen'
    else:
        efficiency_class = 'Médiocre'
    
    return {
        'building_id': building.get('unique_id', 'unknown'),
        'building_type': building_type,
        'floors_count': floors_count,
        'total_floor_area_m2': round(total_floor_area, 1),
        'water_consumption': {
            'theoretical_daily_liters': round(theoretical_daily_consumption, 1),
            'actual_daily_liters': round(actual_daily_consumption, 1),
            'intensity_l_m2_day': round(actual_daily_consumption / total_floor_area, 2),
            'annual_m3': round(actual_daily_consumption * 365 / 1000, 1)
        },
        'efficiency_factors': {
            'geometry_efficiency': round(geometry_efficiency, 3),
            'vertical_efficiency': round(vertical_efficiency, 3),
            'type_efficiency': round(type_efficiency, 3),
            'overall_efficiency': round(overall_efficiency, 3)
        },
        'efficiency_class': efficiency_class,
        'has_precise_geometry': has_geometry,
        'optimization_potential': {
            'water_savings_percent': round((1 - overall_efficiency) * 100, 1),
            'potential_daily_savings_liters': round(actual_daily_consumption - theoretical_daily_consumption, 1)
        }
    }


def analyze_water_consumption_patterns(buildings: List[Dict]) -> Dict:
    """
    Analyse les patterns de consommation d'eau d'une liste de bâtiments
    
    Args:
        buildings: Liste des bâtiments avec données eau
        
    Returns:
        Dict: Analyse des patterns de consommation
    """
    if not buildings:
        return {'error': 'Aucun bâtiment à analyser'}
    
    # Initialisation
    total_buildings = len(buildings)
    total_daily_consumption = 0
    consumption_by_type = {}
    consumption_by_floors = {}
    efficiency_distribution = {}
    
    # Analyse par bâtiment
    for building in buildings:
        # Calcul efficacité
        efficiency_data = calculate_building_water_efficiency(building)
        
        if 'error' not in efficiency_data:
            building_type = efficiency_data['building_type']
            floors = efficiency_data['floors_count']
            daily_consumption = efficiency_data['water_consumption']['actual_daily_liters']
            efficiency_class = efficiency_data['efficiency_class']
            
            # Accumulation totale
            total_daily_consumption += daily_consumption
            
            # Par type de bâtiment
            if building_type not in consumption_by_type:
                consumption_by_type[building_type] = {
                    'count': 0,
                    'total_daily_liters': 0,
                    'total_floor_area': 0
                }
            
            consumption_by_type[building_type]['count'] += 1
            consumption_by_type[building_type]['total_daily_liters'] += daily_consumption
            consumption_by_type[building_type]['total_floor_area'] += efficiency_data['total_floor_area_m2']
            
            # Par nombre d'étages
            floors_category = '1' if floors == 1 else '2-3' if floors <= 3 else '4-10' if floors <= 10 else '10+'
            if floors_category not in consumption_by_floors:
                consumption_by_floors[floors_category] = {
                    'count': 0,
                    'total_daily_liters': 0
                }
            consumption_by_floors[floors_category]['count'] += 1
            consumption_by_floors[floors_category]['total_daily_liters'] += daily_consumption
            
            # Distribution efficacité
            efficiency_distribution[efficiency_class] = efficiency_distribution.get(efficiency_class, 0) + 1
    
    # Calcul des moyennes par type
    for btype, data in consumption_by_type.items():
        if data['count'] > 0:
            data['average_daily_liters'] = round(data['total_daily_liters'] / data['count'], 1)
            data['intensity_l_m2_day'] = round(data['total_daily_liters'] / data['total_floor_area'], 2) if data['total_floor_area'] > 0 else 0
    
    # Calcul des moyennes par étages
    for floors_cat, data in consumption_by_floors.items():
        if data['count'] > 0:
            data['average_daily_liters'] = round(data['total_daily_liters'] / data['count'], 1)
    
    # Statistiques globales
    total_annual_m3 = total_daily_consumption * 365 / 1000
    average_daily_per_building = total_daily_consumption / total_buildings if total_buildings > 0 else 0
    
    return {
        'overview': {
            'total_buildings': total_buildings,
            'total_daily_consumption_liters': round(total_daily_consumption, 1),
            'total_annual_consumption_m3': round(total_annual_m3, 1),
            'average_daily_per_building_liters': round(average_daily_per_building, 1)
        },
        'consumption_by_type': consumption_by_type,
        'consumption_by_floors': consumption_by_floors,
        'efficiency_distribution': efficiency_distribution,
        'efficiency_statistics': {
            'excellent_count': efficiency_distribution.get('Excellent', 0),
            'good_count': efficiency_distribution.get('Bon', 0),
            'average_count': efficiency_distribution.get('Moyen', 0),
            'poor_count': efficiency_distribution.get('Médiocre', 0),
            'excellent_percent': round(efficiency_distribution.get('Excellent', 0) / total_buildings * 100, 1),
            'improvement_potential_percent': round((efficiency_distribution.get('Moyen', 0) + efficiency_distribution.get('Médiocre', 0)) / total_buildings * 100, 1)
        }
    }


def generate_water_optimization_report(buildings: List[Dict]) -> Dict:
    """
    Génère un rapport d'optimisation de la consommation d'eau
    
    Args:
        buildings: Liste des bâtiments
        
    Returns:
        Dict: Rapport d'optimisation complet
    """
    if not buildings:
        return {'error': 'Aucun bâtiment à analyser'}
    
    # Analyse de base
    patterns_analysis = analyze_water_consumption_patterns(buildings)
    
    if 'error' in patterns_analysis:
        return patterns_analysis
    
    # Calcul du potentiel d'économie
    total_savings_potential = 0
    optimization_measures = {
        'geometry_optimization': {'count': 0, 'potential_savings': 0},
        'vertical_optimization': {'count': 0, 'potential_savings': 0},
        'type_optimization': {'count': 0, 'potential_savings': 0}
    }
    
    buildings_needing_optimization = []
    
    for building in buildings:
        efficiency_data = calculate_building_water_efficiency(building)
        
        if 'error' not in efficiency_data:
            overall_efficiency = efficiency_data['efficiency_factors']['overall_efficiency']
            
            if overall_efficiency < 0.8:  # Bâtiments avec potentiel d'amélioration
                building_savings = efficiency_data['optimization_potential']['potential_daily_savings_liters']
                total_savings_potential += building_savings
                
                buildings_needing_optimization.append({
                    'building_id': efficiency_data['building_id'],
                    'building_type': efficiency_data['building_type'],
                    'efficiency_class': efficiency_data['efficiency_class'],
                    'daily_savings_potential': building_savings,
                    'efficiency_factors': efficiency_data['efficiency_factors']
                })
                
                # Catégorisation des mesures
                factors = efficiency_data['efficiency_factors']
                if factors['geometry_efficiency'] < 0.9:
                    optimization_measures['geometry_optimization']['count'] += 1
                    optimization_measures['geometry_optimization']['potential_savings'] += building_savings * 0.3
                
                if factors['vertical_efficiency'] < 0.9:
                    optimization_measures['vertical_optimization']['count'] += 1
                    optimization_measures['vertical_optimization']['potential_savings'] += building_savings * 0.4
                
                if factors['type_efficiency'] < 0.8:
                    optimization_measures['type_optimization']['count'] += 1
                    optimization_measures['type_optimization']['potential_savings'] += building_savings * 0.3
    
    # Tri par potentiel d'économie
    buildings_needing_optimization.sort(key=lambda x: x['daily_savings_potential'], reverse=True)
    
    # Recommandations
    recommendations = []
    
    if optimization_measures['geometry_optimization']['count'] > 0:
        recommendations.append({
            'measure': 'Optimisation géométrique',
            'description': 'Réduire la complexité de distribution d\'eau',
            'buildings_affected': optimization_measures['geometry_optimization']['count'],
            'potential_daily_savings': round(optimization_measures['geometry_optimization']['potential_savings'], 1),
            'actions': ['Simplifier les réseaux de tuyauterie', 'Optimiser l\'emplacement des points d\'eau', 'Réduire les longueurs de canalisations']
        })
    
    if optimization_measures['vertical_optimization']['count'] > 0:
        recommendations.append({
            'measure': 'Optimisation verticale',
            'description': 'Améliorer l\'efficacité des systèmes multi-étages',
            'buildings_affected': optimization_measures['vertical_optimization']['count'],
            'potential_daily_savings': round(optimization_measures['vertical_optimization']['potential_savings'], 1),
            'actions': ['Installer des systèmes de surpression efficaces', 'Optimiser la pression par zone', 'Réduire les pertes de charge']
        })
    
    if optimization_measures['type_optimization']['count'] > 0:
        recommendations.append({
            'measure': 'Optimisation par usage',
            'description': 'Adapter les systèmes aux besoins spécifiques',
            'buildings_affected': optimization_measures['type_optimization']['count'],
            'potential_daily_savings': round(optimization_measures['type_optimization']['potential_savings'], 1),
            'actions': ['Installer des équipements économes', 'Optimiser les débits', 'Mettre en place des systèmes de récupération']
        })
    
    # Calcul ROI approximatif
    annual_savings_m3 = total_savings_potential * 365 / 1000
    estimated_annual_savings_myr = annual_savings_m3 * 2.5  # ~2.5 MYR/m³ en Malaysia
    
    return {
        'executive_summary': {
            'total_buildings_analyzed': len(buildings),
            'buildings_needing_optimization': len(buildings_needing_optimization),
            'optimization_rate_percent': round(len(buildings_needing_optimization) / len(buildings) * 100, 1),
            'total_daily_savings_potential_liters': round(total_savings_potential, 1),
            'total_annual_savings_potential_m3': round(annual_savings_m3, 1),
            'estimated_annual_savings_myr': round(estimated_annual_savings_myr, 0)
        },
        'optimization_measures': optimization_measures,
        'recommendations': recommendations,
        'priority_buildings': buildings_needing_optimization[:10],  # Top 10
        'patterns_analysis': patterns_analysis,
        'generated_at': datetime.now().isoformat(),
        'report_version': '1.0.0'
    }