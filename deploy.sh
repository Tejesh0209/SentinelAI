#!/bin/bash

# SentinelAI Docker Deployment Helper Script

set -e

echo "🚀 SentinelAI Docker Deployment Helper"
echo "======================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install it first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Please update .env with your OpenAI API key:"
        echo "   nano .env"
        exit 1
    else
        echo "❌ .env.example not found"
        exit 1
    fi
fi

# Menu
echo ""
echo "What would you like to do?"
echo "1. Build and start containers"
echo "2. Start existing containers"
echo "3. Stop containers"
echo "4. View logs"
echo "5. Restart containers"
echo "6. Clean up (remove containers and volumes)"
echo "7. Pull latest code and redeploy"
echo ""
read -p "Enter option (1-7): " choice

case $choice in
    1)
        echo "🔨 Building and starting containers..."
        docker-compose up -d --build
        echo "✅ Containers started!"
        echo "   Frontend: http://localhost:3001"
        echo "   Backend: http://localhost:8000"
        ;;
    2)
        echo "▶️  Starting containers..."
        docker-compose up -d
        echo "✅ Containers started!"
        ;;
    3)
        echo "⏹️  Stopping containers..."
        docker-compose down
        echo "✅ Containers stopped!"
        ;;
    4)
        echo "📊 Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    5)
        echo "🔄 Restarting containers..."
        docker-compose restart
        echo "✅ Containers restarted!"
        ;;
    6)
        echo "🗑️  Cleaning up..."
        read -p "Are you sure? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            docker-compose down -v
            echo "✅ Cleanup complete!"
        fi
        ;;
    7)
        echo "📦 Pulling latest code..."
        git pull origin main
        echo "🔨 Rebuilding and redeploying..."
        docker-compose up -d --build
        echo "✅ Redeployment complete!"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🎉 Done!"
