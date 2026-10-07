FROM node:20-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm@12.10.1

COPY package.json pnpm-workspace.yaml /app/
COPY apps/web/package.json /app/apps/web/

RUN pnpm install --frozen-lockfile || pnpm install

COPY apps/web/ /app/apps/web/

RUN pnpm --filter web build

FROM nginx:alpine AS runner

COPY --from=builder /app/apps/web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
