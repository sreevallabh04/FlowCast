import pandas as pd
import numpy as np
import yaml
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer

@dataclass
class TransformationConfig:
    normalization: str = 'zscore'  # 'zscore', 'minmax', or 'none'
    impute_strategy: str = 'mean'  # 'mean', 'median', 'most_frequent', or 'constant'
    feature_engineering: bool = True
    categorical_encoding: str = 'onehot'  # 'onehot', 'label', or 'none'
    log_level: str = 'INFO'
    output_dir: str = 'data/processed'

class DataTransformation:
    def __init__(self, config_path: str = 'config/transformation_config.yaml'):
        self.config = self._load_config(config_path)
        self.logger = self._init_logger()
        os.makedirs(self.config.output_dir, exist_ok=True)
        self.scaler = None
        self.encoder = None
        self.imputer = None

    def _load_config(self, path: str) -> TransformationConfig:
        if os.path.exists(path):
            with open(path, 'r') as f:
                cfg = yaml.safe_load(f)
            return TransformationConfig(**cfg)
        return TransformationConfig()

    def _init_logger(self):
        logger = logging.getLogger('DataTransformation')
        logger.setLevel(getattr(logging, self.config.log_level.upper(), 'INFO'))
        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            logger.addHandler(ch)
        return logger

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info('Cleaning data: removing duplicates and handling missing values')
        df = df.drop_duplicates()
        self.imputer = SimpleImputer(strategy=self.config.impute_strategy)
        df[df.columns] = self.imputer.fit_transform(df)
        return df

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info(f'Normalizing data using {self.config.normalization}')
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if self.config.normalization == 'zscore':
            self.scaler = StandardScaler()
        elif self.config.normalization == 'minmax':
            self.scaler = MinMaxScaler()
        else:
            return df
        df[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
        return df

    def encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info(f'Encoding categorical features using {self.config.categorical_encoding}')
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if self.config.categorical_encoding == 'onehot':
            df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
        elif self.config.categorical_encoding == 'label':
            self.encoder = LabelEncoder()
            for col in cat_cols:
                df[col] = self.encoder.fit_transform(df[col].astype(str))
        return df

    def feature_engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info('Performing feature engineering')
        if 'date' in df.columns:
            df['year'] = pd.to_datetime(df['date']).dt.year
            df['month'] = pd.to_datetime(df['date']).dt.month
            df['dayofweek'] = pd.to_datetime(df['date']).dt.dayofweek
        if 'sales' in df.columns and 'inventory' in df.columns:
            df['sales_to_inventory'] = df['sales'] / (df['inventory'] + 1e-6)
        return df

    def enrich(self, df: pd.DataFrame, enrichments: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        self.logger.info('Enriching data with external sources (if provided)')
        if enrichments:
            for col, values in enrichments.items():
                df[col] = values
        return df

    def transform(self, df: pd.DataFrame, enrichments: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        df = self.clean(df)
        df = self.normalize(df)
        df = self.encode_categorical(df)
        if self.config.feature_engineering:
            df = self.feature_engineer(df)
        df = self.enrich(df, enrichments)
        return df

    def save(self, df: pd.DataFrame, name: str) -> str:
        path = os.path.join(self.config.output_dir, f'{name}.csv')
        df.to_csv(path, index=False)
        self.logger.info(f'Saved transformed data to {path}')
        return path

# Example usage
if __name__ == '__main__':
    transformer = DataTransformation()
    df = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02'],
        'sales': [100, 200],
        'inventory': [50, 80],
        'category': ['A', 'B']
    })
    df_trans = transformer.transform(df)
    transformer.save(df_trans, 'example_transformed')
    print(df_trans.head()) 