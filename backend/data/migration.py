import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker
from alembic import op
import alembic.config
import alembic.script
import alembic.runtime.migration
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import hashlib
import time
from pathlib import Path
import shutil
import tempfile
import threading
import queue
import schedule
import pytz
import uuid
import mysql.connector
import pymongo
import redis
import elasticsearch
import neo4j
import cassandra
import influxdb
import clickhouse_driver
import vertica_python
import snowflake.connector
import bigquery
import redshift_connector
import teradata
import oracle
import sqlserver
import db2
import sqlite3
import hdf5
import parquet
import avro
import orc
import arrow
import feather
import pickle
import joblib
import dask
import vaex
import modin.pandas as mpd
import polars
import pyarrow
import pyarrow.parquet
import pyarrow.feather
import pyarrow.csv
import pyarrow.json
import pyarrow.avro
import pyarrow.orc
import pyarrow.ipc
import pyarrow.flight
import pyarrow.dataset
import pyarrow.compute
import pyarrow.fs
import pyarrow.memory
import pyarrow.schema
import pyarrow.types
import pyarrow.array
import pyarrow.table
import pyarrow.record_batch
import pyarrow.buffer
import pyarrow.memory_pool
import pyarrow.cuda
import pyarrow.gandiva
import pyarrow.plasma
from flask_migrate import Migrate
from models import db

@dataclass
class MigrationConfig:
    """Configuration for the migration system."""
    source_type: str
    source_config: Dict
    target_type: str
    target_config: Dict
    batch_size: int
    max_workers: int
    chunk_size: int
    timeout: int
    retry_attempts: int
    retry_delay: int
    enable_validation: bool
    enable_verification: bool
    enable_logging: bool
    enable_monitoring: bool
    enable_scheduling: bool
    enable_cleanup: bool
    enable_rollback: bool
    enable_resume: bool
    enable_parallel: bool
    enable_incremental: bool
    enable_full: bool
    enable_differential: bool
    enable_snapshot: bool
    enable_replication: bool
    enable_sync: bool
    enable_mirror: bool
    enable_consolidation: bool
    enable_deduplication: bool
    enable_compression: bool
    enable_encryption: bool
    enable_verification: bool
    enable_notification: bool
    enable_logging: bool
    enable_monitoring: bool
    enable_scheduling: bool
    enable_cleanup: bool
    enable_rollback: bool
    enable_resume: bool
    enable_parallel: bool
    enable_incremental: bool
    enable_full: bool
    enable_differential: bool
    enable_snapshot: bool
    enable_replication: bool
    enable_sync: bool
    enable_mirror: bool
    enable_consolidation: bool
    enable_deduplication: bool

