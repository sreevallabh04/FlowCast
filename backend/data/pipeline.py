import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import os
import yaml
from dataclasses import dataclass
import asyncio
import aiohttp
import schedule
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
import signal
import sys

from .generator import DataGenerator
from .processor import DataProcessor
from .validator import DataValidator
from .analyzer import DataAnalyzer
from .exporter import DataExporter

@dataclass
class PipelineConfig:
    """Configuration for the data pipeline."""
    schedule: Dict[str, str]  # cron-style schedule for each step
    batch_size: int
    max_retries: int
    retry_delay: int
    timeout: int
    parallel_processing: bool
    max_workers: int

class DataPipeline:
    def __init__(self, config_path: str = 'config/pipeline_config.yaml'):
        """Initialize the data pipeline with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.generator = DataGenerator()
        self.processor = DataProcessor()
        self.validator = DataValidator()
        self.analyzer = DataAnalyzer()
        self.exporter = DataExporter()
        
        # Initialize pipeline state
        self.is_running = False
        self.current_batch = 0
        self.total_batches = 0
        self.last_run = {}
        self.next_run = {}
        
        # Initialize queues for parallel processing
        self.data_queue = Queue()
        self.result_queue = Queue()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _load_config(self) -> PipelineConfig:
        """Load pipeline configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return PipelineConfig(**config_dict)
        except Exception as e:
            self.logger.error(f"Error loading pipeline configuration: {str(e)}")
            raise

    async def run_pipeline(self, start_date: datetime, end_date: datetime) -> None:
        """Run the complete data pipeline."""
        try:
            self.is_running = True
            self.logger.info("Starting data pipeline")
            
            # Calculate batches
            date_range = pd.date_range(start_date, end_date, freq='D')
            self.total_batches = len(date_range) // self.config.batch_size + 1
            
            for batch_start in range(0, len(date_range), self.config.batch_size):
                batch_end = min(batch_start + self.config.batch_size, len(date_range))
                batch_dates = date_range[batch_start:batch_end]
                
                self.current_batch += 1
                self.logger.info(f"Processing batch {self.current_batch}/{self.total_batches}")
                
                # Run pipeline steps
                await self._run_generation(batch_dates)
                await self._run_processing()
                await self._run_validation()
                await self._run_analysis()
                await self._run_export()
                
                self.last_run = {
                    'batch': self.current_batch,
                    'start_date': batch_dates[0],
                    'end_date': batch_dates[-1],
                    'timestamp': datetime.now()
                }
            
            self.logger.info("Data pipeline completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in data pipeline: {str(e)}")
            raise
        finally:
            self.is_running = False

    async def _run_generation(self, dates: pd.DatetimeIndex) -> None:
        """Run data generation step."""
        try:
            self.logger.info("Starting data generation")
            
            if self.config.parallel_processing:
                with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                    futures = []
                    for date in dates:
                        future = executor.submit(
                            self.generator.generate_all_data,
                            date,
                            date
                        )
                        futures.append(future)
                    
                    for future in futures:
                        self.data_queue.put(future.result())
            else:
                for date in dates:
                    data = self.generator.generate_all_data(date, date)
                    self.data_queue.put(data)
            
            self.logger.info("Data generation completed")
            
        except Exception as e:
            self.logger.error(f"Error in data generation: {str(e)}")
            raise

    async def _run_processing(self) -> None:
        """Run data processing step."""
        try:
            self.logger.info("Starting data processing")
            
            while not self.data_queue.empty():
                data = self.data_queue.get()
                
                if self.config.parallel_processing:
                    with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                        future = executor.submit(self.processor.process_data, data)
                        self.result_queue.put(future.result())
                else:
                    processed_data = self.processor.process_data(data)
                    self.result_queue.put(processed_data)
            
            self.logger.info("Data processing completed")
            
        except Exception as e:
            self.logger.error(f"Error in data processing: {str(e)}")
            raise

    async def _run_validation(self) -> None:
        """Run data validation step."""
        try:
            self.logger.info("Starting data validation")
            
            while not self.result_queue.empty():
                data = self.result_queue.get()
                
                if self.config.parallel_processing:
                    with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                        future = executor.submit(self.validator.validate_data, data)
                        validation_result = future.result()
                else:
                    validation_result = self.validator.validate_data(data)
                
                if not validation_result.is_valid:
                    self.logger.warning(f"Validation failed: {validation_result.errors}")
                    continue
                
                self.data_queue.put(data)
            
            self.logger.info("Data validation completed")
            
        except Exception as e:
            self.logger.error(f"Error in data validation: {str(e)}")
            raise

    async def _run_analysis(self) -> None:
        """Run data analysis step."""
        try:
            self.logger.info("Starting data analysis")
            
            while not self.data_queue.empty():
                data = self.data_queue.get()
                
                if self.config.parallel_processing:
                    with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                        future = executor.submit(self.analyzer.analyze_data, data)
                        analysis_result = future.result()
                else:
                    analysis_result = self.analyzer.analyze_data(data)
                
                self.result_queue.put((data, analysis_result))
            
            self.logger.info("Data analysis completed")
            
        except Exception as e:
            self.logger.error(f"Error in data analysis: {str(e)}")
            raise

    async def _run_export(self) -> None:
        """Run data export step."""
        try:
            self.logger.info("Starting data export")
            
            while not self.result_queue.empty():
                data, analysis = self.result_queue.get()
                
                if self.config.parallel_processing:
                    with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                        future = executor.submit(self.exporter.export_data, data, analysis)
                        future.result()
                else:
                    self.exporter.export_data(data, analysis)
            
            self.logger.info("Data export completed")
            
        except Exception as e:
            self.logger.error(f"Error in data export: {str(e)}")
            raise

    def start_scheduled_pipeline(self) -> None:
        """Start the pipeline with scheduled runs."""
        try:
            self.logger.info("Starting scheduled pipeline")
            
            # Schedule pipeline runs
            for step, schedule_str in self.config.schedule.items():
                schedule.every().day.at(schedule_str).do(
                    self._run_scheduled_step,
                    step
                )
            
            # Run the scheduler
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error in scheduled pipeline: {str(e)}")
            raise

    async def _run_scheduled_step(self, step: str) -> None:
        """Run a scheduled pipeline step."""
        try:
            self.logger.info(f"Running scheduled step: {step}")
            
            # Get date range for the step
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.config.batch_size)
            
            # Run the step
            if step == 'generation':
                await self._run_generation(pd.date_range(start_date, end_date))
            elif step == 'processing':
                await self._run_processing()
            elif step == 'validation':
                await self._run_validation()
            elif step == 'analysis':
                await self._run_analysis()
            elif step == 'export':
                await self._run_export()
            
            self.next_run[step] = schedule.next_run()
            
        except Exception as e:
            self.logger.error(f"Error in scheduled step {step}: {str(e)}")
            raise

    def _handle_shutdown(self, signum: int, frame: None) -> None:
        """Handle pipeline shutdown."""
        self.logger.info("Shutting down pipeline")
        self.is_running = False
        sys.exit(0)

    def get_pipeline_status(self) -> Dict:
        """Get current pipeline status."""
        return {
            'is_running': self.is_running,
            'current_batch': self.current_batch,
            'total_batches': self.total_batches,
            'last_run': self.last_run,
            'next_run': self.next_run
        }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run pipeline
    pipeline = DataPipeline()
    
    # Run pipeline for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    asyncio.run(pipeline.run_pipeline(start_date, end_date)) 