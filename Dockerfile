FROM node:18-alpine
WORKDIR /app

# Copy server package.json
COPY dashboard-server/package*.json ./dashboard-server/

# Install dependencies
RUN cd dashboard-server && npm ci --only=production

# Copy server code
COPY dashboard-server/ ./dashboard-server/

# Set working directory to the server
WORKDIR /app/dashboard-server

EXPOSE ${PORT:-3001}
CMD ["node", "server.js"]