class DataMigration:
    def __init__(self, app):
        self.app = app
        self.migrate = Migrate(app, db)
        self.logger = logging.getLogger('flowcast')
        self.config_path = 'config/migration_config.yaml'
        self.config = self._load_config()
        self.migration_queue = queue.Queue()
        self.processing = False
        self.processing_thread = None
        self.source_client = None
        self.target_client = None
        
        # Initialize clients
        self._init_clients()
        
        # Start processing
        self.start_processing()

    def _load_config(self) -> MigrationConfig:
        """Load migration configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return MigrationConfig(**config_dict)
        except Exception as e:
            print(f"Error loading migration configuration: {str(e)}")
            raise

    def _init_clients(self) -> None:
        """Initialize source and target clients."""
        try:
            # Initialize source client
            if self.config.source_type == 'postgresql':
                self.source_client = create_engine(self.config.source_config['url'])
            elif self.config.source_type == 'mysql':
                self.source_client = mysql.connector.connect(**self.config.source_config)
            elif self.config.source_type == 'mongodb':
                self.source_client = pymongo.MongoClient(**self.config.source_config)
            elif self.config.source_type == 'redis':
                self.source_client = redis.Redis(**self.config.source_config)
            elif self.config.source_type == 'elasticsearch':
                self.source_client = elasticsearch.Elasticsearch(**self.config.source_config)
            elif self.config.source_type == 'neo4j':
                self.source_client = neo4j.GraphDatabase.driver(**self.config.source_config)
            elif self.config.source_type == 'cassandra':
                self.source_client = cassandra.cluster.Cluster(**self.config.source_config)
            elif self.config.source_type == 'influxdb':
                self.source_client = influxdb.InfluxDBClient(**self.config.source_config)
            elif self.config.source_type == 'clickhouse':
                self.source_client = clickhouse_driver.Client(**self.config.source_config)
            elif self.config.source_type == 'vertica':
                self.source_client = vertica_python.connect(**self.config.source_config)
            elif self.config.source_type == 'snowflake':
                self.source_client = snowflake.connector.connect(**self.config.source_config)
            elif self.config.source_type == 'bigquery':
                self.source_client = bigquery.Client(**self.config.source_config)
            elif self.config.source_type == 'redshift':
                self.source_client = redshift_connector.connect(**self.config.source_config)
            elif self.config.source_type == 'teradata':
                self.source_client = teradata.connect(**self.config.source_config)
            elif self.config.source_type == 'oracle':
                self.source_client = oracle.connect(**self.config.source_config)
            elif self.config.source_type == 'sqlserver':
                self.source_client = sqlserver.connect(**self.config.source_config)
            elif self.config.source_type == 'db2':
                self.source_client = db2.connect(**self.config.source_config)
            elif self.config.source_type == 'sqlite':
                self.source_client = sqlite3.connect(**self.config.source_config)
            
            # Initialize target client
            if self.config.target_type == 'postgresql':
                self.target_client = create_engine(self.config.target_config['url'])
            elif self.config.target_type == 'mysql':
                self.target_client = mysql.connector.connect(**self.config.target_config)
            elif self.config.target_type == 'mongodb':
                self.target_client = pymongo.MongoClient(**self.config.target_config)
            elif self.config.target_type == 'redis':
                self.target_client = redis.Redis(**self.config.target_config)
            elif self.config.target_type == 'elasticsearch':
                self.target_client = elasticsearch.Elasticsearch(**self.config.target_config)
            elif self.config.target_type == 'neo4j':
                self.target_client = neo4j.GraphDatabase.driver(**self.config.target_config)
            elif self.config.target_type == 'cassandra':
                self.target_client = cassandra.cluster.Cluster(**self.config.target_config)
            elif self.config.target_type == 'influxdb':
                self.target_client = influxdb.InfluxDBClient(**self.config.target_config)
            elif self.config.target_type == 'clickhouse':
                self.target_client = clickhouse_driver.Client(**self.config.target_config)
            elif self.config.target_type == 'vertica':
                self.target_client = vertica_python.connect(**self.config.target_config)
            elif self.config.target_type == 'snowflake':
                self.target_client = snowflake.connector.connect(**self.config.target_config)
            elif self.config.target_type == 'bigquery':
                self.target_client = bigquery.Client(**self.config.target_config)
            elif self.config.target_type == 'redshift':
                self.target_client = redshift_connector.connect(**self.config.target_config)
            elif self.config.target_type == 'teradata':
                self.target_client = teradata.connect(**self.config.target_config)
            elif self.config.target_type == 'oracle':
                self.target_client = oracle.connect(**self.config.target_config)
            elif self.config.target_type == 'sqlserver':
                self.target_client = sqlserver.connect(**self.config.target_config)
            elif self.config.target_type == 'db2':
                self.target_client = db2.connect(**self.config.target_config)
            elif self.config.target_type == 'sqlite':
                self.target_client = sqlite3.connect(**self.config.target_config)
            
        except Exception as e:
            print(f"Error initializing clients: {str(e)}")
            raise

    def start_processing(self) -> None:
        """Start migration processing."""
        try:
            if not self.processing:
                self.processing = True
                self.processing_thread = threading.Thread(target=self._process_migrations)
                self.processing_thread.daemon = True
                self.processing_thread.start()
            
        except Exception as e:
            print(f"Error starting migration processing: {str(e)}")
            raise

    def stop_processing(self) -> None:
        """Stop migration processing."""
        try:
            self.processing = False
            if self.processing_thread:
                self.processing_thread.join()
            
        except Exception as e:
            print(f"Error stopping migration processing: {str(e)}")
            raise

    def _process_migrations(self) -> None:
        """Process migrations from the queue."""
        try:
            while self.processing:
                try:
                    # Get migration from queue
                    migration = self.migration_queue.get(timeout=1)
                    
                    # Process migration
                    self._execute_migration(migration)
                    
                    # Mark task as done
                    self.migration_queue.task_done()
                    
                except queue.Empty:
                    continue
                
        except Exception as e:
            print(f"Error processing migrations: {str(e)}")
            raise

    def _execute_migration(self, migration: Dict) -> None:
        """Execute a migration."""
        try:
            # Get migration type
            migration_type = migration.get('type', 'full')
            
            # Get source and target
            source = migration.get('source')
            target = migration.get('target')
            
            # Execute based on type
            if migration_type == 'full':
                self._execute_full_migration(source, target)
            elif migration_type == 'incremental':
                self._execute_incremental_migration(source, target)
            elif migration_type == 'differential':
                self._execute_differential_migration(source, target)
            elif migration_type == 'snapshot':
                self._execute_snapshot_migration(source, target)
            else:
                raise ValueError(f"Unknown migration type: {migration_type}")
            
        except Exception as e:
            print(f"Error executing migration: {str(e)}")
            raise

    def _execute_full_migration(self, source: Dict, target: Dict) -> None:
        """Execute a full migration."""
        try:
            # Read data from source
            if self.config.source_type == 'postgresql':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'mysql':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'mongodb':
                data = pd.DataFrame(list(self.source_client[source['database']][source['collection']].find()))
            elif self.config.source_type == 'redis':
                data = pd.DataFrame(self.source_client.hgetall(source['key']))
            elif self.config.source_type == 'elasticsearch':
                data = pd.DataFrame(self.source_client.search(**source))
            elif self.config.source_type == 'neo4j':
                data = pd.DataFrame(self.source_client.run(source['query']).data())
            elif self.config.source_type == 'cassandra':
                data = pd.DataFrame(self.source_client.execute(source['query']))
            elif self.config.source_type == 'influxdb':
                data = pd.DataFrame(self.source_client.query(source['query']).get_points())
            elif self.config.source_type == 'clickhouse':
                data = pd.DataFrame(self.source_client.execute(source['query']))
            elif self.config.source_type == 'vertica':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'snowflake':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'bigquery':
                data = self.source_client.query(source['query']).to_dataframe()
            elif self.config.source_type == 'redshift':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'teradata':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'oracle':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'sqlserver':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'db2':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'sqlite':
                data = pd.read_sql(source['query'], self.source_client)
            
            # Write data to target
            if self.config.target_type == 'postgresql':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'mysql':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'mongodb':
                self.target_client[target['database']][target['collection']].insert_many(data.to_dict('records'))
            elif self.config.target_type == 'redis':
                self.target_client.hmset(target['key'], data.to_dict())
            elif self.config.target_type == 'elasticsearch':
                self.target_client.bulk(data.to_dict('records'))
            elif self.config.target_type == 'neo4j':
                self.target_client.run(target['query'], data=data.to_dict('records'))
            elif self.config.target_type == 'cassandra':
                self.target_client.execute(target['query'], data.to_dict('records'))
            elif self.config.target_type == 'influxdb':
                self.target_client.write_points(data.to_dict('records'))
            elif self.config.target_type == 'clickhouse':
                self.target_client.execute(target['query'], data.to_dict('records'))
            elif self.config.target_type == 'vertica':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'snowflake':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'bigquery':
                self.target_client.load_table_from_dataframe(data, target['table'])
            elif self.config.target_type == 'redshift':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'teradata':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'oracle':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'sqlserver':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'db2':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'sqlite':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            
        except Exception as e:
            print(f"Error executing full migration: {str(e)}")
            raise

    def _execute_incremental_migration(self, source: Dict, target: Dict) -> None:
        """Execute an incremental migration."""
        try:
            # Get last migration timestamp
            last_migration = self._get_last_migration_time()
            
            # Read incremental data from source
            if self.config.source_type == 'postgresql':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.source_type == 'mysql':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.source_type == 'mongodb':
                data = pd.DataFrame(list(self.source_client[source['database']][source['collection']].find({
                    'updated_at': {'$gt': last_migration}
                })))
            elif self.config.source_type == 'redis':
                data = pd.DataFrame(self.source_client.hgetall(source['key']))
            elif self.config.source_type == 'elasticsearch':
                data = pd.DataFrame(self.source_client.search(**{
                    **source,
                    'query': {
                        'range': {
                            'updated_at': {
                                'gt': last_migration
                            }
                        }
                    }
                }))
            elif self.config.source_type == 'neo4j':
                data = pd.DataFrame(self.source_client.run(
                    f"{source['query']} WHERE n.updated_at > '{last_migration}'"
                ).data())
            elif self.config.source_type == 'cassandra':
                data = pd.DataFrame(self.source_client.execute(
                    f"{source['query']} WHERE updated_at > '{last_migration}'"
                ))
            elif self.config.source_type == 'influxdb':
                data = pd.DataFrame(self.source_client.query(
                    f"{source['query']} WHERE time > '{last_migration}'"
                ).get_points())
            elif self.config.source_type == 'clickhouse':
                data = pd.DataFrame(self.source_client.execute(
                    f"{source['query']} WHERE updated_at > '{last_migration}'"
                ))
            elif self.config.source_type == 'vertica':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'snowflake':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'bigquery':
                data = self.source_client.query(
                    f"{source['query']} WHERE updated_at > '{last_migration}'"
                ).to_dataframe()
            elif self.config.target_type == 'redshift':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'teradata':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'oracle':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'sqlserver':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'db2':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'sqlite':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            
            # Write data to target
            if self.config.target_type == 'postgresql':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'mysql':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'mongodb':
                self.target_client[target['database']][target['collection']].insert_many(data.to_dict('records'))
            elif self.config.target_type == 'redis':
                self.target_client.hmset(target['key'], data.to_dict())
            elif self.config.target_type == 'elasticsearch':
                self.target_client.bulk(data.to_dict('records'))
            elif self.config.target_type == 'neo4j':
                self.target_client.run(target['query'], data=data.to_dict('records'))
            elif self.config.target_type == 'cassandra':
                self.target_client.execute(target['query'], data.to_dict('records'))
            elif self.config.target_type == 'influxdb':
                self.target_client.write_points(data.to_dict('records'))
            elif self.config.target_type == 'clickhouse':
                self.target_client.execute(target['query'], data.to_dict('records'))
            elif self.config.target_type == 'vertica':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'snowflake':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'bigquery':
                self.target_client.load_table_from_dataframe(data, target['table'])
            elif self.config.target_type == 'redshift':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'teradata':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'oracle':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'sqlserver':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'db2':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'sqlite':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            
        except Exception as e:
            print(f"Error executing incremental migration: {str(e)}")
            raise

    def _execute_differential_migration(self, source: Dict, target: Dict) -> None:
        """Execute a differential migration."""
        try:
            # Get last migration timestamp
            last_migration = self._get_last_migration_time()
            
            # Read differential data from source
            if self.config.source_type == 'postgresql':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.source_type == 'mysql':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.source_type == 'mongodb':
                data = pd.DataFrame(list(self.source_client[source['database']][source['collection']].find({
                    'updated_at': {'$gt': last_migration}
                })))
            elif self.config.source_type == 'redis':
                data = pd.DataFrame(self.source_client.hgetall(source['key']))
            elif self.config.source_type == 'elasticsearch':
                data = pd.DataFrame(self.source_client.search(**{
                    **source,
                    'query': {
                        'range': {
                            'updated_at': {
                                'gt': last_migration
                            }
                        }
                    }
                }))
            elif self.config.source_type == 'neo4j':
                data = pd.DataFrame(self.source_client.run(
                    f"{source['query']} WHERE n.updated_at > '{last_migration}'"
                ).data())
            elif self.config.source_type == 'cassandra':
                data = pd.DataFrame(self.source_client.execute(
                    f"{source['query']} WHERE updated_at > '{last_migration}'"
                ))
            elif self.config.source_type == 'influxdb':
                data = pd.DataFrame(self.source_client.query(
                    f"{source['query']} WHERE time > '{last_migration}'"
                ).get_points())
            elif self.config.source_type == 'clickhouse':
                data = pd.DataFrame(self.source_client.execute(
                    f"{source['query']} WHERE updated_at > '{last_migration}'"
                ))
            elif self.config.source_type == 'vertica':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'snowflake':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'bigquery':
                data = self.source_client.query(
                    f"{source['query']} WHERE updated_at > '{last_migration}'"
                ).to_dataframe()
            elif self.config.target_type == 'redshift':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'teradata':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'oracle':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'sqlserver':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'db2':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            elif self.config.target_type == 'sqlite':
                data = pd.read_sql(
                    f"{source['query']} WHERE updated_at > '{last_migration}'",
                    self.source_client
                )
            
            # Write data to target
            if self.config.target_type == 'postgresql':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'mysql':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'mongodb':
                self.target_client[target['database']][target['collection']].insert_many(data.to_dict('records'))
            elif self.config.target_type == 'redis':
                self.target_client.hmset(target['key'], data.to_dict())
            elif self.config.target_type == 'elasticsearch':
                self.target_client.bulk(data.to_dict('records'))
            elif self.config.target_type == 'neo4j':
                self.target_client.run(target['query'], data=data.to_dict('records'))
            elif self.config.target_type == 'cassandra':
                self.target_client.execute(target['query'], data.to_dict('records'))
            elif self.config.target_type == 'influxdb':
                self.target_client.write_points(data.to_dict('records'))
            elif self.config.target_type == 'clickhouse':
                self.target_client.execute(target['query'], data.to_dict('records'))
            elif self.config.target_type == 'vertica':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'snowflake':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'bigquery':
                self.target_client.load_table_from_dataframe(data, target['table'])
            elif self.config.target_type == 'redshift':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'teradata':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'oracle':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'sqlserver':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'db2':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            elif self.config.target_type == 'sqlite':
                data.to_sql(target['table'], self.target_client, if_exists='append', index=False)
            
        except Exception as e:
            print(f"Error executing differential migration: {str(e)}")
            raise

    def _execute_snapshot_migration(self, source: Dict, target: Dict) -> None:
        """Execute a snapshot migration."""
        try:
            # Read data from source
            if self.config.source_type == 'postgresql':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'mysql':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'mongodb':
                data = pd.DataFrame(list(self.source_client[source['database']][source['collection']].find()))
            elif self.config.source_type == 'redis':
                data = pd.DataFrame(self.source_client.hgetall(source['key']))
            elif self.config.source_type == 'elasticsearch':
                data = pd.DataFrame(self.source_client.search(**source))
            elif self.config.source_type == 'neo4j':
                data = pd.DataFrame(self.source_client.run(source['query']).data())
            elif self.config.source_type == 'cassandra':
                data = pd.DataFrame(self.source_client.execute(source['query']))
            elif self.config.source_type == 'influxdb':
                data = pd.DataFrame(self.source_client.query(source['query']).get_points())
            elif self.config.source_type == 'clickhouse':
                data = pd.DataFrame(self.source_client.execute(source['query']))
            elif self.config.source_type == 'vertica':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'snowflake':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'bigquery':
                data = self.source_client.query(source['query']).to_dataframe()
            elif self.config.source_type == 'redshift':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'teradata':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'oracle':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'sqlserver':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'db2':
                data = pd.read_sql(source['query'], self.source_client)
            elif self.config.source_type == 'sqlite':
                data = pd.read_sql(source['query'], self.source_client)
            
            # Write data to target
            if self.config.target_type == 'postgresql':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'mysql':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'mongodb':
                self.target_client[target['database']][target['collection']].insert_many(data.to_dict('records'))
            elif self.config.target_type == 'redis':
                self.target_client.hmset(target['key'], data.to_dict())
            elif self.config.target_type == 'elasticsearch':
                self.target_client.bulk(data.to_dict('records'))
            elif self.config.target_type == 'neo4j':
                self.target_client.run(target['query'], data=data.to_dict('records'))
            elif self.config.target_type == 'cassandra':
                self.target_client.execute(target['query'], data.to_dict('records'))
            elif self.config.target_type == 'influxdb':
                self.target_client.write_points(data.to_dict('records'))
            elif self.config.target_type == 'clickhouse':
                self.target_client.execute(target['query'], data.to_dict('records'))
            elif self.config.target_type == 'vertica':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'snowflake':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'bigquery':
                self.target_client.load_table_from_dataframe(data, target['table'])
            elif self.config.target_type == 'redshift':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'teradata':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'oracle':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'sqlserver':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'db2':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            elif self.config.target_type == 'sqlite':
                data.to_sql(target['table'], self.target_client, if_exists='replace', index=False)
            
        except Exception as e:
            print(f"Error executing snapshot migration: {str(e)}")
            raise

    def _get_last_migration_time(self) -> str:
        """Get timestamp of last migration."""
        try:
            # Get last migration time from target
            if self.config.target_type == 'postgresql':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'mysql':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'mongodb':
                result = self.target_client['migration_log']['migrations'].find_one(
                    sort=[('updated_at', -1)]
                )
                return result['updated_at']
            elif self.config.target_type == 'redis':
                return self.target_client.get('last_migration')
            elif self.config.target_type == 'elasticsearch':
                result = self.target_client.search(
                    index='migration_log',
                    body={
                        'query': {
                            'match_all': {}
                        },
                        'sort': [
                            {'updated_at': 'desc'}
                        ],
                        'size': 1
                    }
                )
                return result['hits']['hits'][0]['_source']['updated_at']
            elif self.config.target_type == 'neo4j':
                result = self.target_client.run(
                    "MATCH (m:Migration) RETURN m.updated_at ORDER BY m.updated_at DESC LIMIT 1"
                ).data()
                return result[0]['m.updated_at']
            elif self.config.target_type == 'cassandra':
                result = self.target_client.execute(
                    "SELECT updated_at FROM migration_log ORDER BY updated_at DESC LIMIT 1"
                )
                return result[0].updated_at
            elif self.config.target_type == 'influxdb':
                result = self.target_client.query(
                    "SELECT last(updated_at) FROM migration_log"
                ).get_points()
                return next(result)['last']
            elif self.config.target_type == 'clickhouse':
                result = self.target_client.execute(
                    "SELECT updated_at FROM migration_log ORDER BY updated_at DESC LIMIT 1"
                )
                return result[0][0]
            elif self.config.target_type == 'vertica':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'snowflake':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'bigquery':
                result = self.target_client.query(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log"
                ).to_dataframe()
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'redshift':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'teradata':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'oracle':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'sqlserver':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'db2':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            elif self.config.target_type == 'sqlite':
                result = pd.read_sql(
                    "SELECT MAX(updated_at) as last_migration FROM migration_log",
                    self.target_client
                )
                return result['last_migration'].iloc[0]
            
        except Exception as e:
            print(f"Error getting last migration time: {str(e)}")
            raise

    def create_migration(self, source: Dict, target: Dict, migration_type: str = 'full') -> str:
        """Create a new migration."""
        try:
            # Generate migration ID
            migration_id = str(uuid.uuid4())
            
            # Create migration
            migration = {
                'id': migration_id,
                'type': migration_type,
                'source': source,
                'target': target,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add to queue
            self.migration_queue.put(migration)
            
            return migration_id
            
        except Exception as e:
            print(f"Error creating migration: {str(e)}")
            raise

    def get_migration_stats(self) -> Dict:
        """Get migration statistics."""
        try:
            stats = {
                'queue_size': self.migration_queue.qsize(),
                'processing': self.processing,
                'migration_count': len(self._get_migration_files()),
                'last_migration': self._get_last_migration_time()
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting migration stats: {str(e)}")
            raise

    def _get_migration_files(self) -> List[str]:
        """Get list of migration files."""
        try:
            migration_files = []
            for root, dirs, files in os.walk('migrations'):
                for file in files:
                    if file.endswith('.py'):
                        migration_files.append(os.path.join(root, file))
            return migration_files
            
        except Exception as e:
            print(f"Error getting migration files: {str(e)}")
            raise

    def clear_migrations(self) -> None:
        """Clear all migrations."""
        try:
            # Clear queue
            while not self.migration_queue.empty():
                self.migration_queue.get()
                self.migration_queue.task_done()
            
            # Remove migration files
            for migration_file in self._get_migration_files():
                os.remove(migration_file)
            
        except Exception as e:
            print(f"Error clearing migrations: {str(e)}")
            raise

    def init_migrations(self):
        """Initialize database migrations."""
        try:
            with self.app.app_context():
                self.migrate.init_app(self.app, db)
                self.logger.info('Database migrations initialized successfully')
        except Exception as e:
            self.logger.error(f'Failed to initialize database migrations: {str(e)}')
            raise
    
    def create_migration(self, message):
        """Create a new migration."""
        try:
            with self.app.app_context():
                self.migrate.migrate(message=message)
                self.logger.info(f'Created new migration: {message}')
        except Exception as e:
            self.logger.error(f'Failed to create migration: {str(e)}')
            raise
    
    def upgrade_database(self, revision='head'):
        """Upgrade database to specified revision."""
        try:
            with self.app.app_context():
                self.migrate.upgrade(revision=revision)
                self.logger.info(f'Database upgraded to revision: {revision}')
        except Exception as e:
            self.logger.error(f'Failed to upgrade database: {str(e)}')
            raise
    
    def downgrade_database(self, revision):
        """Downgrade database to specified revision."""
        try:
            with self.app.app_context():
                self.migrate.downgrade(revision=revision)
                self.logger.info(f'Database downgraded to revision: {revision}')
        except Exception as e:
            self.logger.error(f'Failed to downgrade database: {str(e)}')
            raise
    
    def get_migration_history(self):
        """Get database migration history."""
        try:
            with self.app.app_context():
                history = self.migrate.history()
                return history
        except Exception as e:
            self.logger.error(f'Failed to get migration history: {str(e)}')
            raise
    
    def get_current_revision(self):
        """Get current database revision."""
        try:
            with self.app.app_context():
                current = self.migrate.current()
                return current
        except Exception as e:
            self.logger.error(f'Failed to get current revision: {str(e)}')
            raise
    
    def check_migration_status(self):
        """Check if database is up to date."""
        try:
            with self.app.app_context():
                current = self.migrate.current()
                head = self.migrate.head()
                return current == head
        except Exception as e:
            self.logger.error(f'Failed to check migration status: {str(e)}')
            raise
    
    def create_initial_schema(self):
        """Create initial database schema."""
        try:
            with self.app.app_context():
                db.create_all()
                self.logger.info('Initial database schema created successfully')
        except Exception as e:
            self.logger.error(f'Failed to create initial schema: {str(e)}')
            raise
    
    def update_schema(self):
        """Update database schema based on model changes."""
        try:
            with self.app.app_context():
                db.create_all()
                self.logger.info('Database schema updated successfully')
        except Exception as e:
            self.logger.error(f'Failed to update schema: {str(e)}')
            raise
    
    def backup_schema(self):
        """Backup current database schema."""
        try:
            with self.app.app_context():
                # Get current schema
                schema = db.metadata.tables
                
                # Save schema to file
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f'schema_backup_{timestamp}.sql'
                
                with open(filename, 'w') as f:
                    for table in schema.values():
                        f.write(f'-- Table: {table.name}\n')
                        f.write(f'CREATE TABLE IF NOT EXISTS {table.name} (\n')
                        
                        for column in table.columns:
                            f.write(f'    {column.name} {column.type},\n')
                        
                        f.write(');\n\n')
                
                self.logger.info(f'Schema backup created: {filename}')
                return filename
        except Exception as e:
            self.logger.error(f'Failed to backup schema: {str(e)}')
            raise
    
    def restore_schema(self, backup_file):
        """Restore database schema from backup."""
        try:
            with self.app.app_context():
                # Read backup file
                with open(backup_file, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema SQL
                db.session.execute(schema_sql)
                db.session.commit()
                
                self.logger.info(f'Schema restored from backup: {backup_file}')
        except Exception as e:
            self.logger.error(f'Failed to restore schema: {str(e)}')
            raise
    
    def validate_schema(self):
        """Validate database schema against models."""
        try:
            with self.app.app_context():
                # Get current schema
                current_schema = db.metadata.tables
                
                # Get model schema
                model_schema = {}
                for model in db.Model.__subclasses__():
                    model_schema[model.__tablename__] = model.__table__
                
                # Compare schemas
                differences = []
                for table_name, table in model_schema.items():
                    if table_name not in current_schema:
                        differences.append(f'Missing table: {table_name}')
                    else:
                        current_table = current_schema[table_name]
                        for column in table.columns:
                            if column.name not in current_table.columns:
                                differences.append(f'Missing column: {table_name}.{column.name}')
                
                if differences:
                    self.logger.warning('Schema validation found differences:')
                    for diff in differences:
                        self.logger.warning(diff)
                    return False
                
                self.logger.info('Schema validation successful')
                return True
        except Exception as e:
            self.logger.error(f'Failed to validate schema: {str(e)}')
            raise

# Example usage
if __name__ == "__main__":
    # Create migration instance
    migration = DataMigration()
    
    # Create migration
    migration_id = migration.create_migration(
        source={
            'type': 'postgresql',
            'query': 'SELECT * FROM sales'
        },
        target={
            'type': 'mysql',
            'table': 'sales'
        },
        migration_type='full'
    )
    
    # Get migration stats
    stats = migration.get_migration_stats()
    print(f"Migration stats: {stats}")
    
    # Clear migrations
    migration.clear_migrations() 