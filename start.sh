#!/bin/bash

# Editorial Engine Startup Script

set -e

echo "🚀 Starting Editorial Engine Platform..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys before continuing."
    echo "   Required: TAVILY_API_KEY, OPENAI_API_KEY, SEVEN011_API_KEY"
    exit 1
fi

# Check for required environment variables
source .env

if [ -z "$TAVILY_API_KEY" ] || [ "$TAVILY_API_KEY" = "***" ]; then
    echo "❌ TAVILY_API_KEY not set in .env"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "***" ]; then
    echo "❌ OPENAI_API_KEY not set in .env"
    exit 1
fi

if [ -z "$SEVEN011_API_KEY" ] || [ "$SEVEN011_API_KEY" = "***" ]; then
    echo "❌ SEVEN011_API_KEY not set in .env"
    exit 1
fi

echo "✅ Environment variables validated"

# Start services
cd deploy

echo "🐳 Starting Docker services..."
docker compose up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Redis
if docker compose exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not responding"
fi

# Check Orchestrator
if curl -s http://localhost:8080/health | grep -q '"ok"'; then
    echo "✅ Orchestrator is ready"
else
    echo "❌ Orchestrator is not responding"
fi

echo ""
echo "🎉 Editorial Engine is starting up!"
echo ""
echo "📊 Access Points:"
echo "   • Flower Dashboard: http://localhost:5555"
echo "   • Search UI:        http://localhost:3000"
echo "   • Orchestrator API: http://localhost:8080"
echo "   • Prometheus:       http://localhost:9090"
echo "   • Grafana:          http://localhost:3001 (admin/admin)"
echo ""
echo "📝 Logs:"
echo "   docker compose logs -f [service-name]"
echo ""
echo "🛑 To stop:"
echo "   docker compose down"
echo ""

# Show logs for a few seconds
echo "📋 Recent logs:"
docker compose logs --tail=20

echo ""
echo "✨ Platform is ready! Check the access points above."