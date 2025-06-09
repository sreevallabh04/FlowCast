# FlowCast - Supply Chain Forecasting & Optimization Platform

FlowCast is a comprehensive supply chain forecasting and optimization platform that leverages AI to predict demand, manage inventory, optimize delivery routes, and minimize waste. The system processes massive amounts of historical and real-time data to provide actionable insights for supply chain management.

## Features

- **Demand Forecasting**
  - Machine learning-based demand prediction
  - Weather, event, and economic factor integration
  - Confidence intervals for predictions
  - Real-time updates

- **Inventory Optimization**
  - Smart safety stock calculation
  - Dynamic reorder point prediction
  - Economic order quantity optimization
  - Multi-location inventory management

- **Route Optimization**
  - Real-time traffic-aware routing
  - Time window constraints
  - Multi-vehicle optimization
  - Delivery performance tracking

- **Waste Reduction**
  - Expiry prediction
  - Donation coordination
  - Markdown optimization
  - Freshness tracking

## Tech Stack

### Backend
- Python 3.9
- Flask (REST API)
- scikit-learn (ML models)
- OR-Tools (optimization)
- PostgreSQL (database)
- Redis (caching)

### Frontend
- React 18
- Material-UI
- Redux Toolkit
- Recharts
- Socket.IO

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 16+ (for local development)
- Python 3.9+ (for local development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flowcast.git
   cd flowcast
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - API Documentation: http://localhost:5000/docs

### Development Setup

1. Backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   flask run
   ```

2. Frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

## API Endpoints

### Demand Forecasting
- `POST /api/predict-demand` - Get demand predictions
- `GET /api/demand-metrics` - Get demand forecasting metrics

### Inventory Optimization
- `POST /api/optimize-inventory` - Optimize inventory levels
- `GET /api/inventory-metrics` - Get inventory metrics

### Route Optimization
- `POST /api/optimize-routes` - Optimize delivery routes
- `GET /api/routing-metrics` - Get routing metrics

### Analytics
- `GET /api/analytics` - Get comprehensive analytics

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenWeatherMap for weather data
- Google Maps for routing
- FRED for economic indicators 