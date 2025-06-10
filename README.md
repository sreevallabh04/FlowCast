# FlowCast - Supply Chain Analytics Platform

FlowCast is a comprehensive supply chain analytics platform that helps businesses optimize their operations through data-driven insights and forecasting.

## Features

- **Real-time Analytics Dashboard**
  - Sales trends and KPIs
  - Inventory status and alerts
  - Delivery tracking and optimization
  - Weather impact analysis

- **Demand Forecasting**
  - Machine learning-based predictions
  - Confidence interval analysis
  - Seasonal pattern detection
  - Product correlation analysis

- **Inventory Management**
  - Stock level monitoring
  - Reorder point alerts
  - Expiry date tracking
  - Value optimization

- **Route Optimization**
  - Delivery route planning
  - Real-time tracking
  - Weather-aware routing
  - Capacity optimization

- **Data Export & Integration**
  - Multiple export formats (CSV, JSON, Excel)
  - API integration
  - Webhook support
  - Automated backups

## Tech Stack

### Backend
- Flask (Python web framework)
- SQLAlchemy (ORM)
- JWT Authentication
- Redis (Caching)
- Pandas & NumPy (Data processing)
- Scikit-learn (Machine learning)
- Plotly (Data visualization)

### Frontend
- React.js
- Material-UI
- Chart.js
- Google Maps API

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- Redis
- PostgreSQL (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/flowcast.git
cd flowcast
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Set up the frontend:
```bash
cd ../frontend
npm install
```

6. Start the development servers:

Backend:
```bash
cd backend
flask run
```

Frontend:
```bash
cd frontend
npm start
```

## API Documentation

### Authentication
- POST /api/register - Register a new user
- POST /api/login - Login and get JWT token

### Dashboard
- GET /api/dashboard - Get dashboard data and KPIs

### Forecasting
- GET /api/forecast - Get demand forecasts
- GET /api/forecast/seasonal - Get seasonal patterns

### Inventory
- GET /api/inventory - Get inventory status
- PUT /api/inventory/:id - Update inventory

### Routes
- GET /api/routes - Get optimized routes
- GET /api/routes/:id/directions - Get route directions

### Analytics
- GET /api/analytics - Get analytics data
- GET /api/analytics/export - Export analytics data

### Webhooks
- POST /api/webhooks - Handle external webhooks

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [React](https://reactjs.org/)
- [Material-UI](https://material-ui.com/)
- [Chart.js](https://www.chartjs.org/)
- [Google Maps API](https://developers.google.com/maps)

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)
![Demand Forecast](docs/screenshots/demand.png)
![Inventory Optimization](docs/screenshots/inventory.png)
![Route Optimization](docs/screenshots/routes.png) 