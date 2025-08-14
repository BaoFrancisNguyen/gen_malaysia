#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SERVICE DE GÉNÉRATION - COUCHE SERVICE
======================================

Service métier pour orchestrer la génération des données électriques et météo.
Coordonne les appels aux générateurs et gère la logique métier.
"""

import logging
from typing import Dict, List
from datetime import datetime
import pandas as pd

from src.core.generator import ElectricityGenerator, WeatherGenerator
from src.utils.validators import validate_date_range, validate_frequency, validate_building_list
from src.utils.helpers import generate_session_id

logger = logging.getLogger(__name__)


class GenerationService:
    """Service métier pour la génération de données"""
    
    def __init__(self):
        """Initialise le service de génération"""
        self.electricity_generator = ElectricityGenerator()
        self.weather_generator = WeatherGenerator()
        self.water_generator = WaterGenerator()  # Nouveau générateur d'eau
        self.generation_sessions = []
        logger.info("✅ GenerationService initialisé avec générateur d'eau")
    
    def generate_all_data(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H',
        weather_stations: int = 5,
        include_water: bool = True
    ) -> Dict:
        """
        Génère toutes les données (électricité + météo + eau optionnelle)
        
        Args:
            buildings: Liste des bâtiments
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            frequency: Fréquence d'échantillonnage
            weather_stations: Nombre de stations météo
            include_water: Si True, génère aussi la consommation d'eau
            
        Returns:
            Dict: Résultat avec toutes les données générées
        """
        session_id = generate_session_id()
        start_time = datetime.now()
        
        try:
            logger.info(f"🔄 Session génération: {session_id}")
            logger.info(f"📊 Génération complète: {len(buildings)} bâtiments, {weather_stations} stations météo, eau: {include_water}")
            
            # Validation des paramètres
            validation_result = self._validate_generation_parameters(
                buildings, start_date, end_date, frequency, weather_stations
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'Paramètres invalides',
                    'validation_errors': validation_result['errors'],
                    'session_id': session_id
                }
            
            # Génération des données électriques
            logger.info("⚡ Génération des données électriques...")
            electricity_result = self.electricity_generator.generate_consumption_timeseries(
                buildings=buildings,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency
            )
            
            if not electricity_result['success']:
                return {
                    'success': False,
                    'error': f"Erreur génération électricité: {electricity_result['error']}",
                    'session_id': session_id
                }
            
            # Génération des données d'eau (optionnelle)
            water_result = None
            if include_water:
                logger.info("💧 Génération des données de consommation d'eau...")
                water_result = self.water_generator.generate_water_consumption_timeseries(
                    buildings=buildings,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency
                )
                
                if not water_result['success']:
                    logger.warning(f"⚠️ Erreur génération eau (continuant sans): {water_result['error']}")
                    water_result = None
    
    def generate_all_data(
        self,
        buildings: List[Dict],
        start_date: str,
        end_date: str,
        frequency: str = '1H',
        weather_stations: int = 5
    ) -> Dict:
        """
        Génère toutes les données (électricité + météo)
        
        Args:
            buildings: Liste des bâtiments
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            frequency: Fréquence d'échantillonnage
            weather_stations: Nombre de stations météo
            
        Returns:
            Dict: Résultat avec toutes les données générées
        """
        session_id = generate_session_id()
        start_time = datetime.now()
        
        try:
            logger.info(f"🔄 Session génération: {session_id}")
            logger.info(f"📊 Génération complète: {len(buildings)} bâtiments, {weather_stations} stations météo")
            
            # Validation des paramètres
            validation_result = self._validate_generation_parameters(
                buildings, start_date, end_date, frequency, weather_stations
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'Paramètres invalides',
                    'validation_errors': validation_result['errors'],
                    'session_id': session_id
                }
            
            # Génération des données électriques
            logger.info("⚡ Génération des données électriques...")
            electricity_result = self.electricity_generator.generate_consumption_timeseries(
                buildings=buildings,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency
            )
            
            if not electricity_result['success']:
                return {
                    '