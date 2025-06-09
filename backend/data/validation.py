import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any
import json
import yaml
import os
from dataclasses import dataclass
import jsonschema
from jsonschema import validate
import cerberus
from cerberus import Validator
import voluptuous
from voluptuous import Schema, Required, Optional as VoluptuousOptional
import marshmallow
from marshmallow import Schema as MarshmallowSchema, fields, validate as marshmallow_validate
import pydantic
from pydantic import BaseModel, Field, validator
import logging
import re
from datetime import datetime
import pytz
import hashlib
import time

@dataclass
class ValidationConfig:
    """Configuration for the validation system."""
    schema_dir: str
    validation_level: str
    strict_mode: bool
    custom_rules: Dict
    error_threshold: float
    warning_threshold: float

class DataValidator:
    def __init__(self, config_path: str = 'config/validation_config.yaml'):
        """Initialize the data validator."""
        self.config_path = config_path
        self.config = self._load_config()
        self.schemas = {}
        self.validators = {}
        
        # Load schemas
        self._load_schemas()
        
        # Initialize validators
        self._init_validators()

    def _load_config(self) -> ValidationConfig:
        """Load validation configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return ValidationConfig(**config_dict)
        except Exception as e:
            print(f"Error loading validation configuration: {str(e)}")
            raise

    def _load_schemas(self) -> None:
        """Load validation schemas."""
        try:
            # Load JSON schemas
            json_schema_dir = os.path.join(self.config.schema_dir, 'json')
            if os.path.exists(json_schema_dir):
                for file in os.listdir(json_schema_dir):
                    if file.endswith('.json'):
                        with open(os.path.join(json_schema_dir, file), 'r') as f:
                            schema_name = os.path.splitext(file)[0]
                            self.schemas[schema_name] = json.load(f)
            
            # Load YAML schemas
            yaml_schema_dir = os.path.join(self.config.schema_dir, 'yaml')
            if os.path.exists(yaml_schema_dir):
                for file in os.listdir(yaml_schema_dir):
                    if file.endswith('.yaml'):
                        with open(os.path.join(yaml_schema_dir, file), 'r') as f:
                            schema_name = os.path.splitext(file)[0]
                            self.schemas[schema_name] = yaml.safe_load(f)
            
        except Exception as e:
            print(f"Error loading schemas: {str(e)}")
            raise

    def _init_validators(self) -> None:
        """Initialize validation engines."""
        try:
            # Initialize Cerberus validator
            self.validators['cerberus'] = Validator()
            
            # Initialize Voluptuous schemas
            self.validators['voluptuous'] = {}
            for name, schema in self.schemas.items():
                self.validators['voluptuous'][name] = Schema(schema)
            
            # Initialize Marshmallow schemas
            self.validators['marshmallow'] = {}
            for name, schema in self.schemas.items():
                self.validators['marshmallow'][name] = self._create_marshmallow_schema(schema)
            
            # Initialize Pydantic models
            self.validators['pydantic'] = {}
            for name, schema in self.schemas.items():
                self.validators['pydantic'][name] = self._create_pydantic_model(schema)
            
        except Exception as e:
            print(f"Error initializing validators: {str(e)}")
            raise

    def _create_marshmallow_schema(self, schema: Dict) -> MarshmallowSchema:
        """Create a Marshmallow schema from a dictionary."""
        try:
            class DynamicSchema(MarshmallowSchema):
                pass
            
            for field_name, field_spec in schema.items():
                field_type = self._get_marshmallow_field_type(field_spec)
                setattr(DynamicSchema, field_name, field_type)
            
            return DynamicSchema()
            
        except Exception as e:
            print(f"Error creating Marshmallow schema: {str(e)}")
            raise

    def _create_pydantic_model(self, schema: Dict) -> BaseModel:
        """Create a Pydantic model from a dictionary."""
        try:
            class DynamicModel(BaseModel):
                pass
            
            for field_name, field_spec in schema.items():
                field_type = self._get_pydantic_field_type(field_spec)
                setattr(DynamicModel, field_name, field_type)
            
            return DynamicModel
            
        except Exception as e:
            print(f"Error creating Pydantic model: {str(e)}")
            raise

    def _get_marshmallow_field_type(self, field_spec: Dict) -> fields.Field:
        """Get the appropriate Marshmallow field type."""
        try:
            field_type = field_spec.get('type', 'string')
            
            if field_type == 'string':
                return fields.String(required=field_spec.get('required', False))
            elif field_type == 'integer':
                return fields.Integer(required=field_spec.get('required', False))
            elif field_type == 'float':
                return fields.Float(required=field_spec.get('required', False))
            elif field_type == 'boolean':
                return fields.Boolean(required=field_spec.get('required', False))
            elif field_type == 'datetime':
                return fields.DateTime(required=field_spec.get('required', False))
            else:
                return fields.String(required=field_spec.get('required', False))
            
        except Exception as e:
            print(f"Error getting Marshmallow field type: {str(e)}")
            raise

    def _get_pydantic_field_type(self, field_spec: Dict) -> Any:
        """Get the appropriate Pydantic field type."""
        try:
            field_type = field_spec.get('type', 'string')
            
            if field_type == 'string':
                return Field(None, description=field_spec.get('description', ''))
            elif field_type == 'integer':
                return Field(None, description=field_spec.get('description', ''))
            elif field_type == 'float':
                return Field(None, description=field_spec.get('description', ''))
            elif field_type == 'boolean':
                return Field(None, description=field_spec.get('description', ''))
            elif field_type == 'datetime':
                return Field(None, description=field_spec.get('description', ''))
            else:
                return Field(None, description=field_spec.get('description', ''))
            
        except Exception as e:
            print(f"Error getting Pydantic field type: {str(e)}")
            raise

    def validate_data(self, data: Any, schema_name: str, engine: str = 'jsonschema') -> Tuple[bool, List[str]]:
        """Validate data against a schema using the specified engine."""
        try:
            if engine not in ['jsonschema', 'cerberus', 'voluptuous', 'marshmallow', 'pydantic']:
                raise ValueError(f"Unsupported validation engine: {engine}")
            
            if schema_name not in self.schemas:
                raise ValueError(f"Schema not found: {schema_name}")
            
            errors = []
            
            if engine == 'jsonschema':
                try:
                    validate(instance=data, schema=self.schemas[schema_name])
                except jsonschema.exceptions.ValidationError as e:
                    errors.append(str(e))
            
            elif engine == 'cerberus':
                if not self.validators['cerberus'].validate(data, self.schemas[schema_name]):
                    errors.extend(self.validators['cerberus'].errors)
            
            elif engine == 'voluptuous':
                try:
                    self.validators['voluptuous'][schema_name](data)
                except voluptuous.Invalid as e:
                    errors.append(str(e))
            
            elif engine == 'marshmallow':
                result = self.validators['marshmallow'][schema_name].load(data)
                if result.errors:
                    errors.extend(result.errors)
            
            elif engine == 'pydantic':
                try:
                    self.validators['pydantic'][schema_name](**data)
                except pydantic.ValidationError as e:
                    errors.extend(str(err) for err in e.errors())
            
            return len(errors) == 0, errors
            
        except Exception as e:
            print(f"Error validating data: {str(e)}")
            raise

    def validate_dataframe(self, df: pd.DataFrame, schema_name: str) -> Tuple[bool, Dict[str, List[str]]]:
        """Validate a pandas DataFrame against a schema."""
        try:
            if schema_name not in self.schemas:
                raise ValueError(f"Schema not found: {schema_name}")
            
            schema = self.schemas[schema_name]
            errors = {}
            
            # Validate column types
            for column, dtype in df.dtypes.items():
                if column in schema:
                    expected_type = schema[column].get('type')
                    if expected_type == 'string' and not pd.api.types.is_string_dtype(dtype):
                        errors.setdefault(column, []).append(f"Expected string type, got {dtype}")
                    elif expected_type == 'integer' and not pd.api.types.is_integer_dtype(dtype):
                        errors.setdefault(column, []).append(f"Expected integer type, got {dtype}")
                    elif expected_type == 'float' and not pd.api.types.is_float_dtype(dtype):
                        errors.setdefault(column, []).append(f"Expected float type, got {dtype}")
                    elif expected_type == 'boolean' and not pd.api.types.is_bool_dtype(dtype):
                        errors.setdefault(column, []).append(f"Expected boolean type, got {dtype}")
                    elif expected_type == 'datetime' and not pd.api.types.is_datetime64_any_dtype(dtype):
                        errors.setdefault(column, []).append(f"Expected datetime type, got {dtype}")
            
            # Validate required columns
            for column, spec in schema.items():
                if spec.get('required', False) and column not in df.columns:
                    errors.setdefault(column, []).append("Required column missing")
            
            # Validate data constraints
            for column, spec in schema.items():
                if column in df.columns:
                    # Check minimum value
                    if 'minimum' in spec and df[column].min() < spec['minimum']:
                        errors.setdefault(column, []).append(f"Values below minimum {spec['minimum']}")
                    
                    # Check maximum value
                    if 'maximum' in spec and df[column].max() > spec['maximum']:
                        errors.setdefault(column, []).append(f"Values above maximum {spec['maximum']}")
                    
                    # Check pattern
                    if 'pattern' in spec:
                        pattern = re.compile(spec['pattern'])
                        invalid_values = df[column].astype(str).apply(lambda x: not pattern.match(x))
                        if invalid_values.any():
                            errors.setdefault(column, []).append(f"Values do not match pattern {spec['pattern']}")
                    
                    # Check unique
                    if spec.get('unique', False) and not df[column].is_unique:
                        errors.setdefault(column, []).append("Values are not unique")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            print(f"Error validating DataFrame: {str(e)}")
            raise

    def validate_batch(self, data_list: List[Any], schema_name: str, engine: str = 'jsonschema') -> Tuple[bool, List[Dict[str, List[str]]]]:
        """Validate a batch of data items."""
        try:
            results = []
            for data in data_list:
                is_valid, errors = self.validate_data(data, schema_name, engine)
                results.append({
                    'valid': is_valid,
                    'errors': errors
                })
            
            return all(r['valid'] for r in results), results
            
        except Exception as e:
            print(f"Error validating batch: {str(e)}")
            raise

    def get_validation_summary(self, validation_results: List[Dict[str, List[str]]]) -> Dict:
        """Generate a summary of validation results."""
        try:
            total = len(validation_results)
            valid = sum(1 for r in validation_results if r['valid'])
            invalid = total - valid
            
            error_types = {}
            for result in validation_results:
                for error in result['errors']:
                    error_type = error.split(':')[0] if ':' in error else error
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            
            return {
                'total': total,
                'valid': valid,
                'invalid': invalid,
                'error_types': error_types,
                'error_rate': invalid / total if total > 0 else 0
            }
            
        except Exception as e:
            print(f"Error generating validation summary: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Create validator
    validator = DataValidator()
    
    # Example data
    data = {
        'name': 'John Doe',
        'age': 30,
        'email': 'john@example.com'
    }
    
    # Validate data
    is_valid, errors = validator.validate_data(data, 'user')
    print(f"Is valid: {is_valid}")
    print(f"Errors: {errors}")
    
    # Example DataFrame
    df = pd.DataFrame({
        'name': ['John', 'Jane', 'Bob'],
        'age': [30, 25, 35],
        'email': ['john@example.com', 'jane@example.com', 'bob@example.com']
    })
    
    # Validate DataFrame
    is_valid, errors = validator.validate_dataframe(df, 'user')
    print(f"Is valid: {is_valid}")
    print(f"Errors: {errors}") 