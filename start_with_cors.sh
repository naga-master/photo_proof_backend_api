#!/bin/bash

# Start Photo Proof API with correct CORS configuration
cd "$(dirname "$0")"

# Set environment variables
export CORS_ORIGINS="http://*.*.*.*:3001,http://*.*.*.*:8000,http://*.*.*.*:8081,http://localhost:3001,http://localhost:8000,http://localhost:8081,http://localhost:5173,http://localhost:3000"
export DATABASE_URL="postgresql://photo_proof_user:PhotoProof2024!@localhost/photo_proof_production"
export SECRET_KEY="HX3-m-WYoZibjEgD_lHO_INTPlX_4alt9p9g33Z10AI"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="1440"
export USE_S3="false"
export UPLOAD_DIR="$(pwd)/uploads"
export MAX_UPLOAD_SIZE="10485760"
export ENVIRONMENT="development"

echo "🚀 Starting Photo Proof API with CORS for port 8081..."
echo "CORS_ORIGINS: $CORS_ORIGINS"
echo ""

.venv/bin/python main.py
