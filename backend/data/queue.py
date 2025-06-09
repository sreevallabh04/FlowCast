import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import json
import yaml
import os
from dataclasses import dataclass
import time
from datetime import datetime, timedelta
import redis
from redis import Redis
import pika
import kombu
from kombu import Connection, Exchange, Queue
import threading
import logging
import hashlib
import uuid
import pickle
import queue
import asyncio
import aio_pika
from aio_pika import connect_robust, Message
import psutil
import signal
import sys
import traceback

@dataclass
class QueueConfig:
    """Configuration for the queue system."""
    redis_url: str
    rabbitmq_url: str
    queue_name: str
    exchange_name: str
    routing_key: str
    max_retries: int
    retry_delay: int
    batch_size: int
    prefetch_count: int
    enable_redis: bool
    enable_rabbitmq: bool
    enable_priority: bool
    enable_dlq: bool

class DataQueue:
    def __init__(self, config_path: str = 'config/queue_config.yaml'):
        """Initialize the queue system."""
        self.config_path = config_path
        self.config = self._load_config()
        self.redis_queue = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.rabbitmq_exchange = None
        self.rabbitmq_queue = None
        self.processing = False
        self.processing_thread = None
        self.message_handlers = {}
        self.error_handlers = {}
        
        # Initialize queue backends
        self._init_queue_backends()
        
        # Start processing
        self.start_processing()

    def _load_config(self) -> QueueConfig:
        """Load queue configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return QueueConfig(**config_dict)
        except Exception as e:
            print(f"Error loading queue configuration: {str(e)}")
            raise

    def _init_queue_backends(self) -> None:
        """Initialize queue backends."""
        try:
            # Initialize Redis queue
            if self.config.enable_redis:
                self.redis_queue = Redis.from_url(self.config.redis_url)
            
            # Initialize RabbitMQ queue
            if self.config.enable_rabbitmq:
                # Create connection
                self.rabbitmq_connection = pika.BlockingConnection(
                    pika.URLParameters(self.config.rabbitmq_url)
                )
                
                # Create channel
                self.rabbitmq_channel = self.rabbitmq_connection.channel()
                
                # Declare exchange
                self.rabbitmq_exchange = self.rabbitmq_channel.exchange_declare(
                    exchange=self.config.exchange_name,
                    exchange_type='direct',
                    durable=True
                )
                
                # Declare queue
                self.rabbitmq_queue = self.rabbitmq_channel.queue_declare(
                    queue=self.config.queue_name,
                    durable=True,
                    arguments={
                        'x-max-priority': 10 if self.config.enable_priority else None,
                        'x-dead-letter-exchange': f"{self.config.exchange_name}.dlq" if self.config.enable_dlq else None
                    }
                )
                
                # Bind queue to exchange
                self.rabbitmq_channel.queue_bind(
                    exchange=self.config.exchange_name,
                    queue=self.config.queue_name,
                    routing_key=self.config.routing_key
                )
                
                # Set prefetch count
                self.rabbitmq_channel.basic_qos(
                    prefetch_count=self.config.prefetch_count
                )
            
        except Exception as e:
            print(f"Error initializing queue backends: {str(e)}")
            raise

    def start_processing(self) -> None:
        """Start message processing."""
        try:
            if not self.processing:
                self.processing = True
                self.processing_thread = threading.Thread(target=self._process_messages)
                self.processing_thread.daemon = True
                self.processing_thread.start()
            
        except Exception as e:
            print(f"Error starting message processing: {str(e)}")
            raise

    def stop_processing(self) -> None:
        """Stop message processing."""
        try:
            self.processing = False
            if self.processing_thread:
                self.processing_thread.join()
            
        except Exception as e:
            print(f"Error stopping message processing: {str(e)}")
            raise

    def _process_messages(self) -> None:
        """Process messages from the queue."""
        try:
            while self.processing:
                # Process Redis messages
                if self.config.enable_redis:
                    self._process_redis_messages()
                
                # Process RabbitMQ messages
                if self.config.enable_rabbitmq:
                    self._process_rabbitmq_messages()
                
                # Sleep briefly to prevent CPU spinning
                time.sleep(0.1)
            
        except Exception as e:
            print(f"Error processing messages: {str(e)}")
            raise

    def _process_redis_messages(self) -> None:
        """Process messages from Redis queue."""
        try:
            # Get message from Redis
            message = self.redis_queue.blpop(self.config.queue_name, timeout=1)
            
            if message:
                _, message_data = message
                message_dict = json.loads(message_data)
                
                # Process message
                self._handle_message(message_dict)
            
        except Exception as e:
            print(f"Error processing Redis messages: {str(e)}")
            raise

    def _process_rabbitmq_messages(self) -> None:
        """Process messages from RabbitMQ queue."""
        try:
            # Get message from RabbitMQ
            method_frame, header_frame, body = self.rabbitmq_channel.basic_get(
                queue=self.config.queue_name,
                auto_ack=False
            )
            
            if method_frame:
                try:
                    # Parse message
                    message_dict = json.loads(body)
                    
                    # Process message
                    self._handle_message(message_dict)
                    
                    # Acknowledge message
                    self.rabbitmq_channel.basic_ack(method_frame.delivery_tag)
                    
                except Exception as e:
                    # Handle error
                    self._handle_error(message_dict, str(e))
                    
                    # Reject message
                    self.rabbitmq_channel.basic_nack(
                        method_frame.delivery_tag,
                        requeue=True
                    )
            
        except Exception as e:
            print(f"Error processing RabbitMQ messages: {str(e)}")
            raise

    def _handle_message(self, message: Dict) -> None:
        """Handle a message from the queue."""
        try:
            # Get message type
            message_type = message.get('type')
            
            # Get handler for message type
            handler = self.message_handlers.get(message_type)
            
            if handler:
                # Call handler
                handler(message)
            else:
                print(f"No handler found for message type: {message_type}")
            
        except Exception as e:
            print(f"Error handling message: {str(e)}")
            raise

    def _handle_error(self, message: Dict, error: str) -> None:
        """Handle an error during message processing."""
        try:
            # Get error handler
            handler = self.error_handlers.get('default')
            
            if handler:
                # Call error handler
                handler(message, error)
            else:
                print(f"Error processing message: {error}")
            
        except Exception as e:
            print(f"Error handling error: {str(e)}")
            raise

    def register_handler(self, message_type: str, handler: callable) -> None:
        """Register a message handler."""
        try:
            self.message_handlers[message_type] = handler
            
        except Exception as e:
            print(f"Error registering handler: {str(e)}")
            raise

    def register_error_handler(self, handler: callable) -> None:
        """Register an error handler."""
        try:
            self.error_handlers['default'] = handler
            
        except Exception as e:
            print(f"Error registering error handler: {str(e)}")
            raise

    def publish(self, message: Dict, priority: int = 0) -> None:
        """Publish a message to the queue."""
        try:
            # Add message ID and timestamp
            message['id'] = str(uuid.uuid4())
            message['timestamp'] = datetime.utcnow().isoformat()
            
            # Convert message to JSON
            message_json = json.dumps(message)
            
            # Publish to Redis
            if self.config.enable_redis:
                self.redis_queue.rpush(self.config.queue_name, message_json)
            
            # Publish to RabbitMQ
            if self.config.enable_rabbitmq:
                self.rabbitmq_channel.basic_publish(
                    exchange=self.config.exchange_name,
                    routing_key=self.config.routing_key,
                    body=message_json,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make message persistent
                        priority=priority if self.config.enable_priority else None
                    )
                )
            
        except Exception as e:
            print(f"Error publishing message: {str(e)}")
            raise

    def get_queue_stats(self) -> Dict:
        """Get queue statistics."""
        try:
            stats = {
                'redis_queue_length': self.redis_queue.llen(self.config.queue_name) if self.config.enable_redis else 0,
                'rabbitmq_queue_length': self.rabbitmq_queue.method.message_count if self.config.enable_rabbitmq else 0
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting queue stats: {str(e)}")
            raise

    def clear_queue(self) -> None:
        """Clear all messages from the queue."""
        try:
            # Clear Redis queue
            if self.config.enable_redis:
                self.redis_queue.delete(self.config.queue_name)
            
            # Clear RabbitMQ queue
            if self.config.enable_rabbitmq:
                self.rabbitmq_channel.queue_purge(queue=self.config.queue_name)
            
        except Exception as e:
            print(f"Error clearing queue: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Create queue instance
    queue = DataQueue()
    
    # Register message handler
    def handle_sales_message(message):
        print(f"Processing sales message: {message}")
    
    queue.register_handler('sales', handle_sales_message)
    
    # Register error handler
    def handle_error(message, error):
        print(f"Error processing message: {error}")
    
    queue.register_error_handler(handle_error)
    
    # Publish message
    queue.publish({
        'type': 'sales',
        'data': {
            'product_id': 123,
            'quantity': 5,
            'price': 99.99
        }
    })
    
    # Get queue stats
    stats = queue.get_queue_stats()
    print(f"Queue stats: {stats}")
    
    # Clear queue
    queue.clear_queue() 