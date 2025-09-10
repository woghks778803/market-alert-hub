# Market Alert Hub

Vue 3 + Vite (SPA) / FastAPI / MySQL / Redis  
로컬: Docker Compose(dev) + Vite dev server

## Quick Start (Local)

```bash
# 1) backend containers
cd ops/dev
docker compose --env-file .env -f docker-compose.base.yml up -d

# 2) frontend
cd ../../frontend
npm install
npm run dev
