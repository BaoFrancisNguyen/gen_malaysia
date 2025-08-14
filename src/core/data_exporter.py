#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPORTEUR DE DONNÉES - CORE MODULE
==================================

Module core pour l'export des données en différents formats.
Responsabilité unique: export et sérialisation des DataFrames.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import pandas as pd

from config import ExportConfig, AppConfig
from src.utils.helpers import get_file_size_mb, clean_filename, format_file_size
from src.utils.validators import validate_export_format

logger = logging.getLogger(__name__)


class DataExporter:
    """Exporteur de données en formats multiples"""
    
    def __init__(self):
        """Initialise l'exporteur"""
        self.export_count = 0
        self.export_history = []
        logger.info("✅ DataExporter initialisé")
    
    def export_four_datasets(
        self,
        buildings_df: pd.DataFrame,
        consumption_df: pd.DataFrame,
        weather_df: pd.DataFrame,
        water_df: pd.DataFrame,
        export_format: str = 'csv',
        base_filename: str = None
    ) -> Dict:
        """
        Exporte les 4 datasets distincts (ajout de l'eau)
        
        Args:
            buildings_df: DataFrame métadonnées bâtiments
            consumption_df: DataFrame consommation électrique
            weather_df: DataFrame données météo
            water_df: DataFrame consommation eau
            export_format: Format ('csv', 'parquet', 'xlsx')
            base_filename: Nom de base pour les fichiers
            
        Returns:
            Dict: Résultat avec chemins des fichiers créés
        """
        start_time = time.time()
        self.export_count += 1
        export_id = f"export_{self.export_count}_{int(time.time())}"
        
        try:
            # Validation du format
            if not validate_export_format(export_format):
                return {
                    'success': False,
                    'error': f"Format non supporté: {export_format}",
                    'supported_formats': ExportConfig.SUPPORTED_FORMATS
                }
            
            logger.info(f"📁 Export {export_id}: format {export_format.upper()}")
            
            # Génération des noms de fichiers (4 fichiers maintenant)
            if not base_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_filename = f"malaysia_electricity_{timestamp}"
            
            base_filename = clean_filename(base_filename)
            
            filenames = self._generate_four_filenames(base_filename, export_format)
            
            # Export de chaque dataset
            exported_files = []
            
            # 1. Export métadonnées bâtiments
            if not buildings_df.empty:
                buildings_result = self._export_single_dataset(
                    df=buildings_df,
                    filename=filenames['buildings'],
                    dataset_type='buildings_metadata',
                    export_format=export_format
                )
                if buildings_result['success']:
                    exported_files.append(buildings_result['file_info'])
                else:
                    return buildings_result
            
            # 2. Export consommation électrique
            if not consumption_df.empty:
                consumption_result = self._export_single_dataset(
                    df=consumption_df,
                    filename=filenames['consumption'],
                    dataset_type='electricity_consumption',
                    export_format=export_format
                )
                if consumption_result['success']:
                    exported_files.append(consumption_result['file_info'])
                else:
                    return consumption_result
            
            # 3. Export données météo
            if not weather_df.empty:
                weather_result = self._export_single_dataset(
                    df=weather_df,
                    filename=filenames['weather'],
                    dataset_type='weather_simulation',
                    export_format=export_format
                )
                if weather_result['success']:
                    exported_files.append(weather_result['file_info'])
                else:
                    return weather_result
            
            # 4. Export consommation eau (NOUVEAU)
            if not water_df.empty:
                water_result = self._export_single_dataset(
                    df=water_df,
                    filename=filenames['water'],
                    dataset_type='water_consumption',
                    export_format=export_format
                )
                if water_result['success']:
                    exported_files.append(water_result['file_info'])
                    logger.info(f"✅ Exporté: {filenames['water']} ({len(water_df)} points eau)")
                else:
                    logger.warning(f"⚠️ Échec export eau: {water_result.get('error', 'Unknown')}")
            
            # Calcul des statistiques finales
            export_time = time.time() - start_time
            total_size_mb = sum(f['size_mb'] for f in exported_files)
            total_records = sum(f['records'] for f in exported_files)
            
            # Enregistrement dans l'historique
            export_session = {
                'export_id': export_id,
                'export_time': datetime.now().isoformat(),
                'export_format': export_format,
                'files_created': len(exported_files),
                'total_size_mb': total_size_mb,
                'total_records': total_records,
                'export_time_seconds': export_time,
                'base_filename': base_filename,
                'includes_water': not water_df.empty
            }
            
            self.export_history.append(export_session)
            
            # Garde seulement les 20 derniers exports
            if len(self.export_history) > 20:
                self.export_history = self.export_history[-20:]
            
            datasets_created = []
            for file_info in exported_files:
                datasets_created.append(file_info['type'])
            
            logger.info(f"✅ Export {export_id} terminé: {len(exported_files)} fichiers "
                       f"({', '.join(datasets_created)}), {format_file_size(total_size_mb * 1024 * 1024)}")
            
            return {
                'success': True,
                'export_id': export_id,
                'files': exported_files,
                'metadata': {
                    'export_format': export_format,
                    'total_files': len(exported_files),
                    'total_size_mb': round(total_size_mb, 2),
                    'total_records': total_records,
                    'export_time_seconds': round(export_time, 2),
                    'export_directory': str(AppConfig.EXPORTS_DIR),
                    'base_filename': base_filename,
                    'datasets_included': datasets_created,
                    'water_included': not water_df.empty
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur export {export_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'export_id': export_id
            }
    
    def _generate_four_filenames(self, base_filename: str, export_format: str) -> Dict[str, str]:
        """
        Génère les noms de fichiers pour les 4 datasets
        
        Args:
            base_filename: Nom de base
            export_format: Format d'export
            
        Returns:
            Dict: Noms des fichiers pour chaque type
        """
        extension = ExportConfig.FORMAT_CONFIG[export_format]['extension']
        
        return {
            'buildings': f"{base_filename}_buildings_metadata{extension}",
            'consumption': f"{base_filename}_electricity_consumption{extension}",
            'weather': f"{base_filename}_weather_simulation{extension}",
            'water': f"{base_filename}_water_consumption{extension}"
        }
    
    # Garder l'ancienne méthode pour compatibilité
    def export_three_datasets(
        self,
        buildings_df: pd.DataFrame,
        consumption_df: pd.DataFrame,
        weather_df: pd.DataFrame,
        export_format: str = 'csv',
        base_filename: str = None
    ) -> Dict:
        """
        Exporte les 3 datasets originaux (pour compatibilité)
        """
        # Appel de la nouvelle méthode avec DataFrame eau vide
        return self.export_four_datasets(
            buildings_df=buildings_df,
            consumption_df=consumption_df,
            weather_df=weather_df,
            water_df=pd.DataFrame(),  # Pas d'eau
            export_format=export_format,
            base_filename=base_filename
        )
    
    def _generate_filenames(self, base_filename: str, export_format: str) -> Dict[str, str]:
        """
        Génère les noms de fichiers pour les 3 datasets
        
        Args:
            base_filename: Nom de base
            export_format: Format d'export
            
        Returns:
            Dict: Noms des fichiers pour chaque type
        """
        extension = ExportConfig.FORMAT_CONFIG[export_format]['extension']
        
        return {
            'buildings': f"{base_filename}_buildings_metadata{extension}",
            'consumption': f"{base_filename}_electricity_consumption{extension}",
            'weather': f"{base_filename}_weather_simulation{extension}"
        }
    
    def _export_single_dataset(
        self,
        df: pd.DataFrame,
        filename: str,
        dataset_type: str,
        export_format: str
    ) -> Dict:
        """
        Exporte un seul dataset
        
        Args:
            df: DataFrame à exporter
            filename: Nom du fichier
            dataset_type: Type de dataset
            export_format: Format d'export
            
        Returns:
            Dict: Résultat de l'export
        """
        try:
            file_path = AppConfig.EXPORTS_DIR / filename
            
            # Export selon le format
            if export_format == 'csv':
                self._export_to_csv(df, file_path)
            elif export_format == 'parquet':
                self._export_to_parquet(df, file_path)
            elif export_format == 'xlsx':
                self._export_to_excel(df, file_path)
            else:
                return {
                    'success': False,
                    'error': f"Format non implémenté: {export_format}"
                }
            
            # Vérification du fichier créé
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f"Fichier non créé: {filename}"
                }
            
            # Informations du fichier
            file_size_mb = get_file_size_mb(file_path)
            
            file_info = {
                'name': filename,
                'path': str(file_path),
                'type': dataset_type,
                'format': export_format,
                'records': len(df),
                'columns': len(df.columns),
                'size_mb': round(file_size_mb, 2),
                'created_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Exporté: {filename} ({len(df)} enregistrements, {file_size_mb:.1f}MB)")
            
            return {
                'success': True,
                'file_info': file_info
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur export {filename}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _export_to_csv(self, df: pd.DataFrame, file_path: Path):
        """Exporte en CSV"""
        config = ExportConfig.FORMAT_CONFIG['csv']
        
        df.to_csv(
            file_path,
            index=False,
            sep=config['separator'],
            encoding=config['encoding'],
            date_format='%Y-%m-%d %H:%M:%S'
        )
    
    def _export_to_parquet(self, df: pd.DataFrame, file_path: Path):
        """Exporte en Parquet"""
        config = ExportConfig.FORMAT_CONFIG['parquet']
        
        df.to_parquet(
            file_path,
            index=False,
            compression=config['compression'],
            engine='pyarrow'
        )
    
    def _export_to_excel(self, df: pd.DataFrame, file_path: Path):
        """Exporte en Excel"""
        config = ExportConfig.FORMAT_CONFIG['xlsx']
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(
                writer,
                sheet_name=config['sheet_name'],
                index=False
            )
    
    def export_single_dataframe(
        self,
        df: pd.DataFrame,
        filename: str,
        export_format: str = 'csv'
    ) -> Dict:
        """
        Exporte un seul DataFrame
        
        Args:
            df: DataFrame à exporter
            filename: Nom du fichier
            export_format: Format d'export
            
        Returns:
            Dict: Résultat de l'export
        """
        try:
            if df.empty:
                return {
                    'success': False,
                    'error': 'DataFrame vide'
                }
            
            # Nettoyage du nom de fichier
            clean_name = clean_filename(filename)
            if not clean_name.endswith(ExportConfig.FORMAT_CONFIG[export_format]['extension']):
                clean_name += ExportConfig.FORMAT_CONFIG[export_format]['extension']
            
            result = self._export_single_dataset(
                df=df,
                filename=clean_name,
                dataset_type='single_dataframe',
                export_format=export_format
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur export DataFrame unique: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_export_statistics(self) -> Dict:
        """
        Retourne les statistiques d'export
        
        Returns:
            Dict: Statistiques du service
        """
        if not self.export_history:
            return {
                'total_exports': 0,
                'total_files_created': 0,
                'total_size_mb': 0
            }
        
        total_files = sum(exp['files_created'] for exp in self.export_history)
        total_size = sum(exp['total_size_mb'] for exp in self.export_history)
        total_records = sum(exp['total_records'] for exp in self.export_history)
        
        # Répartition par format
        format_counts = {}
        for exp in self.export_history:
            fmt = exp['export_format']
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        return {
            'total_exports': len(self.export_history),
            'total_files_created': total_files,
            'total_size_mb': round(total_size, 2),
            'total_records_exported': total_records,
            'export_count': self.export_count,
            'format_distribution': format_counts,
            'recent_exports': self.export_history[-5:],
            'supported_formats': ExportConfig.SUPPORTED_FORMATS
        }
    
    def list_exported_files(self) -> List[Dict]:
        """
        Liste tous les fichiers exportés dans le dossier
        
        Returns:
            List[Dict]: Liste des fichiers avec métadonnées
        """
        try:
            files = []
            
            for file_path in AppConfig.EXPORTS_DIR.glob('*'):
                if file_path.is_file():
                    stat = file_path.stat()
                    
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # Tri par date de création (plus récent en premier)
            files.sort(key=lambda x: x['created_at'], reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Erreur listage fichiers: {e}")
            return []