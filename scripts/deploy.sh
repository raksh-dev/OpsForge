#!/bin/bash

# AI Operations Agent Deployment Script

set -e

echo "🚀 Starting AI Operations Agent Deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your configuration"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check required environment variables
required_vars=("OPENAI_API_KEY" "PINECONE_API_KEY" "DB_PASSWORD" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env file!"
        exit 1
    fi
done

echo "✅ Environment variables loaded"

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo "🗄️ Initializing database..."
docker-compose exec backend python -m backend.database.init_db

echo "✅ Deployment complete!"
echo ""
echo "📍 Access points:"
echo "   - Frontend: http://localhost"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Default admin credentials:"
echo "   - Username: admin"
echo "   - Password: admin123"
echo ""
echo "⚠️  Remember to change the admin password after first login!"