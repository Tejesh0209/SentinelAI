# Terraform Configuration for SentinelAI on AWS EC2

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "sentinelai" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "sentinelai-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "sentinelai" {
  vpc_id = aws_vpc.sentinelai.id

  tags = {
    Name = "sentinelai-igw"
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.sentinelai.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "sentinelai-public-subnet"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.sentinelai.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.sentinelai.id
  }

  tags = {
    Name = "sentinelai-route-table"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Group
resource "aws_security_group" "sentinelai" {
  name        = "sentinelai-sg"
  description = "Security group for SentinelAI application"
  vpc_id      = aws_vpc.sentinelai.id

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidr_blocks
  }

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Backend API
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sentinelai-sg"
  }
}

# EC2 Instance
resource "aws_instance" "sentinelai" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.sentinelai.id]
  associate_public_ip_address = true
  key_name                    = aws_key_pair.deployer.key_name

  # User data script
  user_data = base64encode(file("${path.module}/setup-ec2.sh"))

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size
    delete_on_termination = true
    encrypted             = true
  }

  monitoring             = true
  iam_instance_profile   = aws_iam_instance_profile.sentinelai.name

  tags = {
    Name = "sentinelai-instance"
  }

  depends_on = [aws_internet_gateway.sentinelai]
}

# Elastic IP
resource "aws_eip" "sentinelai" {
  instance = aws_instance.sentinelai.id
  domain   = "vpc"

  tags = {
    Name = "sentinelai-eip"
  }

  depends_on = [aws_internet_gateway.sentinelai]
}

# Key Pair
resource "aws_key_pair" "deployer" {
  key_name   = "sentinelai-key"
  public_key = file(var.public_key_path)

  tags = {
    Name = "sentinelai-key"
  }
}

# IAM Role for EC2 instance
resource "aws_iam_role" "sentinelai" {
  name = "sentinelai-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

# IAM Policy for CloudWatch and Systems Manager
resource "aws_iam_role_policy" "sentinelai" {
  name   = "sentinelai-policy"
  role   = aws_iam_role.sentinelai.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:UpdateInstanceInformation"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "sentinelai" {
  name = "sentinelai-profile"
  role = aws_iam_role.sentinelai.name
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "sentinelai" {
  name              = "/aws/ec2/sentinelai"
  retention_in_days = 30

  tags = {
    Name = "sentinelai-logs"
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Outputs
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.sentinelai.id
}

output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.sentinelai.public_ip
}

output "public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = aws_instance.sentinelai.public_dns
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.sentinelai.id
}
