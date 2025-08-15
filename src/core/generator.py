#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÉNÉRATEURS DE DONNÉES - CORE MODULE
====================================

Modules core pour la génération des données électriques, météorologiques et eau.
Séparation claire: ElectricityGenerator, WeatherGenerator, WaterGenerator.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List
import numpy as np
import pandas as pd

from config import MalaysiaConfig, WeatherConfig
from src.utils.helpers import generate_unique_id

logger = logging.getLogger(__name__)


# ==============================================================================
# GÉNÉRATEUR ÉLECTRICITÉ
# ==============================================================================

class ElectricityGenerator:
    """Générateur de données de consommation électrique"""
    
    def __init__(self):
        """Initialise le générateur électrique"""
        self.generation_count = 0
        logger.info("✅ ElectricityGenerator initialisé")
    
    def generate_consumption_timeseries(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H'
    ) -> Dict:
        """
        Génère les séries temporelles de consommation électrique
        
        Args:
            buildings: Liste des bâtiments
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            frequency: Fréquence ('15T', '1H', '3H', 'D')
            
        Returns:
            Dict: Résultat avec DataFrame de consommation
        """
        start_time = time.time()
        self.generation_count += 1
        
        try:
            logger.info(f"⚡ Génération consommation: {len(buildings)} bâtiments")
            logger.info(f"📅 Période: {start_date} → {end_date} ({frequency})")
            
            # Création de l'index temporel
            date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)
            logger.info(f"📊 {len(date_range)} points temporels à générer")
            
            # Génération des données
            consumption_data = []
            
            for building in buildings:
                building_consumption = self._generate_building_consumption_series(
                    building, date_range
                )
                consumption_data.extend(building_consumption)
            
            # Création du DataFrame
            df = pd.DataFrame(consumption_data)
            
            generation_time = time.time() - start_time
            logger.info(f"✅ {len(consumption_data)} points générés en {generation_time:.1f}s")
            
            return {
                'success': True,
                'data': df,
                'metadata': {
                    'total_points': len(consumption_data),
                    'buildings_count': len(buildings),
                    'time_range': f"{start_date} → {end_date}",
                    'frequency': frequency,
                    'generation_time_seconds': generation_time,
                    'generation_id': generate_unique_id('gen')
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération électricité: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_building_consumption_series(
        self, 
        building: Dict, 
        date_range: pd.DatetimeIndex
    ) -> List[Dict]:
        """
        Génère la série de consommation pour un bâtiment
        
        Args:
            building: Données du bâtiment
            date_range: Index temporel
            
        Returns:
            List[Dict]: Points de consommation
        """
        building_type = building.get('building_type', 'residential')
        surface_area = building.get('surface_area_m2', 100)
        building_id = building['id']
        
        # Consommation de base
        base_consumption = self._calculate_base_consumption(building_type, surface_area)
        
        consumption_points = []
        
        for timestamp in date_range:
            # Facteurs de variation
            hour_factor = self._get_hourly_factor(timestamp.hour, building_type)
            day_factor = self._get_daily_factor(timestamp.dayofweek, building_type)
            seasonal_factor = self._get_seasonal_factor(timestamp.month)
            
            # Variation aléatoire réaliste
            random_factor = np.random.normal(1.0, 0.1)
            
            # Consommation finale
            consumption = (base_consumption * 
                          hour_factor * 
                          day_factor * 
                          seasonal_factor * 
                          random_factor)
            
            consumption_points.append({
                'building_id': building_id,
                'timestamp': timestamp,
                'consumption_kwh': max(0, consumption),
                'building_type': building_type,
                'surface_area_m2': surface_area
            })
        
        return consumption_points
    
    def _calculate_base_consumption(self, building_type: str, surface_area: float) -> float:
        """Calcule la consommation de base horaire"""
        config = MalaysiaConfig.get_building_type_config(building_type)
        daily_consumption_m2 = config['base_consumption_kwh_m2_day']
        
        # Conversion en horaire
        hourly_consumption = (daily_consumption_m2 * surface_area) / 24
        return hourly_consumption
    
    def _get_hourly_factor(self, hour: int, building_type: str) -> float:
        """Facteur de variation horaire"""
        if building_type == 'residential':
            # Pics matin et soir
            if 6 <= hour <= 8 or 18 <= hour <= 22:
                return 1.5
            elif 0 <= hour <= 5:
                return 0.3
            else:
                return 1.0
        elif building_type in ['office', 'commercial']:
            # Heures de bureau
            if 8 <= hour <= 18:
                return 1.8
            else:
                return 0.2
        else:
            # Profil plus constant
            return 1.0 + 0.3 * np.sin((hour - 6) * np.pi / 12)
    
    def _get_daily_factor(self, day_of_week: int, building_type: str) -> float:
        """Facteur de variation journalière (0=lundi, 6=dimanche)"""
        if building_type == 'residential':
            return 1.2 if day_of_week >= 5 else 1.0  # Weekend plus élevé
        elif building_type in ['office', 'commercial']:
            return 0.3 if day_of_week >= 5 else 1.0  # Weekend très bas
        else:
            return 1.0  # Constant pour industriel/hôpital
    
    def _get_seasonal_factor(self, month: int) -> float:
        """Facteur saisonnier (climat tropical Malaysia)"""
        # Saison sèche = plus de climatisation
        if 6 <= month <= 8:
            return 1.3
        # Saison des pluies = moins de climatisation
        elif 11 <= month <= 12 or 1 <= month <= 2:
            return 0.9
        else:
            return 1.0


# ==============================================================================
# GÉNÉRATEUR MÉTÉO
# ==============================================================================

class WeatherGenerator:
    """Générateur de données météorologiques pour Malaysia"""
    
    def __init__(self):
        """Initialise le générateur météo"""
        self.generation_count = 0
        logger.info("✅ WeatherGenerator initialisé")
    
    def generate_weather_timeseries(
        self,
        start_date: str,
        end_date: str,
        frequency: str = '1H',
        station_count: int = 5
    ) -> Dict:
        """
        Génère les données météorologiques simulées
        
        Args:
            start_date: Date début
            end_date: Date fin
            frequency: Fréquence des observations
            station_count: Nombre de stations météo
            
        Returns:
            Dict: Résultat avec DataFrame météo
        """
        start_time = time.time()
        self.generation_count += 1
        
        try:
            logger.info(f"🌤️ Génération météo: {station_count} stations")
            logger.info(f"📅 Période: {start_date} → {end_date} ({frequency})")
            
            # Création de l'index temporel
            date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)
            logger.info(f"📊 {len(date_range)} observations par station")
            
            weather_data = []
            
            # Génération pour chaque station
            for station_id in range(1, station_count + 1):
                station_data = self._generate_station_weather_series(date_range, station_id)
                weather_data.extend(station_data)
            
            # Création du DataFrame
            df = pd.DataFrame(weather_data)
            
            generation_time = time.time() - start_time
            total_points = len(weather_data)
            logger.info(f"✅ {total_points} observations météo générées en {generation_time:.1f}s")
            
            return {
                'success': True,
                'data': df,
                'metadata': {
                    'total_observations': total_points,
                    'stations_count': station_count,
                    'time_range': f"{start_date} → {end_date}",
                    'frequency': frequency,
                    'generation_time_seconds': generation_time,
                    'generation_id': generate_unique_id('weather')
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération météo: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_station_weather_series(
        self, 
        date_range: pd.DatetimeIndex, 
        location_id: int
    ) -> List[Dict]:
        """
        Génère les données météo pour une station
        
        Args:
            date_range: Index temporel
            location_id: ID de la station
            
        Returns:
            List[Dict]: Observations météorologiques
        """
        station_data = []
        climate = WeatherConfig.CLIMATE_PARAMS
        
        for timestamp in date_range:
            # === TEMPÉRATURE ===
            # Variation diurne
            temp_diurnal = climate['temperature_variation'] * np.sin((timestamp.hour - 6) * np.pi / 12)
            # Variation saisonnière
            temp_seasonal = climate['seasonal_variation'] * np.sin((timestamp.month - 1) * np.pi / 6)
            # Bruit aléatoire
            temp_noise = np.random.normal(0, 1)
            
            temperature_2m = climate['base_temperature'] + temp_diurnal + temp_seasonal + temp_noise
            
            # === HUMIDITÉ ===
            humidity_variation = 0.1 * np.sin((timestamp.hour - 12) * np.pi / 12)
            relative_humidity_2m = np.clip(
                climate['base_humidity'] + humidity_variation + np.random.normal(0, 0.05), 
                0.5, 1.0
            )
            
            # === POINT DE ROSÉE ===
            dew_point_2m = temperature_2m - ((100 - relative_humidity_2m * 100) / 5)
            
            # === TEMPÉRATURE APPARENTE ===
            apparent_temperature = self._calculate_heat_index(temperature_2m, relative_humidity_2m)
            
            # === PRÉCIPITATIONS ===
            precip_prob = (climate['precipitation_prob_afternoon'] 
                          if 14 <= timestamp.hour <= 18 
                          else climate['precipitation_prob_night'])
            
            precipitation = (np.random.exponential(5) 
                           if np.random.random() < precip_prob 
                           else 0)
            rain = precipitation
            snowfall = 0  # Pas de neige en Malaysia
            snow_depth = 0
            
            # === CODE MÉTÉO ===
            if precipitation > 10:
                weather_code = 63  # Pluie modérée
            elif precipitation > 0:
                weather_code = 61  # Pluie légère
            elif relative_humidity_2m > 0.9:
                weather_code = 45  # Brouillard
            else:
                weather_code = 0   # Ciel clair
            
            # === PRESSION ===
            pressure_msl = climate['base_pressure'] + np.random.normal(0, 2)
            surface_pressure = pressure_msl - 5
            
            # === COUVERTURE NUAGEUSE ===
            if precipitation > 0:
                cloud_cover = np.random.uniform(80, 100)
            else:
                cloud_cover = np.random.uniform(20, 70)
            
            cloud_cover_low = cloud_cover * 0.6
            cloud_cover_mid = cloud_cover * 0.3
            cloud_cover_high = cloud_cover * 0.1
            
            # === ÉVAPOTRANSPIRATION ===
            et0_fao_evapotranspiration = np.random.uniform(4, 8)
            
            # === DÉFICIT DE PRESSION VAPEUR ===
            vapour_pressure_deficit = max(0, 2 * (1 - relative_humidity_2m))
            
            # === VENT ===
            wind_speed_10m = np.random.exponential(3)
            wind_direction_10m = np.random.uniform(0, 360)
            wind_gusts_10m = wind_speed_10m * np.random.uniform(1.2, 2.0)
            
            # === TEMPÉRATURE SOL ===
            soil_temperature_0_to_7cm = temperature_2m + np.random.normal(0, 1)
            soil_temperature_7_to_28cm = temperature_2m + np.random.normal(-1, 0.5)
            
            # === HUMIDITÉ SOL ===
            soil_moisture_0_to_7cm = np.random.uniform(0.3, 0.6)
            soil_moisture_7_to_28cm = np.random.uniform(0.4, 0.7)
            
            # === JOUR/NUIT ===
            is_day = 1 if 6 <= timestamp.hour <= 18 else 0
            
            # === ENSOLEILLEMENT ===
            sunshine_duration = (np.random.uniform(0, 3600) 
                               if is_day and precipitation == 0 
                               else 0)
            
            # === RADIATION SOLAIRE ===
            if is_day:
                base_radiation = 800 * np.sin((timestamp.hour - 6) * np.pi / 12)
                cloud_factor = (100 - cloud_cover) / 100
                shortwave_radiation = base_radiation * cloud_factor
                direct_radiation = shortwave_radiation * 0.7
                diffuse_radiation = shortwave_radiation * 0.3
                direct_normal_irradiance = direct_radiation * 1.2
            else:
                shortwave_radiation = 0
                direct_radiation = 0
                diffuse_radiation = 0
                direct_normal_irradiance = 0
            
            # === RADIATION TERRESTRE ===
            terrestrial_radiation = 400 + np.random.normal(0, 20)
            
            # === ASSEMBLAGE OBSERVATION ===
            weather_observation = {
                'timestamp': timestamp,
                'temperature_2m': round(temperature_2m, 2),
                'relative_humidity_2m': round(relative_humidity_2m, 3),
                'dew_point_2m': round(dew_point_2m, 2),
                'apparent_temperature': round(apparent_temperature, 2),
                'precipitation': round(precipitation, 2),
                'rain': round(rain, 2),
                'snowfall': round(snowfall, 2),
                'snow_depth': round(snow_depth, 2),
                'weather_code': int(weather_code),
                'pressure_msl': round(pressure_msl, 2),
                'surface_pressure': round(surface_pressure, 2),
                'cloud_cover': round(cloud_cover, 1),
                'cloud_cover_low': round(cloud_cover_low, 1),
                'cloud_cover_mid': round(cloud_cover_mid, 1),
                'cloud_cover_high': round(cloud_cover_high, 1),
                'et0_fao_evapotranspiration': round(et0_fao_evapotranspiration, 3),
                'vapour_pressure_deficit': round(vapour_pressure_deficit, 3),
                'wind_speed_10m': round(wind_speed_10m, 2),
                'wind_direction_10m': round(wind_direction_10m, 1),
                'wind_gusts_10m': round(wind_gusts_10m, 2),
                'soil_temperature_0_to_7cm': round(soil_temperature_0_to_7cm, 2),
                'soil_temperature_7_to_28cm': round(soil_temperature_7_to_28cm, 2),
                'soil_moisture_0_to_7cm': round(soil_moisture_0_to_7cm, 3),
                'soil_moisture_7_to_28cm': round(soil_moisture_7_to_28cm, 3),
                'is_day': int(is_day),
                'sunshine_duration': round(sunshine_duration, 1),
                'shortwave_radiation': round(shortwave_radiation, 2),
                'direct_radiation': round(direct_radiation, 2),
                'diffuse_radiation': round(diffuse_radiation, 2),
                'direct_normal_irradiance': round(direct_normal_irradiance, 2),
                'terrestrial_radiation': round(terrestrial_radiation, 2),
                'location_id': location_id
            }
            
            station_data.append(weather_observation)
        
        return station_data
    
    def _calculate_heat_index(self, temp_c: float, humidity: float) -> float:
        """
        Calcule l'indice de chaleur (température apparente) - VERSION CORRIGÉE
        
        Args:
            temp_c: Température en Celsius
            humidity: Humidité relative (0-1)
            
        Returns:
            float: Température apparente en Celsius
        """
        # Conversion en Fahrenheit pour calcul
        temp_f = temp_c * 9/5 + 32
        rh = humidity * 100
        
        # Formule Heat Index simplifiée
        hi = (0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (rh * 0.094)))
        
        if hi >= 80:
            # Formule complète pour températures élevées
            hi = (-42.379 + 2.04901523 * temp_f + 
                  10.14333127 * rh - 0.22475541 * temp_f * rh -
                  0.00683783 * temp_f * temp_f - 0.05481717 * rh * rh +
                  0.00122874 * temp_f * temp_f * rh + 0.00085282 * temp_f * rh * rh -
                  0.00000199 * temp_f * temp_f * rh * rh)
        
        # Conversion retour en Celsius - PARTIE MANQUANTE CORRIGÉE
        hi_celsius = (hi - 32) * 5/9
        
        return hi_celsius


# ==============================================================================
# GÉNÉRATEUR CONSOMMATION D'EAU
# ==============================================================================

class WaterGenerator:
    """Générateur de données de consommation d'eau pour Malaysia"""
    
    def __init__(self):
        """Initialise le générateur d'eau"""
        self.generation_count = 0
        logger.info("✅ WaterGenerator initialisé")
    
    def generate_water_consumption_timeseries(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H'
    ) -> Dict:
        """
        Génère les séries temporelles de consommation d'eau
        
        Args:
            buildings: Liste des bâtiments
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            frequency: Fréquence ('15T', '1H', '3H', 'D')
            
        Returns:
            Dict: Résultat avec DataFrame de consommation d'eau
        """
        start_time = time.time()
        self.generation_count += 1
        
        try:
            logger.info(f"💧 Génération consommation eau: {len(buildings)} bâtiments")
            logger.info(f"📅 Période: {start_date} → {end_date} ({frequency})")
            
            # Création de l'index temporel
            date_range = pd.date_range(start=start_date, end=end_date, freq=frequency)
            logger.info(f"📊 {len(date_range)} points temporels à générer")
            
            # Génération des données
            water_data = []
            
            for building in buildings:
                building_water = self._generate_building_water_series(
                    building, date_range
                )
                water_data.extend(building_water)
            
            # Création du DataFrame
            df = pd.DataFrame(water_data)
            
            generation_time = time.time() - start_time
            logger.info(f"✅ {len(water_data)} points eau générés en {generation_time:.1f}s")
            
            return {
                'success': True,
                'data': df,
                'metadata': {
                    'total_points': len(water_data),
                    'buildings_count': len(buildings),
                    'time_range': f"{start_date} → {end_date}",
                    'frequency': frequency,
                    'generation_time_seconds': generation_time,
                    'generation_id': generate_unique_id('water')
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération eau: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_building_water_series(
        self, 
        building: Dict, 
        date_range: pd.DatetimeIndex
    ) -> List[Dict]:
        """
        Génère la série de consommation d'eau pour un bâtiment
        
        Args:
            building: Données du bâtiment
            date_range: Index temporel
            
        Returns:
            List[Dict]: Points de consommation d'eau
        """
        building_type = building.get('building_type', 'residential')
        surface_area = building.get('surface_area_m2', 100)
        building_id = building['id']
        
        # Consommation de base eau
        base_water_consumption = self._calculate_base_water_consumption(building_type, surface_area)
        
        water_points = []
        
        for timestamp in date_range:
            # Facteurs de variation eau (différents de l'électricité)
            hour_factor = self._get_water_hourly_factor(timestamp.hour, building_type)
            day_factor = self._get_water_daily_factor(timestamp.dayofweek, building_type)
            seasonal_factor = self._get_water_seasonal_factor(timestamp.month)
            
            # Variation aléatoire pour l'eau
            random_factor = np.random.normal(1.0, 0.15)  # Plus de variabilité que électricité
            
            # Consommation finale eau
            water_consumption = (base_water_consumption * 
                               hour_factor * 
                               day_factor * 
                               seasonal_factor * 
                               random_factor)
            
            water_points.append({
                'building_id': building_id,
                'timestamp': timestamp,
                'water_consumption_liters': max(0, water_consumption),
                'building_type': building_type,
                'surface_area_m2': surface_area,
                'consumption_intensity_l_m2': water_consumption / surface_area if surface_area > 0 else 0
            })
        
        return water_points
    
    def _calculate_base_water_consumption(self, building_type: str, surface_area: float) -> float:
        """
        Calcule la consommation d'eau de base horaire en litres
        
        Basé sur les standards Malaysia de consommation d'eau
        """
        # Utilisation des données de config.py
        config = MalaysiaConfig.get_building_type_config(building_type)
        daily_consumption_m2 = config.get('base_water_consumption_l_m2_day', 150)
        
        # Conversion en horaire
        hourly_consumption = (daily_consumption_m2 * surface_area) / 24
        
        return hourly_consumption
    
    def _get_water_hourly_factor(self, hour: int, building_type: str) -> float:
        """Facteur de variation horaire pour l'eau"""
        if building_type == 'residential':
            # Pics eau: matin (douches), midi (cuisine), soir (bains)
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
            # Usage eau bureaux: constant pendant heures travail
            if 8 <= hour <= 18:
                return 1.5
            else:
                return 0.1
        elif building_type == 'hospital':
            # Hôpital: consommation plus constante 24h/24
            return 1.0 + 0.2 * np.sin((hour - 6) * np.pi / 12)
        else:
            # Profil industriel/école
            if 7 <= hour <= 19:
                return 1.8
            else:
                return 0.3
    
    def _get_water_daily_factor(self, day_of_week: int, building_type: str) -> float:
        """Facteur de variation journalière pour l'eau"""
        if building_type == 'residential':
            return 1.3 if day_of_week >= 5 else 1.0  # Plus d'eau weekend (présence)
        elif building_type in ['office', 'commercial', 'school']:
            return 0.2 if day_of_week >= 5 else 1.0  # Beaucoup moins weekend
        else:
            return 1.0  # Constant pour industriel/hôpital
    
    def _get_water_seasonal_factor(self, month: int) -> float:
        """Facteur saisonnier eau (climat tropical Malaysia)"""
        # Saison sèche (juin-août) = plus de consommation d'eau
        if 6 <= month <= 8:
            return 1.4
        # Saison des pluies = moins de consommation (eau de pluie disponible)
        elif 11 <= month <= 12 or 1 <= month <= 2:
            return 0.8
        else:
            return 1.0