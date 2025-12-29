#!/bin/bash

# SentinelAI AWS EC2 Deployment Script
# This script sets up a complete SentinelAI environment on AWS EC2

set -e

echo "🚀 Starting SentinelAI AWS EC2 Setup..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable Docker daemon
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose standalone
echo "📦 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install git
echo "🔗 Installing Git..."
sudo apt-get install -y git

# Install Nginx (for production reverse proxy)
echo "🌐 Installing Nginx..."
sudo apt-get install -y nginx

# Create app directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/sentinelai
sudo chown $USER:$USER /opt/sentinelai

# Clone repository (if not already cloned)
if [ ! -d "/opt/sentinelai/.git" ]; then
    cd /opt/sentinelai
    git clone https://github.com/Tejesh0209/SentinelAI.git .
else
    echo "Repository already cloned, pulling latest changes..."
    cd /opt/sentinelai
    git pull origin main
fi

# Create .env file
echo "🔐 Setting up environment variables..."
cat > /opt/sentinelai/.env << EOF
# OpenAI API Key - Replace with your actual key
OPENAI_API_KEY=your_openai_api_key_here

# Allowed origins for CORS
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:3000,http://127.0.0.1:3001,http://127.0.0.1:3000

# Environment
ENVIRONMENT=production
EOF

echo "⚠️  Please update the .env file with your OpenAI API key:"
echo "   nano /opt/sentinelai/.env"

# Setup Nginx as reverse proxy
echo "🔄 Setting up Nginx reverse proxy..."
sudo cp /opt/sentinelai/deploy/nginx.conf /etc/nginx/sites-available/sentinelai
sudo ln -sf /etc/nginx/sites-available/sentinelai /etc/nginx/sites-enabled/sentinelai
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Create systemd service for Docker Compose
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/sentinelai.service > /dev/null << EOF
[Unit]
Description=SentinelAI Docker Compose Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/sentinelai
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=unless-stopped
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sentinelai

# Create log directory
sudo mkdir -p /var/log/sentinelai
sudo chown $USER:$USER /var/log/sentinelai

# Setup CloudWatch agent for monitoring (optional)
echo "📊 Setting up monitoring..."
cat > /opt/sentinelai/cloudwatch-config.json << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/sentinelai/*.log",
            "log_group_name": "/aws/ec2/sentinelai",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  },
  "metrics": {
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_IDLE",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEM_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": ["/"]
      }
    }
  }
}
EOF

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update .env with your OpenAI API key:"
echo "   sudo nano /opt/sentinelai/.env"
echo ""
echo "2. Start the application:"
echo "   sudo systemctl start sentinelai"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status sentinelai"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -fu sentinelai"
echo ""
echo "5. Access the application:"
echo "   http://your-ec2-instance-ip"
