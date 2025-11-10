# Frontend Dockerfile for AcuNexus (Production Build)
# Builds the Vue application and outputs to /app/dist

FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY . .

# Build the application
RUN npm run build

# The dist folder will be mounted as a volume and shared with nginx
# This container exits after building
CMD ["sh", "-c", "echo 'Build completed successfully' && exit 0"]