import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import logging
from datetime import datetime
import json
import os
import yaml
from dataclasses import dataclass
import markdown
import jinja2
import sphinx
from sphinx.application import Sphinx
from sphinx.ext.autodoc import AutodocDirective
import pdoc
import inspect
import ast
import re
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import hashlib
import time

@dataclass
class DocumentationConfig:
    """Configuration for the documentation system."""
    output_dir: str
    template_dir: str
    api_docs_dir: str
    data_dictionary_dir: str
    pipeline_docs_dir: str
    format: str
    theme: str
    include_examples: bool
    include_diagrams: bool
    auto_generate: bool

class DataDocumentation:
    def __init__(self, config_path: str = 'config/doc_config.yaml'):
        """Initialize the documentation system with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize documentation state
        self.is_generating = False
        self.docs_status = {}
        
        # Set up database connection
        self.engine = create_engine(self.config.database_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Create necessary directories
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.template_dir, exist_ok=True)
        os.makedirs(self.config.api_docs_dir, exist_ok=True)
        os.makedirs(self.config.data_dictionary_dir, exist_ok=True)
        os.makedirs(self.config.pipeline_docs_dir, exist_ok=True)
        
        # Set up Jinja2 environment
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.config.template_dir)
        )

    def _load_config(self) -> DocumentationConfig:
        """Load documentation configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return DocumentationConfig(**config_dict)
        except Exception as e:
            self.logger.error(f"Error loading documentation configuration: {str(e)}")
            raise

    def generate_documentation(self, doc_type: str = 'all') -> Dict:
        """Generate documentation."""
        try:
            self.is_generating = True
            self.logger.info(f"Generating {doc_type} documentation")
            
            start_time = time.time()
            results = {
                'generated': [],
                'errors': []
            }
            
            if doc_type in ['all', 'api']:
                self._generate_api_documentation(results)
            
            if doc_type in ['all', 'data']:
                self._generate_data_dictionary(results)
            
            if doc_type in ['all', 'pipeline']:
                self._generate_pipeline_documentation(results)
            
            # Save documentation status
            self._save_documentation_status(results)
            
            duration = time.time() - start_time
            self.logger.info(f"Documentation generation completed in {duration:.2f} seconds")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating documentation: {str(e)}")
            raise
        finally:
            self.is_generating = False

    def _generate_api_documentation(self, results: Dict) -> None:
        """Generate API documentation."""
        try:
            # Generate API documentation using pdoc
            pdoc.pdoc(
                'backend/api',
                output_directory=self.config.api_docs_dir,
                format='html'
            )
            
            # Generate OpenAPI specification
            self._generate_openapi_spec()
            
            # Generate API examples
            if self.config.include_examples:
                self._generate_api_examples()
            
            results['generated'].append('api_documentation')
            
        except Exception as e:
            self.logger.error(f"Error generating API documentation: {str(e)}")
            results['errors'].append({
                'type': 'api',
                'error': str(e)
            })

    def _generate_data_dictionary(self, results: Dict) -> None:
        """Generate data dictionary."""
        try:
            # Get database schema
            inspector = sa.inspect(self.engine)
            
            # Generate table documentation
            for table_name in inspector.get_table_names():
                try:
                    # Get table information
                    columns = inspector.get_columns(table_name)
                    constraints = inspector.get_unique_constraints(table_name)
                    foreign_keys = inspector.get_foreign_keys(table_name)
                    indexes = inspector.get_indexes(table_name)
                    
                    # Generate table documentation
                    table_doc = {
                        'name': table_name,
                        'description': self._get_table_description(table_name),
                        'columns': [
                            {
                                'name': col['name'],
                                'type': str(col['type']),
                                'nullable': col['nullable'],
                                'default': str(col['default']) if col['default'] else None,
                                'description': self._get_column_description(table_name, col['name'])
                            }
                            for col in columns
                        ],
                        'constraints': [
                            {
                                'name': constraint['name'],
                                'columns': constraint['column_names'],
                                'type': 'unique'
                            }
                            for constraint in constraints
                        ],
                        'foreign_keys': [
                            {
                                'name': fk['name'],
                                'columns': fk['constrained_columns'],
                                'references': f"{fk['referred_table']}({','.join(fk['referred_columns'])})"
                            }
                            for fk in foreign_keys
                        ],
                        'indexes': [
                            {
                                'name': index['name'],
                                'columns': index['column_names'],
                                'unique': index['unique']
                            }
                            for index in indexes
                        ]
                    }
                    
                    # Save table documentation
                    self._save_table_documentation(table_name, table_doc)
                    
                except Exception as e:
                    self.logger.error(f"Error documenting table {table_name}: {str(e)}")
                    results['errors'].append({
                        'type': 'data_dictionary',
                        'table': table_name,
                        'error': str(e)
                    })
            
            results['generated'].append('data_dictionary')
            
        except Exception as e:
            self.logger.error(f"Error generating data dictionary: {str(e)}")
            results['errors'].append({
                'type': 'data_dictionary',
                'error': str(e)
            })

    def _generate_pipeline_documentation(self, results: Dict) -> None:
        """Generate pipeline documentation."""
        try:
            # Generate pipeline overview
            self._generate_pipeline_overview()
            
            # Generate component documentation
            self._generate_component_documentation()
            
            # Generate data flow diagrams
            if self.config.include_diagrams:
                self._generate_data_flow_diagrams()
            
            # Generate configuration documentation
            self._generate_configuration_documentation()
            
            results['generated'].append('pipeline_documentation')
            
        except Exception as e:
            self.logger.error(f"Error generating pipeline documentation: {str(e)}")
            results['errors'].append({
                'type': 'pipeline',
                'error': str(e)
            })

    def _generate_openapi_spec(self) -> None:
        """Generate OpenAPI specification."""
        try:
            # Load API routes
            routes = self._load_api_routes()
            
            # Generate OpenAPI specification
            openapi_spec = {
                'openapi': '3.0.0',
                'info': {
                    'title': 'FlowCast API',
                    'version': '1.0.0',
                    'description': 'API documentation for FlowCast'
                },
                'paths': {},
                'components': {
                    'schemas': {},
                    'securitySchemes': {}
                }
            }
            
            # Add paths
            for route in routes:
                path = route['path']
                method = route['method'].lower()
                
                if path not in openapi_spec['paths']:
                    openapi_spec['paths'][path] = {}
                
                openapi_spec['paths'][path][method] = {
                    'summary': route['summary'],
                    'description': route['description'],
                    'parameters': route['parameters'],
                    'responses': route['responses']
                }
            
            # Save OpenAPI specification
            spec_path = os.path.join(self.config.api_docs_dir, 'openapi.json')
            with open(spec_path, 'w') as f:
                json.dump(openapi_spec, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error generating OpenAPI specification: {str(e)}")
            raise

    def _generate_api_examples(self) -> None:
        """Generate API examples."""
        try:
            # Load API routes
            routes = self._load_api_routes()
            
            # Generate examples for each route
            for route in routes:
                try:
                    # Generate request example
                    request_example = self._generate_request_example(route)
                    
                    # Generate response example
                    response_example = self._generate_response_example(route)
                    
                    # Save examples
                    examples = {
                        'request': request_example,
                        'response': response_example
                    }
                    
                    example_path = os.path.join(
                        self.config.api_docs_dir,
                        'examples',
                        f"{route['path'].replace('/', '_')}_{route['method'].lower()}.json"
                    )
                    
                    with open(example_path, 'w') as f:
                        json.dump(examples, f, indent=2)
                    
                except Exception as e:
                    self.logger.error(f"Error generating examples for {route['path']}: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error generating API examples: {str(e)}")
            raise

    def _generate_pipeline_overview(self) -> None:
        """Generate pipeline overview documentation."""
        try:
            # Load pipeline configuration
            pipeline_config = self._load_pipeline_config()
            
            # Generate overview
            overview = {
                'name': 'FlowCast Data Pipeline',
                'description': 'End-to-end data pipeline for supply chain forecasting',
                'components': [
                    {
                        'name': 'Data Generator',
                        'description': 'Generates synthetic supply chain data',
                        'inputs': [],
                        'outputs': ['products', 'locations', 'suppliers', 'vehicles', 'events',
                                  'weather_data', 'sales_data', 'inventory_data', 'delivery_data']
                    },
                    {
                        'name': 'Data Processor',
                        'description': 'Processes and transforms supply chain data',
                        'inputs': ['products', 'locations', 'suppliers', 'vehicles', 'events',
                                 'weather_data', 'sales_data', 'inventory_data', 'delivery_data'],
                        'outputs': ['processed_data']
                    },
                    {
                        'name': 'Data Validator',
                        'description': 'Validates data quality and integrity',
                        'inputs': ['processed_data'],
                        'outputs': ['validation_results']
                    },
                    {
                        'name': 'Data Analyzer',
                        'description': 'Analyzes supply chain data',
                        'inputs': ['processed_data'],
                        'outputs': ['analysis_results']
                    }
                ],
                'configuration': pipeline_config
            }
            
            # Save overview
            overview_path = os.path.join(self.config.pipeline_docs_dir, 'overview.json')
            with open(overview_path, 'w') as f:
                json.dump(overview, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error generating pipeline overview: {str(e)}")
            raise

    def _generate_component_documentation(self) -> None:
        """Generate component documentation."""
        try:
            # Generate documentation for each component
            components = [
                'generator',
                'processor',
                'validator',
                'analyzer',
                'exporter',
                'pipeline',
                'monitor',
                'backup',
                'migration',
                'testing'
            ]
            
            for component in components:
                try:
                    # Load component code
                    component_path = f'backend/data/{component}.py'
                    with open(component_path, 'r') as f:
                        code = f.read()
                    
                    # Parse code
                    tree = ast.parse(code)
                    
                    # Extract documentation
                    doc = {
                        'name': component,
                        'description': self._extract_docstring(tree),
                        'classes': self._extract_classes(tree),
                        'functions': self._extract_functions(tree),
                        'dependencies': self._extract_dependencies(tree)
                    }
                    
                    # Save documentation
                    doc_path = os.path.join(self.config.pipeline_docs_dir, f'{component}.json')
                    with open(doc_path, 'w') as f:
                        json.dump(doc, f, indent=2)
                    
                except Exception as e:
                    self.logger.error(f"Error documenting component {component}: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error generating component documentation: {str(e)}")
            raise

    def _generate_data_flow_diagrams(self) -> None:
        """Generate data flow diagrams."""
        try:
            # Generate Mermaid diagrams
            diagrams = {
                'data_flow': self._generate_data_flow_mermaid(),
                'component_interaction': self._generate_component_interaction_mermaid(),
                'database_schema': self._generate_database_schema_mermaid()
            }
            
            # Save diagrams
            for name, diagram in diagrams.items():
                diagram_path = os.path.join(self.config.pipeline_docs_dir, f'{name}.mmd')
                with open(diagram_path, 'w') as f:
                    f.write(diagram)
            
        except Exception as e:
            self.logger.error(f"Error generating data flow diagrams: {str(e)}")
            raise

    def _generate_configuration_documentation(self) -> None:
        """Generate configuration documentation."""
        try:
            # Load all configuration files
            config_files = [
                'config/config.yaml',
                'config/generator_config.yaml',
                'config/processor_config.yaml',
                'config/validator_config.yaml',
                'config/analyzer_config.yaml',
                'config/exporter_config.yaml',
                'config/pipeline_config.yaml',
                'config/monitor_config.yaml',
                'config/backup_config.yaml',
                'config/migration_config.yaml',
                'config/testing_config.yaml',
                'config/doc_config.yaml'
            ]
            
            config_docs = {}
            
            for config_file in config_files:
                try:
                    # Load configuration
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    # Generate documentation
                    config_docs[config_file] = {
                        'description': self._get_config_description(config_file),
                        'parameters': self._document_config_parameters(config)
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error documenting configuration {config_file}: {str(e)}")
            
            # Save configuration documentation
            config_path = os.path.join(self.config.pipeline_docs_dir, 'configuration.json')
            with open(config_path, 'w') as f:
                json.dump(config_docs, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error generating configuration documentation: {str(e)}")
            raise

    def _save_documentation_status(self, results: Dict) -> None:
        """Save documentation generation status."""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'generated': results['generated'],
                'errors': results['errors']
            }
            
            status_path = os.path.join(self.config.output_dir, 'documentation_status.json')
            with open(status_path, 'w') as f:
                json.dump(status, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving documentation status: {str(e)}")
            raise

    def get_documentation_status(self) -> Dict:
        """Get current documentation status."""
        return {
            'is_generating': self.is_generating,
            'last_generated': self.docs_status.get('timestamp'),
            'generated_docs': self.docs_status.get('generated', []),
            'errors': self.docs_status.get('errors', [])
        }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and generate documentation
    documentation = DataDocumentation()
    results = documentation.generate_documentation() 