### Stage 1 – Build React app
FROM node:20-alpine AS builder

WORKDIR /app

ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

COPY package*.json ./
RUN npm ci --silent

COPY . .
RUN npm run build

### Stage 2 – Serve with nginx
FROM nginx:alpine

# Copy build output
COPY --from=builder /app/build /usr/share/nginx/html

# nginx config: proxy /api → backend, serve React for all other routes
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
