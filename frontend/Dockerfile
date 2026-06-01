FROM node:18-alpine

WORKDIR /app

# Install dependencies first
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy the rest of the application
COPY frontend/ .

# Build the Next.js application
RUN npm run build

EXPOSE 3000

ENV PORT=3000

CMD ["npm", "run", "start"]
