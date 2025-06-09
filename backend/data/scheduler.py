import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import json
import yaml
import os
from dataclasses import dataclass
import time
from datetime import datetime, timedelta
import schedule
import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import threading
import logging
import hashlib
import uuid
import pickle
import queue
import asyncio
import signal
import sys
import traceback
import pytz
import croniter
import humanize
import psutil

@dataclass
class SchedulerConfig:
    """Configuration for the scheduler system."""
    timezone: str
    max_instances: int
    coalesce: bool
    misfire_grace_time: int
    job_defaults: Dict
    thread_pool_size: int
    process_pool_size: int
    enable_persistence: bool
    enable_logging: bool
    enable_metrics: bool

class DataScheduler:
    def __init__(self, config_path: str = 'config/scheduler_config.yaml'):
        """Initialize the scheduler system."""
        self.config_path = config_path
        self.config = self._load_config()
        self.scheduler = None
        self.jobs = {}
        self.job_stores = {}
        self.executors = {}
        self.running = False
        
        # Initialize scheduler
        self._init_scheduler()
        
        # Start scheduler
        self.start()

    def _load_config(self) -> SchedulerConfig:
        """Load scheduler configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return SchedulerConfig(**config_dict)
        except Exception as e:
            print(f"Error loading scheduler configuration: {str(e)}")
            raise

    def _init_scheduler(self) -> None:
        """Initialize the scheduler."""
        try:
            # Create scheduler
            self.scheduler = BackgroundScheduler(
                timezone=pytz.timezone(self.config.timezone),
                job_defaults=self.config.job_defaults
            )
            
            # Add job stores
            if self.config.enable_persistence:
                self.scheduler.add_jobstore(
                    'sqlalchemy',
                    url='sqlite:///jobs.sqlite'
                )
            
            # Add executors
            self.scheduler.add_executor(
                'threadpool',
                max_workers=self.config.thread_pool_size
            )
            
            self.scheduler.add_executor(
                'processpool',
                max_workers=self.config.process_pool_size
            )
            
            # Configure logging
            if self.config.enable_logging:
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
        except Exception as e:
            print(f"Error initializing scheduler: {str(e)}")
            raise

    def start(self) -> None:
        """Start the scheduler."""
        try:
            if not self.running:
                self.scheduler.start()
                self.running = True
            
        except Exception as e:
            print(f"Error starting scheduler: {str(e)}")
            raise

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        try:
            if self.running:
                self.scheduler.shutdown()
                self.running = False
            
        except Exception as e:
            print(f"Error shutting down scheduler: {str(e)}")
            raise

    def add_job(self, func: callable, trigger: str, **trigger_args) -> str:
        """Add a job to the scheduler."""
        try:
            # Generate job ID
            job_id = str(uuid.uuid4())
            
            # Add job to scheduler
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                **trigger_args
            )
            
            # Store job
            self.jobs[job_id] = job
            
            return job_id
            
        except Exception as e:
            print(f"Error adding job: {str(e)}")
            raise

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler."""
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
            
        except Exception as e:
            print(f"Error removing job: {str(e)}")
            raise

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job information."""
        try:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                return {
                    'id': job.id,
                    'name': job.name,
                    'func': job.func.__name__,
                    'trigger': str(job.trigger),
                    'next_run_time': job.next_run_time,
                    'coalesce': job.coalesce,
                    'misfire_grace_time': job.misfire_grace_time
                }
            return None
            
        except Exception as e:
            print(f"Error getting job: {str(e)}")
            raise

    def get_jobs(self) -> List[Dict]:
        """Get all jobs information."""
        try:
            return [
                self.get_job(job_id)
                for job_id in self.jobs
            ]
            
        except Exception as e:
            print(f"Error getting jobs: {str(e)}")
            raise

    def pause_job(self, job_id: str) -> None:
        """Pause a job."""
        try:
            if job_id in self.jobs:
                self.scheduler.pause_job(job_id)
            
        except Exception as e:
            print(f"Error pausing job: {str(e)}")
            raise

    def resume_job(self, job_id: str) -> None:
        """Resume a job."""
        try:
            if job_id in self.jobs:
                self.scheduler.resume_job(job_id)
            
        except Exception as e:
            print(f"Error resuming job: {str(e)}")
            raise

    def modify_job(self, job_id: str, **job_args) -> None:
        """Modify a job."""
        try:
            if job_id in self.jobs:
                self.scheduler.modify_job(job_id, **job_args)
            
        except Exception as e:
            print(f"Error modifying job: {str(e)}")
            raise

    def reschedule_job(self, job_id: str, trigger: str, **trigger_args) -> None:
        """Reschedule a job."""
        try:
            if job_id in self.jobs:
                self.scheduler.reschedule_job(job_id, trigger=trigger, **trigger_args)
            
        except Exception as e:
            print(f"Error rescheduling job: {str(e)}")
            raise

    def get_job_schedule(self, job_id: str) -> Optional[str]:
        """Get job schedule in human-readable format."""
        try:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                if isinstance(job.trigger, CronTrigger):
                    return str(job.trigger)
                elif isinstance(job.trigger, IntervalTrigger):
                    return f"Every {humanize.naturaldelta(job.trigger.interval)}"
                elif isinstance(job.trigger, DateTrigger):
                    return f"At {job.trigger.run_date}"
            return None
            
        except Exception as e:
            print(f"Error getting job schedule: {str(e)}")
            raise

    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Get next run time for a job."""
        try:
            if job_id in self.jobs:
                return self.jobs[job_id].next_run_time
            return None
            
        except Exception as e:
            print(f"Error getting next run time: {str(e)}")
            raise

    def get_job_count(self) -> int:
        """Get total number of jobs."""
        try:
            return len(self.jobs)
            
        except Exception as e:
            print(f"Error getting job count: {str(e)}")
            raise

    def get_running_jobs(self) -> List[Dict]:
        """Get currently running jobs."""
        try:
            running_jobs = []
            
            for job_id, job in self.jobs.items():
                if job.next_run_time is not None:
                    running_jobs.append(self.get_job(job_id))
            
            return running_jobs
            
        except Exception as e:
            print(f"Error getting running jobs: {str(e)}")
            raise

    def get_job_history(self, job_id: str, limit: int = 10) -> List[Dict]:
        """Get job execution history."""
        try:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                return [
                    {
                        'run_time': run_time,
                        'retval': retval,
                        'exception': str(exception) if exception else None,
                        'traceback': traceback.format_exc() if exception else None
                    }
                    for run_time, retval, exception in job.get_run_times(limit)
                ]
            return []
            
        except Exception as e:
            print(f"Error getting job history: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Create scheduler instance
    scheduler = DataScheduler()
    
    # Example job function
    def example_job():
        print("Running example job...")
    
    # Add job
    job_id = scheduler.add_job(
        example_job,
        'interval',
        minutes=5
    )
    
    # Get job information
    job_info = scheduler.get_job(job_id)
    print(f"Job info: {job_info}")
    
    # Get next run time
    next_run = scheduler.get_next_run_time(job_id)
    print(f"Next run time: {next_run}")
    
    # Get job schedule
    schedule = scheduler.get_job_schedule(job_id)
    print(f"Job schedule: {schedule}")
    
    # Get running jobs
    running_jobs = scheduler.get_running_jobs()
    print(f"Running jobs: {running_jobs}")
    
    # Shutdown scheduler
    scheduler.shutdown() 