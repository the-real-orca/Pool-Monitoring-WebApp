#!/bin/bash
set -e

DEPLOY_DIR="../deploy"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Root files
cp docker-compose.yml "$DEPLOY_DIR/"
cp Caddyfile "$DEPLOY_DIR/"
cp .env_production "$DEPLOY_DIR/.env"

# Backend
mkdir -p "$DEPLOY_DIR/backend"
cp backend/main.py backend/mqtt.py backend/Dockerfile backend/requirements.txt backend/pyproject.toml "$DEPLOY_DIR/backend/"

# Frontend (nur dist + statische configs)
mkdir -p "$DEPLOY_DIR/frontend"
cp -r frontend/dist frontend/public "$DEPLOY_DIR/frontend/"
cp frontend/Dockerfile_production frontend/nginx.conf "$DEPLOY_DIR/frontend/"

# Mosquitto
mkdir -p "$DEPLOY_DIR/mosquitto/config"
cp mosquitto/config/mosquitto.conf "$DEPLOY_DIR/mosquitto/config/"

echo "Fertig: $DEPLOY_DIR/"
echo "Kopieren mit: scp -r $DEPLOY_DIR user@vserver:/opt/pool-monitoring"