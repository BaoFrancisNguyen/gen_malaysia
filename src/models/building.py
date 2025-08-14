    def _calculate_energy_properties(self):
        """Calcule les propriétés énergétiques basées sur le type"""
        # Import local pour éviter la circularité
        type_config = self._get_building_type_config(self.building_type)
        self.base_consumption_kwh_m2_day = type_config['base_consumption_kwh_m2_day']
    
    def _get_building_type_config(self, building_type: str) -> Dict:
        """Obtient la configuration d'un type de bâtiment"""
        # Configuration locale pour éviter l'import circulaire
        BUILDING_TYPES_CONFIG = {
            'residential': {'base_consumption_kwh_m2_day': 0.8},
            'commercial': {'base_consumption_kwh_m2_day': 1.5},
            'office': {'base_consumption_kwh_m2_day': 2.0},
            'industrial': {'base_consumption_kwh_m2_day': 3.5},
            'school': {'base_consumption_kwh_m2_day': 1.2},
            'hospital': {'base_consumption_kwh_m2_day': 4.0}
        }
        return BUILDING_TYPES_CONFIG.get(building_type, BUILDING_TYPES_CONFIG['residential'])
    
    def _normalize_building#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODÈLE BUILDING - STRUCTURES DE DONNÉES
========================================

