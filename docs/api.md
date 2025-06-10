# FlowCast API Documentation

## Overview

The FlowCast API provides endpoints for demand forecasting, inventory optimization, route optimization, and analytics. All endpoints return JSON responses and use standard HTTP status codes.

## Base URL

```
http://localhost:5000
```

## Authentication

All API endpoints require authentication using a Bearer token:

```http
Authorization: Bearer <your_token>
```

## Endpoints

### Demand Prediction

Predict future demand for products at specific locations.

```http
POST /predict-demand
```

#### Request Body

```json
{
    "product_id": "string",
    "store_id": "string",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
}
```

#### Response

```json
{
    "predictions": [
        {
            "date": "YYYY-MM-DD",
            "predicted_demand": number,
            "confidence": number
        }
    ],
    "confidence_intervals": {
        "lower": [number],
        "upper": [number]
    },
    "metrics": {
        "r2_score": number,
        "mae": number
    }
}
```

### Inventory Optimization

Calculate optimal inventory levels and generate recommendations.

```http
POST /optimize-inventory
```

#### Request Body

```json
{
    "product_id": "string",
    "store_id": "string",
    "current_inventory": {
        "current_stock": number,
        "days_until_expiry": number,
        "storage_temperature": number,
        "storage_humidity": number
    }
}
```

#### Response

```json
{
    "safety_stock": number,
    "reorder_point": number,
    "economic_order_quantity": number,
    "recommendations": [
        {
            "action": "string",
            "quantity": number,
            "urgency": "high|medium|low"
        }
    ],
    "metrics": {
        "service_level": number,
        "stockout_probability": number,
        "inventory_turnover": number
    }
}
```

### Route Optimization

Optimize delivery routes for multiple locations.

```http
POST /optimize-routes
```

#### Request Body

```json
{
    "locations": [
        {
            "lat": number,
            "lng": number
        }
    ],
    "demands": [number],
    "vehicle_capacity": number,
    "num_vehicles": number,
    "mode": "driving|walking|bicycling|transit"
}
```

#### Response

```json
{
    "routes": [
        {
            "vehicle_id": number,
            "route": [
                {
                    "location": {
                        "lat": number,
                        "lng": number
                    },
                    "demand": number
                }
            ],
            "distance": number,
            "duration": number
        }
    ],
    "total_distance": number,
    "total_duration": number,
    "route_polylines": ["string"],
    "metrics": {
        "num_vehicles": number,
        "vehicle_capacity": number,
        "total_demand": number,
        "average_route_distance": number,
        "average_route_duration": number
    }
}
```

### Analytics

Get comprehensive analytics and metrics.

```http
GET /analytics
```

#### Query Parameters

- `product_id` (string, required)
- `store_id` (string, required)
- `start_date` (YYYY-MM-DD, required)
- `end_date` (YYYY-MM-DD, required)

#### Response

```json
{
    "demand_metrics": {
        "total_demand": number,
        "average_daily_demand": number,
        "demand_volatility": number,
        "seasonal_factors": {
            "summer": number,
            "winter": number,
            "holiday": number
        }
    },
    "inventory_metrics": {
        "current_stock": number,
        "safety_stock": number,
        "reorder_point": number,
        "stockout_probability": number,
        "inventory_turnover": number
    },
    "route_metrics": {
        "total_distance": number,
        "total_duration": number,
        "average_route_distance": number,
        "average_route_duration": number,
        "fuel_efficiency": number
    },
    "waste_metrics": {
        "total_units": number,
        "expiring_units": number,
        "expiry_rate": number,
        "donatable_units": number,
        "donation_rate": number
    }
}
```

## Error Handling

All endpoints return standard HTTP status codes:

- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

Error responses follow this format:

```json
{
    "error": "string",
    "message": "string",
    "details": {}
}
```

## Rate Limiting

API requests are limited to:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1612345678
```

## Caching

Responses are cached for 5 minutes by default. Cache headers are included in all responses:

```http
Cache-Control: public, max-age=300
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

## Webhooks

The API supports webhooks for real-time updates. Configure webhooks by sending a POST request to:

```http
POST /webhooks
```

#### Request Body

```json
{
    "url": "string",
    "events": ["demand_update", "inventory_update", "route_update"],
    "secret": "string"
}
```

## SDKs

Official SDKs are available for:
- Python
- JavaScript/TypeScript
- Java
- .NET

Example using Python SDK:

```python
from flowcast import FlowCastClient

client = FlowCastClient(api_key="your_api_key")

# Predict demand
predictions = client.predict_demand(
    product_id="PROD001",
    store_id="STORE001",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Optimize inventory
optimization = client.optimize_inventory(
    product_id="PROD001",
    store_id="STORE001",
    current_inventory={
        "current_stock": 100,
        "days_until_expiry": 5
    }
)

# Optimize routes
routes = client.optimize_routes(
    locations=[
        {"lat": 40.7128, "lng": -74.0060},
        {"lat": 40.7589, "lng": -73.9851}
    ],
    demands=[0, 100],
    vehicle_capacity=500,
    num_vehicles=2
)
```

## Changelog

### v1.0.0 (2024-01-01)
- Initial release
- Basic demand forecasting
- Inventory optimization
- Route optimization
- Analytics dashboard

### v1.1.0 (2024-02-01)
- Added webhook support
- Improved caching
- Enhanced error handling
- Added SDKs

## Support

For API support, please contact:
- Email: api-support@flowcast.com
- Documentation: https://docs.flowcast.com
- Status Page: https://status.flowcast.com 