from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=8), load_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    sku = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    category = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    quantity = fields.Int(required=True, validate=validate.Range(min=0))
    reorder_point = fields.Int(required=True, validate=validate.Range(min=0))
    expiry_date = fields.DateTime(allow_none=True)
    value = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class StoreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    address = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class TransactionSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    store_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    timestamp = fields.DateTime(dump_only=True)

class WeatherSchema(Schema):
    id = fields.Int(dump_only=True)
    store_id = fields.Int(required=True)
    temperature = fields.Float(required=True)
    condition = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    timestamp = fields.DateTime(dump_only=True)

class RouteSchema(Schema):
    id = fields.Int(dump_only=True)
    store_id = fields.Int(required=True)
    status = fields.Str(required=True, validate=validate.OneOf(['pending', 'active', 'completed', 'cancelled']))
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(allow_none=True)
    distance = fields.Float(allow_none=True)
    duration = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class DeliverySchema(Schema):
    id = fields.Int(dump_only=True)
    route_id = fields.Int(required=True)
    address = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))
    status = fields.Str(required=True, validate=validate.OneOf(['pending', 'in_transit', 'delivered', 'failed']))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ForecastSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    date = fields.DateTime(required=True)
    forecast = fields.Float(required=True)
    confidence_upper = fields.Float(allow_none=True)
    confidence_lower = fields.Float(allow_none=True)
    created_at = fields.DateTime(dump_only=True)

class LogSchema(Schema):
    id = fields.Int(dump_only=True)
    level = fields.Str(required=True, validate=validate.OneOf(['info', 'warning', 'error']))
    message = fields.Str(required=True)
    timestamp = fields.DateTime(dump_only=True) 