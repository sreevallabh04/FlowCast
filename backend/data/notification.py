import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import json
import yaml
import os
from dataclasses import dataclass
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import slack_sdk
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import twilio
from twilio.rest import Client
import telegram
from telegram.ext import Updater
import logging
import hashlib
import uuid
import threading
import queue
import asyncio
import aiohttp
import jinja2
import markdown
import html2text
import pytz
import schedule

@dataclass
class NotificationConfig:
    """Configuration for the notification system."""
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    slack_token: str
    slack_channel: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    telegram_token: str
    telegram_chat_id: str
    notification_queue_size: int
    retry_attempts: int
    retry_delay: int
    enable_email: bool
    enable_slack: bool
    enable_sms: bool
    enable_telegram: bool

class DataNotification:
    def __init__(self, config_path: str = 'config/notification_config.yaml'):
        """Initialize the notification system."""
        self.config_path = config_path
        self.config = self._load_config()
        self.notification_queue = queue.Queue(maxsize=self.config.notification_queue_size)
        self.processing = False
        self.processing_thread = None
        self.template_loader = jinja2.FileSystemLoader('templates')
        self.template_env = jinja2.Environment(loader=self.template_loader)
        
        # Initialize notification channels
        self._init_channels()
        
        # Start processing
        self.start_processing()

    def _load_config(self) -> NotificationConfig:
        """Load notification configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return NotificationConfig(**config_dict)
        except Exception as e:
            print(f"Error loading notification configuration: {str(e)}")
            raise

    def _init_channels(self) -> None:
        """Initialize notification channels."""
        try:
            # Initialize email
            if self.config.enable_email:
                self.smtp_server = smtplib.SMTP(
                    self.config.smtp_host,
                    self.config.smtp_port
                )
                self.smtp_server.starttls()
                self.smtp_server.login(
                    self.config.smtp_username,
                    self.config.smtp_password
                )
            
            # Initialize Slack
            if self.config.enable_slack:
                self.slack_client = WebClient(token=self.config.slack_token)
            
            # Initialize Twilio
            if self.config.enable_sms:
                self.twilio_client = Client(
                    self.config.twilio_account_sid,
                    self.config.twilio_auth_token
                )
            
            # Initialize Telegram
            if self.config.enable_telegram:
                self.telegram_updater = Updater(token=self.config.telegram_token)
                self.telegram_bot = self.telegram_updater.bot
            
        except Exception as e:
            print(f"Error initializing notification channels: {str(e)}")
            raise

    def start_processing(self) -> None:
        """Start notification processing."""
        try:
            if not self.processing:
                self.processing = True
                self.processing_thread = threading.Thread(target=self._process_notifications)
                self.processing_thread.daemon = True
                self.processing_thread.start()
            
        except Exception as e:
            print(f"Error starting notification processing: {str(e)}")
            raise

    def stop_processing(self) -> None:
        """Stop notification processing."""
        try:
            self.processing = False
            if self.processing_thread:
                self.processing_thread.join()
            
        except Exception as e:
            print(f"Error stopping notification processing: {str(e)}")
            raise

    def _process_notifications(self) -> None:
        """Process notifications from the queue."""
        try:
            while self.processing:
                try:
                    # Get notification from queue
                    notification = self.notification_queue.get(timeout=1)
                    
                    # Process notification
                    self._send_notification(notification)
                    
                    # Mark task as done
                    self.notification_queue.task_done()
                    
                except queue.Empty:
                    continue
                
        except Exception as e:
            print(f"Error processing notifications: {str(e)}")
            raise

    def _send_notification(self, notification: Dict) -> None:
        """Send a notification through the appropriate channel."""
        try:
            # Get notification type
            notification_type = notification.get('type')
            
            # Get notification template
            template = self._get_template(notification_type)
            
            # Render notification content
            content = self._render_template(template, notification)
            
            # Send through appropriate channels
            if self.config.enable_email and 'email' in notification.get('channels', []):
                self._send_email(notification['to'], notification['subject'], content)
            
            if self.config.enable_slack and 'slack' in notification.get('channels', []):
                self._send_slack(notification['channel'], content)
            
            if self.config.enable_sms and 'sms' in notification.get('channels', []):
                self._send_sms(notification['to'], content)
            
            if self.config.enable_telegram and 'telegram' in notification.get('channels', []):
                self._send_telegram(notification['chat_id'], content)
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            raise

    def _get_template(self, notification_type: str) -> str:
        """Get notification template."""
        try:
            template_path = f"notifications/{notification_type}.html"
            return self.template_env.get_template(template_path)
            
        except Exception as e:
            print(f"Error getting template: {str(e)}")
            raise

    def _render_template(self, template: jinja2.Template, data: Dict) -> str:
        """Render notification template with data."""
        try:
            return template.render(**data)
            
        except Exception as e:
            print(f"Error rendering template: {str(e)}")
            raise

    def _send_email(self, to: str, subject: str, content: str) -> None:
        """Send email notification."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username
            msg['To'] = to
            msg['Subject'] = subject
            
            # Add content
            msg.attach(MIMEText(content, 'html'))
            
            # Send email
            self.smtp_server.send_message(msg)
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise

    def _send_slack(self, channel: str, content: str) -> None:
        """Send Slack notification."""
        try:
            # Convert HTML to markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            markdown_content = h.handle(content)
            
            # Send message
            self.slack_client.chat_postMessage(
                channel=channel or self.config.slack_channel,
                text=markdown_content
            )
            
        except Exception as e:
            print(f"Error sending Slack message: {str(e)}")
            raise

    def _send_sms(self, to: str, content: str) -> None:
        """Send SMS notification."""
        try:
            # Convert HTML to plain text
            h = html2text.HTML2Text()
            h.ignore_links = True
            text_content = h.handle(content)
            
            # Send message
            self.twilio_client.messages.create(
                to=to,
                from_=self.config.twilio_phone_number,
                body=text_content
            )
            
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            raise

    def _send_telegram(self, chat_id: str, content: str) -> None:
        """Send Telegram notification."""
        try:
            # Convert HTML to markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            markdown_content = h.handle(content)
            
            # Send message
            self.telegram_bot.send_message(
                chat_id=chat_id or self.config.telegram_chat_id,
                text=markdown_content,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")
            raise

    def send_notification(self, notification: Dict) -> None:
        """Add a notification to the queue."""
        try:
            # Add notification ID and timestamp
            notification['id'] = str(uuid.uuid4())
            notification['timestamp'] = datetime.utcnow().isoformat()
            
            # Add to queue
            self.notification_queue.put(notification)
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            raise

    def get_notification_stats(self) -> Dict:
        """Get notification statistics."""
        try:
            stats = {
                'queue_size': self.notification_queue.qsize(),
                'queue_maxsize': self.notification_queue.maxsize,
                'processing': self.processing
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting notification stats: {str(e)}")
            raise

    def clear_notifications(self) -> None:
        """Clear all pending notifications."""
        try:
            while not self.notification_queue.empty():
                self.notification_queue.get()
                self.notification_queue.task_done()
            
        except Exception as e:
            print(f"Error clearing notifications: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Create notification instance
    notification = DataNotification()
    
    # Send notification
    notification.send_notification({
        'type': 'alert',
        'channels': ['email', 'slack'],
        'to': 'user@example.com',
        'subject': 'System Alert',
        'channel': '#alerts',
        'data': {
            'message': 'System is running low on resources',
            'severity': 'high',
            'timestamp': datetime.utcnow().isoformat()
        }
    })
    
    # Get notification stats
    stats = notification.get_notification_stats()
    print(f"Notification stats: {stats}")
    
    # Clear notifications
    notification.clear_notifications() 