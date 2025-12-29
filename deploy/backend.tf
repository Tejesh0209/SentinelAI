# Terraform Backend Configuration (for state management)
# Uncomment and configure to use S3 backend

# terraform {
#   backend "s3" {
#     bucket         = "your-terraform-state-bucket"
#     key            = "sentinelai/terraform.tfstate"
#     region         = "us-east-1"
#     encrypt        = true
#     dynamodb_table = "terraform-locks"
#   }
# }
