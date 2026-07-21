FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Baked in at build time (Vite). Override on Railway with service variable.
ARG VITE_API_URL=https://thriving-vision-production-5dbb.up.railway.app
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve@14.2.4

COPY --from=build /app/dist ./dist

# Railway injects PORT; serve SPA with history fallback (-s).
CMD ["sh", "-c", "serve -s dist -l tcp://0.0.0.0:${PORT:-3000}"]
