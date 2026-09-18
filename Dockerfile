FROM node:18-alpine AS production
WORKDIR /app

# Copy server dependency definitions
COPY dashboard-server/package*.json ./dashboard-server/

# Install production dependencies
RUN cd dashboard-server && npm ci --only=production

# Copy server application code
COPY dashboard-server/ ./dashboard-server/

# Run as non-root user for container security
USER node

WORKDIR /app/dashboard-server

EXPOSE 3001
CMD ["node", "server.js"]
