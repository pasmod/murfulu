# The `web` container. Built in Node, served by nginx — so the running image
# carries no build tools and no source. Tags are exact; never `latest`.

FROM node:22.16.0-alpine3.21 AS build

WORKDIR /app

# Dependency metadata first, so a source change does not reinstall the world.
COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts index.html ./
COPY src ./src
RUN npm run build

FROM nginx:1.27.4-alpine3.21

# The SPA fallback and the API proxy. The app always calls /api, whether it is
# talking to the dev server or to this one.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
