#!/bin/bash
set -e

DEPLOY_DIR="../deploy"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Root files
cp docker-compose.yml "$DEPLOY_DIR/"
cp Caddyfile "$DEPLOY_DIR/"
cp .gitignore "$DEPLOY_DIR/.gitignore"
cp .env_production "$DEPLOY_DIR/.env"

# Backend
mkdir -p "$DEPLOY_DIR/backend"
cp backend/main.py backend/mqtt.py backend/ai.py backend/db.py backend/live_state.py backend/aggregator.py backend/Dockerfile backend/requirements.txt backend/pyproject.toml "$DEPLOY_DIR/backend/"
cp backend/.dockerignore "$DEPLOY_DIR/backend/.dockerignore"

# History-data volume (Phase 20) - mount point must exist on first deploy
mkdir -p "$DEPLOY_DIR/data/history"
touch "$DEPLOY_DIR/data/history/.gitkeep"

# mqtt2mail
mkdir -p "$DEPLOY_DIR/mqtt2mail/app"
cp mqtt2mail/Dockerfile mqtt2mail/requirements.txt mqtt2mail/.env.example "$DEPLOY_DIR/mqtt2mail/"
cp mqtt2mail/app/mqtt2mail.py "$DEPLOY_DIR/mqtt2mail/app/"

# Frontend build
echo "Building frontend..."
cd frontend
npm install --silent
npm run build
cd ..
mkdir -p "$DEPLOY_DIR/frontend"
cp -r frontend/dist frontend/public "$DEPLOY_DIR/frontend/"
cp frontend/nginx.conf "$DEPLOY_DIR/frontend/"
cp frontend/Dockerfile_production "$DEPLOY_DIR/frontend/Dockerfile"
cp frontend/.dockerignore "$DEPLOY_DIR/frontend/.dockerignore"

# Mosquitto
mkdir -p "$DEPLOY_DIR/mosquitto/config"
cp mosquitto/config/mosquitto.conf "$DEPLOY_DIR/mosquitto/config/"

echo "finished: $DEPLOY_DIR/"
echo "copy with: scp -r $DEPLOY_DIR user@vserver:/opt/pool-monitoring"
