# Stage 1: Build frontend
FROM node:20-alpine AS builder
ARG VITE_API_URL=/api/v2
ENV VITE_API_URL=$VITE_API_URL
RUN npm install -g pnpm
WORKDIR /build
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# Stage 2: Serve with nginx
FROM nginx:stable-alpine
RUN apk add --no-cache openssl
COPY --from=builder /build/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY infra/docker/nginx-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
EXPOSE 80 443
ENTRYPOINT ["/docker-entrypoint.sh"]
