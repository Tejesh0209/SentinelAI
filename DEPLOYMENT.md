# SentinelAI Deployment Guide

## Overview
This guide covers deploying SentinelAI using Docker and AWS EC2.

---

## Table of Contents
1. [Local Docker Deployment](#local-docker-deployment)
2. [AWS EC2 Deployment](#aws-ec2-deployment)
3. [AWS Deployment with Terraform](#aws-deployment-with-terraform)
4. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Local Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   nano .env
   ```

2. **Build and start containers:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000
   - Health check: http://localhost:8000/health

4. **View logs:**
   ```bash
   docker-compose logs -f
   ```

5. **Stop containers:**
   ```bash
   docker-compose down
   ```

### Useful Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Execute command in container
docker-compose exec backend python -m pytest

# Remove containers and volumes
docker-compose down -v

# Rebuild without cache
docker-compose build --no-cache
```

---

## AWS EC2 Deployment

### Prerequisites
- AWS account with EC2 permissions
- SSH key pair created in AWS
- OpenAI API key

### Manual Deployment Steps

1. **Launch EC2 Instance:**
   - AMI: Ubuntu 22.04 LTS (ami-0c02fb55731490381)
   - Instance type: t3.medium or larger
   - Storage: 30 GB gp3
   - Security group: Allow SSH (22), HTTP (80), HTTPS (443), API (8000)

2. **Connect to instance:**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Run setup script:**
   ```bash
   # Clone repository
   git clone https://github.com/Tejesh0209/SentinelAI.git
   cd SentinelAI
   
   # Make script executable
   chmod +x deploy/setup-ec2.sh
   
   # Run setup
   sudo bash deploy/setup-ec2.sh
   ```

4. **Configure environment:**
   ```bash
   sudo nano /opt/sentinelai/.env
   # Add your OpenAI API key and other variables
   ```

5. **Start the application:**
   ```bash
   sudo systemctl start sentinelai
   sudo systemctl status sentinelai
   ```

6. **Access the application:**
   ```
   http://your-instance-ip
   ```

### Useful EC2 Commands

```bash
# Check service status
sudo systemctl status sentinelai

# View logs
sudo journalctl -fu sentinelai

# Restart service
sudo systemctl restart sentinelai

# View Docker containers
sudo docker-compose -f /opt/sentinelai/docker-compose.yml ps

# View container logs
sudo docker logs sentinelai-backend -f
```

---

## AWS Deployment with Terraform

### Prerequisites
- Terraform installed (>= 1.0)
- AWS CLI configured with credentials
- SSH key pair generated locally

### Deployment Steps

1. **Generate SSH key pair (if not already done):**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/sentinelai-key
   chmod 400 ~/.ssh/sentinelai-key
   ```

2. **Initialize Terraform:**
   ```bash
   cd deploy
   terraform init
   ```

3. **Create terraform.tfvars:**
   ```bash
   cat > terraform.tfvars << EOF
   aws_region      = "us-east-1"
   instance_type   = "t3.medium"
   public_key_path = "~/.ssh/sentinelai-key.pub"
   ssh_cidr_blocks = ["YOUR_IP/32"]  # Replace with your IP for security
   EOF
   ```

4. **Plan deployment:**
   ```bash
   terraform plan
   ```

5. **Apply configuration:**
   ```bash
   terraform apply
   ```

6. **Get outputs:**
   ```bash
   terraform output
   ```

7. **SSH into instance:**
   ```bash
   ssh -i ~/.ssh/sentinelai-key ubuntu@<public_ip>
   ```

8. **Configure and start application:**
   ```bash
   # Update environment variables
   sudo nano /opt/sentinelai/.env
   
   # Start application
   sudo systemctl start sentinelai
   ```

### Terraform Commands

```bash
# Plan changes
terraform plan

# Apply changes
terraform apply

# Destroy resources
terraform destroy

# Show current state
terraform show

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive
```

### Terraform Outputs

After applying, get your deployment details:

```bash
terraform output public_ip      # Public IP address
terraform output public_dns     # Public DNS name
terraform output instance_id    # EC2 Instance ID
terraform output security_group_id  # Security Group ID
```

---

## Monitoring and Maintenance

### Health Checks

1. **Backend health:**
   ```bash
   curl http://your-instance-ip:8000/health
   ```

2. **Frontend health:**
   ```bash
   curl http://your-instance-ip/health
   ```

3. **Docker health:**
   ```bash
   docker inspect sentinelai-backend | grep -A 5 "Health"
   ```

### Log Files

- **Systemd service logs:**
  ```bash
  sudo journalctl -u sentinelai -f
  ```

- **Docker logs:**
  ```bash
  sudo docker logs sentinelai-backend -f
  sudo docker logs sentinelai-frontend -f
  ```

- **Nginx logs:**
  ```bash
  sudo tail -f /var/log/nginx/access.log
  sudo tail -f /var/log/nginx/error.log
  ```

### Performance Monitoring

1. **AWS CloudWatch Dashboard:**
   - View in AWS Console
   - CPU, Memory, Network metrics
   - Log aggregation

2. **System metrics:**
   ```bash
   # CPU and Memory
   top
   
   # Disk usage
   df -h
   
   # Docker stats
   docker stats
   ```

### Backups

1. **Database/Data backups:**
   ```bash
   # Backup data directory
   sudo tar -czf sentinelai-data-$(date +%Y%m%d).tar.gz /opt/sentinelai/data/
   ```

2. **S3 backup:**
   ```bash
   aws s3 cp sentinelai-data-*.tar.gz s3://your-backup-bucket/
   ```

### Updates

1. **Update application:**
   ```bash
   cd /opt/sentinelai
   git pull origin main
   sudo systemctl restart sentinelai
   ```

2. **Update Docker images:**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

### Troubleshooting

**Application won't start:**
```bash
# Check systemd service
sudo systemctl status sentinelai

# View service logs
sudo journalctl -u sentinelai -n 50

# Check Docker
sudo docker ps -a
sudo docker logs sentinelai-backend
```

**Port already in use:**
```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :3001

# Kill process
kill -9 <PID>
```

**Out of disk space:**
```bash
# Check disk usage
df -h

# Clean Docker images/containers
docker system prune -a

# Clean logs
sudo journalctl --vacuum=size=100M
```

---

## Security Best Practices

1. **Update SSH security group** - Replace `0.0.0.0/0` with your IP
2. **Enable HTTPS** - Use AWS Certificate Manager with ALB
3. **Rotate API keys** - Regularly update OpenAI API key
4. **Enable CloudWatch monitoring** - Set up alarms for anomalies
5. **Use IAM roles** - Don't use root credentials
6. **Encrypt data** - Enable EBS encryption in Terraform

---

## Cost Optimization

- **Use t3 instances** - Auto-scaling, cost-effective
- **Enable auto-shutdown** - Stop instances during off-hours
- **Right-size resources** - Monitor and adjust instance type
- **Use spot instances** - For non-critical environments
- **Set up billing alerts** - AWS CloudWatch budgets

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/Tejesh0209/SentinelAI/issues
- Documentation: Check README.md in project root
