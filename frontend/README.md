# FlowCast Frontend

This is the frontend application for FlowCast, a comprehensive inventory and route management system.

## Features

- User authentication and authorization
- Inventory management
- Route optimization and tracking
- Analytics and reporting
- Settings and configuration
- API key management

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/flowcast.git
cd flowcast/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory and add the following:
```
REACT_APP_API_URL=http://localhost:5000/api
```

## Development

To start the development server:

```bash
npm start
```

The application will be available at `http://localhost:3000`.

## Building for Production

To create a production build:

```bash
npm run build
```

The build files will be created in the `build` directory.

## Project Structure

```
src/
  ├── components/         # React components
  │   ├── auth/          # Authentication components
  │   ├── inventory/     # Inventory management components
  │   ├── routes/        # Route management components
  │   ├── analytics/     # Analytics and reporting components
  │   ├── settings/      # Settings and configuration components
  │   └── layout/        # Layout components
  ├── redux/             # Redux store and slices
  ├── theme.js           # Material-UI theme configuration
  ├── App.js            # Main application component
  └── index.js          # Application entry point
```

## Dependencies

- React
- Redux Toolkit
- Material-UI
- React Router
- Axios
- Redux Persist
- Recharts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 