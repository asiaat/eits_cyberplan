FROM node:20-alpine

WORKDIR /app/frontend

RUN npm install -g pnpm

COPY frontend/package.json /app/frontend/
COPY frontend/pnpm-lock.yaml /app/frontend/

RUN pnpm install --frozen-lockfile

COPY frontend /app/frontend/

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0"]