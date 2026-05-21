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
cp backend/main.py backend/mqtt.py backend/Dockerfile backend/requirements.txt backend/pyproject.toml "$DEPLOY_DIR/backend/"
cp backend/.dockerignore "$DEPLOY_DIR/backend/.dockerignore"

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
#mkdir -p "$DEPLOY_DIR/mosquitto/config"
#cp mosquitto/config/mosquitto.conf "$DEPLOY_DIR/mosquitto/config/"

echo "finished: $DEPLOY_DIR/"
echo "copy with: scp -r $DEPLOY_DIR user@vserver:/opt/pool-monitoring"