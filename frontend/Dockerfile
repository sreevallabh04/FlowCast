# Use Node.js 16 slim image
FROM node:16-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV NODE_ENV=production \
    REACT_APP_API_URL=http://localhost:5000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Install serve to run the application
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Set healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Run the application
CMD ["serve", "-s", "build", "-l", "3000"] 