# FlowCast Backend

This is the backend API for FlowCast, an inventory and route management system. It provides endpoints for managing inventory items, optimizing delivery routes, and handling user authentication.

## Features

- User authentication with JWT
- Inventory management with CRUD operations
- Route optimization and management
- API key generation for third-party integrations
- Rate limiting and security features
- MongoDB database integration

## Prerequisites

- Node.js (v14 or higher)
- MongoDB
- npm or yarn

## Installation

1. Clone the repository
2. Navigate to the backend directory:
   ```bash
   cd backend
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Create a `.env` file in the root directory with the following variables:
   ```
   NODE_ENV=development
   PORT=5000
   MONGODB_URI=mongodb://localhost:27017/flowcast
   JWT_SECRET=your_jwt_secret_key_here
   JWT_EXPIRE=30d
   RATE_LIMIT_WINDOW_MS=900000
   RATE_LIMIT_MAX=100
   ```

## Running the Application

### Development Mode
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

## API Endpoints

### Authentication
- POST /api/v1/auth/register - Register a new user
- POST /api/v1/auth/login - Login user
- GET /api/v1/auth/me - Get current user
- PUT /api/v1/auth/updatedetails - Update user details
- PUT /api/v1/auth/updatepassword - Update password
- POST /api/v1/auth/forgotpassword - Forgot password
- POST /api/v1/auth/apikey - Generate API key
- DELETE /api/v1/auth/apikey/:keyId - Revoke API key

### Inventory
- GET /api/v1/inventory - Get all inventory items
- POST /api/v1/inventory - Create new inventory item
- GET /api/v1/inventory/:id - Get single inventory item
- PUT /api/v1/inventory/:id - Update inventory item
- DELETE /api/v1/inventory/:id - Delete inventory item
- GET /api/v1/inventory/stats - Get inventory statistics
- GET /api/v1/inventory/lowstock - Get low stock items
- GET /api/v1/inventory/expiring - Get expiring items

### Routes
- GET /api/v1/routes - Get all routes
- POST /api/v1/routes - Create new route
- GET /api/v1/routes/:id - Get single route
- PUT /api/v1/routes/:id - Update route
- DELETE /api/v1/routes/:id - Delete route
- POST /api/v1/routes/:id/optimize - Optimize route
- PUT /api/v1/routes/:id/status - Update route status
- GET /api/v1/routes/stats - Get route statistics

## Security Features

- JWT Authentication
- Rate Limiting
- XSS Protection
- CORS Enabled
- Helmet Security Headers
- HTTP Parameter Pollution Prevention

## Testing

Run tests using:
```bash
npm test
```

## Error Handling

The API uses a centralized error handling mechanism. All errors are caught and formatted consistently in the response.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License. 