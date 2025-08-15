#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODÈLE BUILDING - STRUCTURES DE DONNÉES
========================================

Modèle de données pour les bâtiments Malaysia. Version optimisée sans redondances.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from config import MalaysiaConfig
from src.utils.helpers import (validate_malaysia_coordinates, generate_building_id, 
                              calculate_approximate_area, normalize_building_type)


@dataclass
class Building:
    """
    Modèle de données pour un bâtiment avec propriétés énergétiques
    VERSION OPTIMISÉE - Suppression des redondances avec config et helpers
    """
    
    # Identifiants
    id: str
    osm_id: Optional[str] = None
    
    # Géolocalisation
    latitude: float = 0.0
    longitude: float = 0.0
    zone_name: Optional[str] = None
    
    # Caractéristiques physiques
    building_type: str = 'residential'
    surface_area_m2: float = 100.0
    floors_count: int = 1
    construction_year: Optional[int] = None
    
    # Propriétés énergétiques (référence config centralisée)
    energy_efficiency_class: str = 'C'  # A, B, C, D, E
    base_consumption_kwh_m2_day: float = field(init=False)
    base_water_consumption_l_m2_day: float = field(init=False)
    heating_type: str = 'none'  # Malaysia = tropical
    cooling_type: str = 'electric'  # air conditioning
    
    # Métadonnées OSM
    osm_tags: Dict = field(default_factory=dict)
    source: str = 'manual'
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validation et calculs automatiques après création"""
        self._validate_coordinates()
        self._normalize_building_type()
        self._calculate_energy_properties()
    
    def _validate_coordinates(self):
        """Valide que les coordonnées sont dans les limites Malaysia"""
        if not validate_malaysia_coordinates(self.latitude, self.longitude):
            raise ValueError(f"Coordonnées hors Malaysia: {self.latitude}, {self.longitude}")
    
    def _normalize_building_type(self):
        """Normalise le type de bâtiment - UTILISE HELPER CENTRALISÉ"""
        self.building_type = normalize_building_type(self.building_type)
    
    def _calculate_energy_properties(self):
        """Calcule les propriétés énergétiques depuis la config centralisée"""
        type_config = MalaysiaConfig.get_building_type_config(self.building_type)
        self.base_consumption_kwh_m2_day = type_config['base_consumption_kwh_m2_day']
        self.base_water_consumption_l_m2_day = type_config['base_water_consumption_l_m2_day']
    
    def calculate_daily_consumption(self) -> float:
        """
        Calcule la consommation journalière électrique de base en kWh
        
        Returns:
            float: Consommation journalière en kWh
        """
        base_consumption = self.base_consumption_kwh_m2_day * self.surface_area_m2
        
        # Facteur d'efficacité énergétique depuis config
        efficiency_factor = MalaysiaConfig.ENERGY_EFFICIENCY_CLASSES[self.energy_efficiency_class]['factor']
        
        # Facteur nombre d'étages (Malaysia souvent 1-2 étages)
        floors_factor = 1.0 + (self.floors_count - 1) * 0.1
        
        return base_consumption * efficiency_factor * floors_factor
    
    def calculate_daily_water_consumption(self) -> float:
        """
        Calcule la consommation journalière d'eau de base en litres
        
        Returns:
            float: Consommation journalière en litres
        """
        base_water = self.base_water_consumption_l_m2_day * self.surface_area_m2
        
        # Facteur d'efficacité (moins d'impact pour l'eau)
        efficiency_factor = MalaysiaConfig.ENERGY_EFFICIENCY_CLASSES[self.energy_efficiency_class]['factor']
        water_efficiency_factor = 1.0 - ((1.0 - efficiency_factor) * 0.3)  # Impact réduit
        
        # Facteur nombre d'étages
        floors_factor = 1.0 + (self.floors_count - 1) * 0.15  # Plus d'impact pour l'eau
        
        return base_water * water_efficiency_factor * floors_factor
    
    def get_hourly_consumption_profile(self) -> List[float]:
        """
        Retourne le profil de consommation électrique horaire (24h)
        
        Returns:
            List[float]: Facteurs multiplicateurs pour chaque heure (0-23)
        """
        # Récupération des heures d'occupation depuis config
        type_config = MalaysiaConfig.get_building_type_config(self.building_type)
        occupancy_hours = type_config.get('occupancy_hours', (8, 18))
        
        if self.building_type == 'residential':
            # Profil résidentiel Malaysia : pics matin et soir
            profile = [
                0.3, 0.3, 0.3, 0.3, 0.4, 0.6,  # 0-5h: nuit
                1.2, 1.5, 1.0, 0.8, 0.7, 0.8,  # 6-11h: matin
                1.0, 0.9, 0.8, 0.9, 1.0, 1.2,  # 12-17h: après-midi
                1.5, 1.8, 1.6, 1.2, 0.8, 0.5   # 18-23h: soirée
            ]
        elif self.building_type in ['office', 'commercial']:
            # Profil bureau/commercial : heures de travail
            profile = [
                0.1, 0.1, 0.1, 0.1, 0.1, 0.2,  # 0-5h: fermé
                0.5, 1.0, 1.5, 1.8, 1.8, 1.5,  # 6-11h: ouverture
                1.2, 1.5, 1.8, 1.8, 1.5, 1.0,  # 12-17h: activité
                0.8, 0.5, 0.3, 0.2, 0.1, 0.1   # 18-23h: fermeture
            ]
        elif self.building_type == 'industrial':
            # Profil industriel : plus constant
            profile = [
                0.8, 0.8, 0.7, 0.7, 0.8, 1.0,  # 0-5h: garde réduite
                1.3, 1.8, 2.0, 2.0, 1.8, 1.5,  # 6-11h: production
                1.2, 1.5, 1.8, 2.0, 1.8, 1.5,  # 12-17h: production
                1.2, 1.0, 0.9, 0.8, 0.8, 0.8   # 18-23h: réduction
            ]
        elif self.building_type == 'hospital':
            # Profil hôpital : constant 24h/24
            profile = [1.0] * 24
        else:
            # Profil par défaut basé sur les heures d'occupation
            start_hour, end_hour = occupancy_hours
            profile = []
            for hour in range(24):
                if start_hour <= hour <= end_hour:
                    profile.append(1.5)  # Heures actives
                elif hour < start_hour or hour > end_hour + 2:
                    profile.append(0.3)  # Heures creuses
                else:
                    profile.append(0.8)  # Transition
        
        # Normalisation pour que la moyenne soit 1.0
        avg_factor = sum(profile) / len(profile)
        normalized_profile = [f / avg_factor for f in profile]
        
        return normalized_profile
    
    def get_water_hourly_profile(self) -> List[float]:
        """
        Retourne le profil de consommation d'eau horaire (24h)
        
        Returns:
            List[float]: Facteurs multiplicateurs pour chaque heure (0-23)
        """
        if self.building_type == 'residential':
            # Profil eau résidentiel : pics matin, midi, soir
            profile = [
                0.2, 0.2, 0.1, 0.1, 0.2, 0.5,  # 0-5h: nuit
                2.0, 2.5, 1.5, 1.0, 0.8, 1.5,  # 6-11h: matin + douches
                2.0, 1.5, 1.0, 1.0, 1.2, 1.5,  # 12-17h: midi + après-midi
                2.2, 2.0, 1.8, 1.2, 0.8, 0.5   # 18-23h: soirée + bains
            ]
        elif self.building_type in ['office', 'commercial']:
            # Usage eau bureaux : constant pendant heures travail
            profile = [
                0.1, 0.1, 0.1, 0.1, 0.1, 0.1,  # 0-5h: fermé
                0.5, 1.0, 1.5, 1.8, 1.8, 2.0,  # 6-11h: ouverture
                1.5, 1.8, 1.8, 1.5, 1.2, 1.0,  # 12-17h: activité
                0.5, 0.2, 0.1, 0.1, 0.1, 0.1   # 18-23h: fermeture
            ]
        elif self.building_type == 'hospital':
            # Hôpital : consommation eau plus constante 24h/24
            import math
            profile = [1.0 + 0.3 * math.sin((hour - 6) * math.pi / 12) for hour in range(24)]
        else:
            # Profil par défaut
            profile = [0.5, 0.4, 0.3, 0.3, 0.4, 0.8,
                      1.5, 1.8, 1.5, 1.2, 1.0, 1.3,
                      1.5, 1.2, 1.0, 1.2, 1.5, 1.8,
                      1.5, 1.2, 1.0, 0.8, 0.6, 0.5]
        
        # Normalisation
        avg_factor = sum(profile) / len(profile)
        normalized_profile = [f / avg_factor for f in profile]
        
        return normalized_profile
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour export"""
        return {
            'id': self.id,
            'osm_id': self.osm_id,
            'building_type': self.building_type,
            'latitude': round(self.latitude, 6),
            'longitude': round(self.longitude, 6),
            'zone_name': self.zone_name,
            'surface_area_m2': round(self.surface_area_m2, 1),
            'floors_count': self.floors_count,
            'energy_efficiency_class': self.energy_efficiency_class,
            'daily_consumption_kwh': round(self.calculate_daily_consumption(), 2),
            'daily_water_consumption_l': round(self.calculate_daily_water_consumption(), 1),
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_osm_data(cls, osm_element, zone_name: str) -> 'Building':
        """
        Crée un Building depuis des données OSM
        UTILISE LES HELPERS CENTRALISÉS
        
        Args:
            osm_element: Élément OSM avec tags et géométrie
            zone_name: Nom de la zone Malaysia
            
        Returns:
            Building: Instance créée
        """
        # Extraction des tags
        tags = getattr(osm_element, 'tags', {})
        osm_id = getattr(osm_element, 'id', None)
        
        # Détermination du type de bâtiment (utilise helper centralisé)
        building_type = normalize_building_type(tags.get('building', ''))
        
        # Calcul géométrie (utilise helper centralisé)
        coords, surface_area = cls._extract_geometry_from_osm(osm_element)
        
        # Génération ID (utilise helper centralisé)
        building_id = generate_building_id(building_type, zone_name)
        
        return cls(
            id=building_id,
            osm_id=str(osm_id) if osm_id else None,
            latitude=coords[0],
            longitude=coords[1],
            zone_name=zone_name,
            building_type=building_type,
            surface_area_m2=surface_area,
            osm_tags=tags,
            source='openstreetmap'
        )
    
    @staticmethod
    def _extract_geometry_from_osm(osm_element) -> Tuple[Tuple[float, float], float]:
        """Extrait coordonnées et surface depuis un élément OSM"""
        try:
            if hasattr(osm_element, 'geometry') and osm_element.geometry:
                coords_list = []
                
                for geom in osm_element.geometry:
                    if hasattr(geom, 'lat') and hasattr(geom, 'lon'):
                        coords_list.append((geom.lat, geom.lon))
                
                if coords_list:
                    # Centre géométrique
                    center_lat = sum(c[0] for c in coords_list) / len(coords_list)
                    center_lon = sum(c[1] for c in coords_list) / len(coords_list)
                    
                    # Surface approximative (utilise helper centralisé)
                    surface_area = calculate_approximate_area(coords_list)
                    
                    return (center_lat, center_lon), surface_area
            
            # Valeurs par défaut si pas de géométrie
            kl_coords = MalaysiaConfig.MAJOR_CITIES['kuala_lumpur']
            return (kl_coords['lat'], kl_coords['lon']), 100.0
            
        except Exception:
            kl_coords = MalaysiaConfig.MAJOR_CITIES['kuala_lumpur']
            return (kl_coords['lat'], kl_coords['lon']), 100.0


# ==============================================================================
# FONCTIONS UTILITAIRES BUILDING (optimisées)
# ==============================================================================

def create_building_from_coordinates(
    latitude: float,
    longitude: float,
    building_type: str = 'residential',
    surface_area_m2: float = 100.0,
    zone_name: str = 'unknown'
) -> Building:
    """
    Crée un Building depuis des coordonnées
    UTILISE LES HELPERS CENTRALISÉS
    """
    building_id = generate_building_id(building_type, zone_name)
    
    return Building(
        id=building_id,
        latitude=latitude,
        longitude=longitude,
        building_type=building_type,
        surface_area_m2=surface_area_m2,
        zone_name=zone_name,
        source='manual'
    )


def validate_building_list(buildings: List[Building]) -> Dict:
    """
    Valide une liste de bâtiments
    VERSION SIMPLIFIÉE - Utilise validators centralisés
    """
    from src.utils.validators import validate_building_list as validate_building_dict_list
    
    # Conversion en dictionnaires pour validation
    buildings_dicts = [building.to_dict() for building in buildings]
    
    return validate_building_dict_list(buildings_dicts)


def create_building_from_type_config(building_type: str, zone_name: str = 'unknown') -> Building:
    """
    Crée un Building prototype basé sur la configuration du type
    
    Args:
        building_type: Type de bâtiment
        zone_name: Nom de la zone
        
    Returns:
        Building: Building prototype
    """
    type_config = MalaysiaConfig.get_building_type_config(building_type)
    typical_size = type_config.get('typical_size_m2', (100, 100))
    
    # Surface moyenne du type
    avg_surface = sum(typical_size) / 2
    
    # Coordonnées par défaut (centre Malaysia approximatif)
    default_coords = MalaysiaConfig.MAJOR_CITIES['kuala_lumpur']
    
    building_id = generate_building_id(building_type, zone_name)
    
    return Building(
        id=building_id,
        latitude=default_coords['lat'],
        longitude=default_coords['lon'],
        building_type=building_type,
        surface_area_m2=avg_surface,
        zone_name=zone_name,
        source='prototype'
    )


def analyze_building_energy_potential(building: Building) -> Dict:
    """
    Analyse le potentiel énergétique d'un bâtiment
    
    Args:
        building: Bâtiment à analyser
        
    Returns:
        Dict: Analyse énergétique complète
    """
    daily_electricity = building.calculate_daily_consumption()
    daily_water = building.calculate_daily_water_consumption()
    
    # Intensités
    electricity_intensity = daily_electricity / building.surface_area_m2
    water_intensity = daily_water / building.surface_area_m2
    
    # Comparaison avec moyennes du type
    type_config = MalaysiaConfig.get_building_type_config(building.building_type)
    base_electricity = type_config['base_consumption_kwh_m2_day']
    base_water = type_config['base_water_consumption_l_m2_day']
    
    # Ratios par rapport aux standards
    electricity_ratio = electricity_intensity / base_electricity
    water_ratio = water_intensity / base_water
    
    # Classification énergétique
    if electricity_ratio < 0.8:
        electricity_class = 'Très efficient'
    elif electricity_ratio < 1.0:
        electricity_class = 'Efficient'
    elif electricity_ratio < 1.2:
        electricity_class = 'Standard'
    else:
        electricity_class = 'Peu efficient'
    
    # Estimations annuelles
    annual_electricity = daily_electricity * 365
    annual_water = daily_water * 365
    
    return {
        'building_id': building.id,
        'building_type': building.building_type,
        'surface_area_m2': building.surface_area_m2,
        'energy_efficiency_class': building.energy_efficiency_class,
        'daily_consumption': {
            'electricity_kwh': round(daily_electricity, 2),
            'water_liters': round(daily_water, 1)
        },
        'annual_consumption': {
            'electricity_kwh': round(annual_electricity, 0),
            'water_liters': round(annual_water, 0)
        },
        'intensity': {
            'electricity_kwh_m2_day': round(electricity_intensity, 3),
            'water_l_m2_day': round(water_intensity, 1)
        },
        'comparison_to_standards': {
            'electricity_ratio': round(electricity_ratio, 2),
            'water_ratio': round(water_ratio, 2),
            'electricity_classification': electricity_class
        },
        'optimization_potential': {
            'electricity_savings_percent': max(0, (electricity_ratio - 0.7) * 100 / electricity_ratio),
            'water_savings_percent': max(0, (water_ratio - 0.8) * 100 / water_ratio)
        }
    }


def get_building_type_statistics(buildings: List[Building]) -> Dict:
    """
    Calcule les statistiques par type de bâtiment
    
    Args:
        buildings: Liste des bâtiments
        
    Returns:
        Dict: Statistiques par type
    """
    if not buildings:
        return {}
    
    type_stats = {}
    
    for building in buildings:
        btype = building.building_type
        
        if btype not in type_stats:
            type_stats[btype] = {
                'count': 0,
                'total_surface_m2': 0,
                'total_daily_electricity': 0,
                'total_daily_water': 0,
                'buildings': []
            }
        
        stats = type_stats[btype]
        stats['count'] += 1
        stats['total_surface_m2'] += building.surface_area_m2
        stats['total_daily_electricity'] += building.calculate_daily_consumption()
        stats['total_daily_water'] += building.calculate_daily_water_consumption()
        stats['buildings'].append(building.id)
    
    # Calcul des moyennes
    for btype, stats in type_stats.items():
        count = stats['count']
        if count > 0:
            stats['average_surface_m2'] = round(stats['total_surface_m2'] / count, 1)
            stats['average_daily_electricity'] = round(stats['total_daily_electricity'] / count, 2)
            stats['average_daily_water'] = round(stats['total_daily_water'] / count, 1)
            stats['electricity_intensity'] = round(stats['total_daily_electricity'] / stats['total_surface_m2'], 3)
            stats['water_intensity'] = round(stats['total_daily_water'] / stats['total_surface_m2'], 1)
        
        # Nettoyage pour export
        stats.pop('buildings', None)  # Evite les listes trop longues
    
    return type_stats


def generate_building_summary_report(buildings: List[Building]) -> Dict:
    """
    Génère un rapport de synthèse des bâtiments
    
    Args:
        buildings: Liste des bâtiments
        
    Returns:
        Dict: Rapport complet
    """
    if not buildings:
        return {'error': 'Aucun bâtiment à analyser'}
    
    # Statistiques générales
    total_count = len(buildings)
    total_surface = sum(b.surface_area_m2 for b in buildings)
    total_daily_electricity = sum(b.calculate_daily_consumption() for b in buildings)
    total_daily_water = sum(b.calculate_daily_water_consumption() for b in buildings)
    
    # Répartition par zone
    zone_distribution = {}
    for building in buildings:
        zone = building.zone_name or 'unknown'
        zone_distribution[zone] = zone_distribution.get(zone, 0) + 1
    
    # Répartition par classe d'efficacité
    efficiency_distribution = {}
    for building in buildings:
        eff_class = building.energy_efficiency_class
        efficiency_distribution[eff_class] = efficiency_distribution.get(eff_class, 0) + 1
    
    # Statistiques par type
    type_statistics = get_building_type_statistics(buildings)
    
    # Ranges et moyennes
    surfaces = [b.surface_area_m2 for b in buildings]
    electricities = [b.calculate_daily_consumption() for b in buildings]
    
    return {
        'overview': {
            'total_buildings': total_count,
            'total_surface_m2': round(total_surface, 1),
            'average_surface_m2': round(total_surface / total_count, 1),
            'surface_range': {
                'min': round(min(surfaces), 1),
                'max': round(max(surfaces), 1)
            }
        },
        'energy_summary': {
            'total_daily_electricity_kwh': round(total_daily_electricity, 1),
            'total_daily_water_liters': round(total_daily_water, 0),
            'average_daily_electricity_kwh': round(total_daily_electricity / total_count, 2),
            'average_daily_water_liters': round(total_daily_water / total_count, 1),
            'total_annual_electricity_mwh': round(total_daily_electricity * 365 / 1000, 1),
            'electricity_intensity_kwh_m2_day': round(total_daily_electricity / total_surface, 3),
            'water_intensity_l_m2_day': round(total_daily_water / total_surface, 1)
        },
        'distributions': {
            'by_type': {btype: stats['count'] for btype, stats in type_statistics.items()},
            'by_zone': zone_distribution,
            'by_efficiency_class': efficiency_distribution
        },
        'type_statistics': type_statistics,
        'generated_at': datetime.now().isoformat(),
        'report_version': '3.0.0'
    }