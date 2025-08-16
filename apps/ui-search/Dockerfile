FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY apps/ui-search/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY apps/ui-search/ ./

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]