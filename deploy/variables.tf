# Terraform Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
  
  validation {
    condition     = contains(["t3.small", "t3.medium", "t3.large", "t3.xlarge"], var.instance_type)
    error_message = "Instance type must be t3.small, t3.medium, t3.large, or t3.xlarge."
  }
}

variable "root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 30
  
  validation {
    condition     = var.root_volume_size >= 20
    error_message = "Root volume size must be at least 20 GB."
  }
}

variable "public_key_path" {
  description = "Path to the public SSH key"
  type        = string
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Change to your IP for better security
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}
