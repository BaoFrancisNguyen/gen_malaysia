#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODÈLE TIMESERIES - STRUCTURES DE DONNÉES
==========================================

Modèle de données pour les séries temporelles électriques avec métadonnées.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union
import pandas as pd


@dataclass
class TimeSeries:
    """
    Modèle de données pour un point temporel de consommation électrique
    
    Représente une observation de consommation électrique à un moment donné
    avec toutes les métadonnées contextuelles nécessaires.
    """
    
    # Identifiants et timestamp
    building_id: str
    timestamp: pd.Timestamp
    
    # Données de consommation électrique
    consumption_kwh: float
    
    # Métadonnées du bâtiment
    building_type: str
    surface_area_m2: float
    zone_name: Optional[str] = None
    
    # Données contextuelles calculées
    hour: Optional[int] = None
    day_of_week: Optional[int] = None
    month: Optional[int] = None
    is_weekend: Optional[bool] = None
    is_business_hour: Optional[bool] = None
    
    # Données de qualité
    data_quality_score: Optional[float] = None
    anomaly_flag: Optional[bool] = None
    
    # Métadonnées de génération
    generation_session_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Calculs automatiques après création de l'instance"""
        self._calculate_temporal_flags()
        self._calculate_quality_score()
        self._detect_anomalies()
        
        if not self.created_at:
            self.created_at = datetime.now()
    
    def _calculate_temporal_flags(self):
        """Calcule les flags temporels basés sur le timestamp"""
        if isinstance(self.timestamp, pd.Timestamp):
            self.hour = self.timestamp.hour
            self.day_of_week = self.timestamp.dayofweek
            self.month = self.timestamp.month
            self.is_weekend = self.timestamp.dayofweek >= 5
            self.is_business_hour = 8 <= self.timestamp.hour <= 18
    
    def _calculate_quality_score(self):
        """Calcule un score de qualité des données (0-1)"""
        score = 1.0
        
        # Pénalités pour valeurs suspectes
        if self.consumption_kwh < 0:
            score -= 0.5  # Consommation négative très suspecte
        elif self.consumption_kwh == 0:
            score -= 0.2  # Consommation nulle suspecte
        
        # Vérification cohérence consommation/surface
        if self.surface_area_m2 > 0:
            consumption_per_m2 = self.consumption_kwh / self.surface_area_m2
            if consumption_per_m2 > 1.0:  # Plus de 1 kWh/m²/h = très élevé
                score -= 0.2
            elif consumption_per_m2 < 0.001:  # Moins de 1 Wh/m²/h = très faible
                score -= 0.1
        
        # Vérification cohérence type bâtiment / heure
        if self.building_type in ['office', 'commercial'] and self.hour is not None:
            if 2 <= self.hour <= 5 and self.consumption_kwh > 0.1:
                score -= 0.1  # Consommation élevée la nuit pour bureau
        
        self.data_quality_score = max(0.0, min(1.0, score))
    
    def _detect_anomalies(self):
        """Détecte les anomalies dans les données"""
        anomalies = []
        
        # Consommation négative
        if self.consumption_kwh < 0:
            anomalies.append('negative_consumption')
        
        # Consommation extrêmement élevée
        if self.consumption_kwh > 100:  # Plus de 100 kWh/h
            anomalies.append('extremely_high_consumption')
        
        # Consommation incohérente avec le type de bâtiment
        if self.building_type == 'residential' and self.consumption_kwh > 20:
            anomalies.append('high_residential_consumption')
        elif self.building_type == 'industrial' and self.consumption_kwh < 0.1:
            anomalies.append('low_industrial_consumption')
        
        self.anomaly_flag = len(anomalies) > 0
    
    def get_consumption_intensity(self) -> float:
        """
        Calcule l'intensité de consommation en kWh/m²
        
        Returns:
            float: Intensité de consommation
        """
        if self.surface_area_m2 <= 0:
            return 0.0
        return self.consumption_kwh / self.surface_area_m2
    
    def is_peak_hour(self) -> bool:
        """
        Détermine si c'est une heure de pointe selon le type de bâtiment
        
        Returns:
            bool: True si heure de pointe
        """
        if self.hour is None:
            return False
        
        if self.building_type == 'residential':
            # Pointes résidentielles: matin et soir
            return (6 <= self.hour <= 8) or (18 <= self.hour <= 22)
        elif self.building_type in ['office', 'commercial']:
            # Pointe bureaux: heures de travail
            return 9 <= self.hour <= 17
        elif self.building_type == 'industrial':
            # Pointe industrielle: journée de travail
            return 7 <= self.hour <= 19
        else:
            # Pointe générale
            return 8 <= self.hour <= 20
    
    def get_load_factor(self) -> str:
        """
        Classe la charge électrique
        
        Returns:
            str: Classe de charge ('base', 'medium', 'peak')
        """
        if self.building_type == 'residential':
            if self.consumption_kwh < 0.5:
                return 'base'
            elif self.consumption_kwh < 2.0:
                return 'medium'
            else:
                return 'peak'
        elif self.building_type in ['office', 'commercial']:
            if self.consumption_kwh < 1.0:
                return 'base'
            elif self.consumption_kwh < 5.0:
                return 'medium'
            else:
                return 'peak'
        else:  # industrial, hospital, etc.
            if self.consumption_kwh < 2.0:
                return 'base'
            elif self.consumption_kwh < 10.0:
                return 'medium'
            else:
                return 'peak'
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour export"""
        return {
            'building_id': self.building_id,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, pd.Timestamp) else str(self.timestamp),
            'consumption_kwh': round(self.consumption_kwh, 4),
            'building_type': self.building_type,
            'surface_area_m2': round(self.surface_area_m2, 1),
            'zone_name': self.zone_name,
            'hour': self.hour,
            'day_of_week': self.day_of_week,
            'month': self.month,
            'is_weekend': self.is_weekend,
            'is_business_hour': self.is_business_hour,
            'is_peak_hour': self.is_peak_hour(),
            'load_factor': self.get_load_factor(),
            'consumption_intensity_kwh_m2': round(self.get_consumption_intensity(), 6),
            'data_quality_score': round(self.data_quality_score, 3) if self.data_quality_score else None,
            'anomaly_flag': self.anomaly_flag,
            'generation_session_id': self.generation_session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TimeSeries':
        """
        Crée une instance depuis un dictionnaire
        
        Args:
            data: Dictionnaire de données
            
        Returns:
            TimeSeries: Instance créée
        """
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            building_id=data['building_id'],
            timestamp=timestamp,
            consumption_kwh=float(data['consumption_kwh']),
            building_type=data['building_type'],
            surface_area_m2=float(data['surface_area_m2']),
            zone_name=data.get('zone_name'),
            generation_session_id=data.get('generation_session_id'),
            created_at=created_at
        )


# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def timeseries_to_dataframe(timeseries_list: List[TimeSeries]) -> pd.DataFrame:
    """
    Convertit une liste de TimeSeries en DataFrame
    
    Args:
        timeseries_list: Liste des objets TimeSeries
        
    Returns:
        pd.DataFrame: DataFrame des séries temporelles
    """
    if not timeseries_list:
        return pd.DataFrame()
    
    # Conversion en dictionnaires
    data_dicts = [ts.to_dict() for ts in timeseries_list]
    
    # Création DataFrame
    df = pd.DataFrame(data_dicts)
    
    # Optimisation des types
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Tri par timestamp et building_id
    if not df.empty and 'timestamp' in df.columns and 'building_id' in df.columns:
        df = df.sort_values(['building_id', 'timestamp']).reset_index(drop=True)
    
    return df


def dataframe_to_timeseries(df: pd.DataFrame) -> List[TimeSeries]:
    """
    Convertit un DataFrame en liste de TimeSeries
    
    Args:
        df: DataFrame à convertir
        
    Returns:
        List[TimeSeries]: Liste des objets TimeSeries
    """
    if df.empty:
        return []
    
    timeseries_list = []
    
    for _, row in df.iterrows():
        try:
            ts = TimeSeries.from_dict(row.to_dict())
            timeseries_list.append(ts)
        except Exception as e:
            # Log l'erreur mais continue
            import logging
            logging.warning(f"Erreur conversion ligne en TimeSeries: {e}")
            continue
    
    return timeseries_list


def validate_timeseries_data(timeseries_list: List[TimeSeries]) -> Dict:
    """
    Valide une liste de données TimeSeries
    
    Args:
        timeseries_list: Liste des TimeSeries à valider
        
    Returns:
        Dict: Résultat de validation avec statistiques
    """
    if not timeseries_list:
        return {
            'valid': False,
            'error': 'Liste vide',
            'total_points': 0
        }
    
    errors = []
    warnings = []
    quality_scores = []
    anomaly_count = 0
    
    for i, ts in enumerate(timeseries_list):
        # Validation consommation
        if ts.consumption_kwh < 0:
            errors.append(f"Point {i}: consommation négative")
        elif ts.consumption_kwh > 1000:  # Plus de 1000 kWh/h
            warnings.append(f"Point {i}: consommation très élevée")
        
        # Validation surface
        if ts.surface_area_m2 <= 0:
            errors.append(f"Point {i}: surface invalide")
        
        # Validation building_id
        if not ts.building_id or len(ts.building_id) < 3:
            errors.append(f"Point {i}: building_id invalide")
        
        # Collecte des scores de qualité
        if ts.data_quality_score is not None:
            quality_scores.append(ts.data_quality_score)
        
        # Comptage des anomalies
        if ts.anomaly_flag:
            anomaly_count += 1
    
    # Calcul des statistiques
    total_points = len(timeseries_list)
    avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    anomaly_percentage = (anomaly_count / total_points) * 100 if total_points > 0 else 0
    
    # Calcul des statistiques de consommation
    consumptions = [ts.consumption_kwh for ts in timeseries_list]
    consumption_stats = {
        'mean': sum(consumptions) / len(consumptions),
        'min': min(consumptions),
        'max': max(consumptions),
        'total': sum(consumptions)
    }
    
    return {
        'valid': len(errors) == 0,
        'total_points': total_points,
        'errors': errors[:10],  # Limite aux 10 premiers
        'warnings': warnings[:10],
        'quality_statistics': {
            'average_quality_score': round(avg_quality_score, 3),
            'anomaly_count': anomaly_count,
            'anomaly_percentage': round(anomaly_percentage, 2)
        },
        'consumption_statistics': {
            'mean_kwh': round(consumption_stats['mean'], 4),
            'min_kwh': round(consumption_stats['min'], 4),
            'max_kwh': round(consumption_stats['max'], 4),
            'total_kwh': round(consumption_stats['total'], 2)
        }
    }


def aggregate_timeseries_by_hour(timeseries_list: List[TimeSeries]) -> Dict:
    """
    Agrège les données TimeSeries par heure
    
    Args:
        timeseries_list: Liste des TimeSeries
        
    Returns:
        Dict: Données agrégées par heure (0-23)
    """
    if not timeseries_list:
        return {}
    
    hourly_data = {}
    
    for ts in timeseries_list:
        if ts.hour is not None:
            hour = ts.hour
            if hour not in hourly_data:
                hourly_data[hour] = {
                    'total_consumption': 0.0,
                    'count': 0,
                    'building_types': set()
                }
            
            hourly_data[hour]['total_consumption'] += ts.consumption_kwh
            hourly_data[hour]['count'] += 1
            hourly_data[hour]['building_types'].add(ts.building_type)
    
    # Calcul des moyennes
    for hour in hourly_data:
        data = hourly_data[hour]
        data['average_consumption'] = data['total_consumption'] / data['count']
        data['building_types'] = list(data['building_types'])
    
    return hourly_data


def aggregate_timeseries_by_building_type(timeseries_list: List[TimeSeries]) -> Dict:
    """
    Agrège les données TimeSeries par type de bâtiment
    
    Args:
        timeseries_list: Liste des TimeSeries
        
    Returns:
        Dict: Données agrégées par type de bâtiment
    """
    if not timeseries_list:
        return {}
    
    type_data = {}
    
    for ts in timeseries_list:
        btype = ts.building_type
        if btype not in type_data:
            type_data[btype] = {
                'total_consumption': 0.0,
                'total_surface': 0.0,
                'count': 0,
                'buildings': set()
            }
        
        type_data[btype]['total_consumption'] += ts.consumption_kwh
        type_data[btype]['total_surface'] += ts.surface_area_m2
        type_data[btype]['count'] += 1
        type_data[btype]['buildings'].add(ts.building_id)
    
    # Calcul des moyennes et intensités
    for btype in type_data:
        data = type_data[btype]
        data['average_consumption'] = data['total_consumption'] / data['count']
        data['consumption_intensity'] = data['total_consumption'] / data['total_surface'] if data['total_surface'] > 0 else 0
        data['unique_buildings'] = len(data['buildings'])
        data['buildings'] = list(data['buildings'])
    
    return type_data


def filter_timeseries_by_period(
    timeseries_list: List[TimeSeries],
    start_hour: int = 0,
    end_hour: int = 23,
    weekdays_only: bool = False
) -> List[TimeSeries]:
    """
    Filtre les TimeSeries selon une période
    
    Args:
        timeseries_list: Liste des TimeSeries
        start_hour: Heure de début (0-23)
        end_hour: Heure de fin (0-23)
        weekdays_only: Si True, garde seulement les jours de semaine
        
    Returns:
        List[TimeSeries]: TimeSeries filtrées
    """
    filtered = []
    
    for ts in timeseries_list:
        # Filtre par heure
        if ts.hour is not None:
            if not (start_hour <= ts.hour <= end_hour):
                continue
        
        # Filtre par jour de semaine
        if weekdays_only and ts.is_weekend:
            continue
        
        filtered.append(ts)
    
    return filtered


def calculate_load_duration_curve(timeseries_list: List[TimeSeries]) -> List[float]:
    """
    Calcule la courbe de charge classée
    
    Args:
        timeseries_list: Liste des TimeSeries
        
    Returns:
        List[float]: Consommations triées par ordre décroissant
    """
    if not timeseries_list:
        return []
    
    consumptions = [ts.consumption_kwh for ts in timeseries_list]
    return sorted(consumptions, reverse=True)


def detect_consumption_patterns(timeseries_list: List[TimeSeries]) -> Dict:
    """
    Détecte les patterns de consommation
    
    Args:
        timeseries_list: Liste des TimeSeries
        
    Returns:
        Dict: Patterns détectés
    """
    if not timeseries_list:
        return {}
    
    patterns = {
        'peak_hours': [],
        'off_peak_hours': [],
        'highest_consumption_day': None,
        'lowest_consumption_day': None,
        'weekend_vs_weekday_ratio': 0.0
    }
    
    # Agrégation par heure
    hourly_agg = aggregate_timeseries_by_hour(timeseries_list)
    
    if hourly_agg:
        # Détection des heures de pointe (consommation > moyenne + écart-type)
        hourly_consumptions = [data['average_consumption'] for data in hourly_agg.values()]
        mean_consumption = sum(hourly_consumptions) / len(hourly_consumptions)
        
        # Écart-type simplifié
        variance = sum((x - mean_consumption) ** 2 for x in hourly_consumptions) / len(hourly_consumptions)
        std_dev = variance ** 0.5
        
        peak_threshold = mean_consumption + std_dev
        off_peak_threshold = mean_consumption - std_dev
        
        for hour, data in hourly_agg.items():
            if data['average_consumption'] > peak_threshold:
                patterns['peak_hours'].append(hour)
            elif data['average_consumption'] < off_peak_threshold:
                patterns['off_peak_hours'].append(hour)
    
    # Comparaison weekend vs semaine
    weekday_consumption = []
    weekend_consumption = []
    
    for ts in timeseries_list:
        if ts.is_weekend:
            weekend_consumption.append(ts.consumption_kwh)
        else:
            weekday_consumption.append(ts.consumption_kwh)
    
    if weekday_consumption and weekend_consumption:
        avg_weekday = sum(weekday_consumption) / len(weekday_consumption)
        avg_weekend = sum(weekend_consumption) / len(weekend_consumption)
        patterns['weekend_vs_weekday_ratio'] = avg_weekend / avg_weekday if avg_weekday > 0 else 0
    
    return patterns


def export_timeseries_summary(timeseries_list: List[TimeSeries]) -> Dict:
    """
    Génère un résumé complet des TimeSeries pour export
    
    Args:
        timeseries_list: Liste des TimeSeries
        
    Returns:
        Dict: Résumé complet
    """
    if not timeseries_list:
        return {'error': 'Aucune donnée TimeSeries'}
    
    # Validation
    validation = validate_timeseries_data(timeseries_list)
    
    # Agrégations
    hourly_agg = aggregate_timeseries_by_hour(timeseries_list)
    type_agg = aggregate_timeseries_by_building_type(timeseries_list)
    
    # Patterns
    patterns = detect_consumption_patterns(timeseries_list)
    
    # Statistiques temporelles
    timestamps = [ts.timestamp for ts in timeseries_list if ts.timestamp]
    temporal_stats = {}
    if timestamps:
        temporal_stats = {
            'start_date': min(timestamps).isoformat(),
            'end_date': max(timestamps).isoformat(),
            'duration_hours': (max(timestamps) - min(timestamps)).total_seconds() / 3600,
            'unique_timestamps': len(set(timestamps))
        }
    
    # Résumé des bâtiments
    building_ids = set(ts.building_id for ts in timeseries_list)
    zones = set(ts.zone_name for ts in timeseries_list if ts.zone_name)
    
    summary = {
        'overview': {
            'total_observations': len(timeseries_list),
            'unique_buildings': len(building_ids),
            'unique_zones': len(zones),
            'zones_list': list(zones)
        },
        'temporal_statistics': temporal_stats,
        'validation_results': validation,
        'consumption_patterns': patterns,
        'hourly_aggregation': hourly_agg,
        'building_type_aggregation': type_agg,
        'data_quality': {
            'average_quality_score': validation.get('quality_statistics', {}).get('average_quality_score', 0),
            'anomaly_percentage': validation.get('quality_statistics', {}).get('anomaly_percentage', 0)
        }
    }
    
    return summary