Modèle de données pour les bâtiments Malaysia avec propriétés énergétiques.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class Building:
    """
    Modèle de données pour un bâtiment avec propriétés énergétiques
    
    Représente un bâtiment avec toutes ses caractéristiques
    nécessaires pour la génération de données électriques.
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
    
    # Propriétés énergétiques
    energy_efficiency_class: str = 'C'  # A, B, C, D, E
    base_consumption_kwh_m2_day: float = 1.0
    heating_type: str = 'none'  # none, electric, gas (Malaysia = tropical)
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
        self._calculate_energy_properties()
        self._normalize_building_type()
    
    def _validate_coordinates(self):
        """Valide que les coordonnées sont dans les limites Malaysia"""
        if not (0.5 <= self.latitude <= 7.5 and 99.5 <= self.longitude <= 119.5):
            raise ValueError(f"Coordonnées hors Malaysia: {self.latitude}, {self.longitude}")
    
    def _calculate_energy_properties(self):
        """Calcule les propriétés énergétiques basées sur le type"""
        from config import MalaysiaConfig
        
        type_config = MalaysiaConfig.get_building_type_config(self.building_type)
        self.base_consumption_kwh_m2_day = type_config['base_consumption_kwh_m2_day']
    
    def _normalize_building_type(self):
        """Normalise le type de bâtiment"""
        # Normalisation locale pour éviter l'import circulaire
        if not self.building_type:
            self.building_type = 'residential'
            return
        
        raw_lower = self.building_type.lower()
        
        # Mapping local
        type_mapping = {
            'house': 'residential',
            'apartment': 'residential', 
            'flat': 'residential',
            'terrace': 'residential',
            'shop': 'commercial',
            'retail': 'commercial',
            'mall': 'commercial',
            'store': 'commercial',
            'office': 'office',
            'government': 'office',
            'civic': 'office',
            'factory': 'industrial',
            'warehouse': 'industrial',
            'industrial': 'industrial',
            'school': 'school',
            'university': 'school',
            'college': 'school',
            'hospital': 'hospital',
            'clinic': 'hospital',
            'healthcare': 'hospital'
        }
        
        for key, normalized_type in type_mapping.items():
            if key in raw_lower:
                self.building_type = normalized_type
                return
        
        # Garder le type original s'il est valide
        valid_types = ['residential', 'commercial', 'office', 'industrial', 'school', 'hospital']
        if self.building_type not in valid_types:
            self.building_type = 'residential'
    
    def calculate_daily_consumption(self) -> float:
        """
        Calcule la consommation journalière de base en kWh
        
        Returns:
            float: Consommation journalière en kWh
        """
        base_consumption = self.base_consumption_kwh_m2_day * self.surface_area_m2
        
        # Facteur d'efficacité énergétique
        efficiency_factors = {
            'A': 0.7, 'B': 0.85, 'C': 1.0, 'D': 1.15, 'E': 1.3
        }
        efficiency_factor = efficiency_factors.get(self.energy_efficiency_class, 1.0)
        
        # Facteur nombre d'étages (Malaysia souvent 1-2 étages)
        floors_factor = 1.0 + (self.floors_count - 1) * 0.1
        
        return base_consumption * efficiency_factor * floors_factor
    
    def get_hourly_consumption_profile(self) -> List[float]:
        """
        Retourne le profil de consommation horaire (24h) pour ce type de bâtiment
        
        Returns:
            List[float]: Facteurs multiplicateurs pour chaque heure (0-23)
        """
        daily_consumption = self.calculate_daily_consumption()
        
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
            # Profil par défaut
            profile = [0.8, 0.7, 0.6, 0.6, 0.7, 0.9,
                      1.2, 1.4, 1.3, 1.1, 1.0, 1.1,
                      1.2, 1.1, 1.0, 1.1, 1.2, 1.3,
                      1.4, 1.3, 1.2, 1.1, 1.0, 0.9]
        
        # Normalisation pour que la moyenne soit 1.0
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
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_osm_data(cls, osm_element, zone_name: str) -> 'Building':
        """
        Crée un Building depuis des données OSM
        
        Args:
            osm_element: Élément OSM avec tags et géométrie
            zone_name: Nom de la zone Malaysia
            
        Returns:
            Building: Instance créée
        """
        from src.utils.helpers import generate_building_id, calculate_approximate_area
        
        # Extraction des tags
        tags = getattr(osm_element, 'tags', {})
        osm_id = getattr(osm_element, 'id', None)
        
        # Détermination du type de bâtiment
        building_type = cls._determine_building_type_from_tags(tags)
        
        # Calcul géométrie
        coords, surface_area = cls._extract_geometry_from_osm(osm_element)
        
        # Génération ID
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
    def _determine_building_type_from_tags(tags: Dict) -> str:
        """Détermine le type de bâtiment depuis les tags OSM"""
        building_tag = tags.get('building', '').lower()
        amenity_tag = tags.get('amenity', '').lower()
        landuse_tag = tags.get('landuse', '').lower()
        
        # Mapping vers nos types
        if any(t in building_tag + amenity_tag for t in ['house', 'residential', 'apartment']):
            return 'residential'
        elif any(t in building_tag + amenity_tag for t in ['commercial', 'shop', 'retail', 'mall']):
            return 'commercial'
        elif any(t in building_tag + amenity_tag for t in ['office', 'government', 'civic']):
            return 'office'
        elif any(t in building_tag + amenity_tag for t in ['industrial', 'factory', 'warehouse']):
            return 'industrial'
        elif any(t in building_tag + amenity_tag for t in ['school', 'university', 'college']):
            return 'school'
        elif any(t in building_tag + amenity_tag for t in ['hospital', 'clinic', 'healthcare']):
            return 'hospital'
        else:
            return 'residential'  # Par défaut
    
    @staticmethod
    def _extract_geometry_from_osm(osm_element) -> Tuple[Tuple[float, float], float]:
        """Extrait coordonnées et surface depuis un élément OSM"""
        from src.utils.helpers import calculate_approximate_area
        
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
                    
                    # Surface approximative
                    surface_area = calculate_approximate_area(coords_list)
                    
                    return (center_lat, center_lon), surface_area
            
            # Valeurs par défaut si pas de géométrie
            return (3.1390, 101.6869), 100.0  # Centre KL, 100m²
            
        except Exception:
            return (3.1390, 101.6869), 100.0


# ==============================================================================
# FONCTIONS UTILITAIRES
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
    
    Args:
        latitude: Latitude
        longitude: Longitude
        building_type: Type de bâtiment
        surface_area_m2: Surface en m²
        zone_name: Nom de la zone
        
    Returns:
        Building: Instance créée
    """
    from src.utils.helpers import generate_building_id
    
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
    
    Args:
        buildings: Liste des bâtiments à valider
        
    Returns:
        Dict: Résultat de validation
    """
    if not buildings:
        return {'valid': False, 'error': 'Liste vide'}
    
    errors = []
    warnings = []
    
    for i, building in enumerate(buildings):
        try:
            # Validation coordonnées
            if not (0.5 <= building.latitude <= 7.5 and 
                   99.5 <= building.longitude <= 119.5):
                errors.append(f"Bâtiment {i}: coordonnées hors Malaysia")
            
            # Validation surface
            if building.surface_area_m2 <= 0:
                errors.append(f"Bâtiment {i}: surface invalide")
            elif building.surface_area_m2 < 10:
                warnings.append(f"Bâtiment {i}: surface très petite")
            
            # Validation type
            from config import MalaysiaConfig
            if building.building_type not in MalaysiaConfig.BUILDING_TYPES:
                errors.append(f"Bâtiment {i}: type invalide")
                
        except Exception as e:
            errors.append(f"Bâtiment {i}: erreur validation - {e}")
    
    return {
        'valid': len(errors) == 0,
        'total_buildings': len(buildings),
        'errors': errors,
        'warnings': warnings
    }