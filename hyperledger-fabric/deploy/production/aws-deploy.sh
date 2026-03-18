#!/bin/bash

#
# AWS Production Deployment Script for LGCSE Certificate Verification System
#
# This script deploys the LGCSE Hyperledger Fabric system to AWS EC2 with
# production-grade configuration, security, and monitoring.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="us-east-1"
INSTANCE_TYPE="t3.xlarge"
KEY_NAME="lgcse-keypair"
SECURITY_GROUP_NAME="lgcse-sg"
VPC_ID=""
SUBNET_ID=""
IAM_ROLE_NAME="lgcse-instance-role"
S3_BUCKET_NAME="lgcse-blockchain-backups"
EFS_ID=""
DOMAIN_NAME="lgcse.example.com"
SSL_ARN=""

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Function to print header
print_header() {
    clear
    print_color $BLUE "=================================================="
    print_color $BLUE "🚀 AWS Production Deployment - LGCSE Blockchain"
    print_color $BLUE "=================================================="
    echo ""
    print_color $WHITE "Deploying LGCSE Certificate Verification System to AWS"
    print_color $WHITE "with production-grade security, monitoring, and scalability."
    echo ""
}

# Function to check AWS CLI
check_aws_cli() {
    print_color $CYAN "🔍 Checking AWS CLI configuration..."
    
    if ! command -v aws >/dev/null 2>&1; then
        print_color $RED "❌ AWS CLI is not installed. Please install AWS CLI and configure credentials."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_color $RED "❌ AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    print_color $GREEN "✅ AWS CLI is configured"
}

# Function to create IAM role
create_iam_role() {
    print_color $CYAN "🔐 Creating IAM role for EC2 instances..."
    
    # Create trust policy
    cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
    
    # Create IAM role
    aws iam create-role \
        --role-name "$IAM_ROLE_NAME" \
        --assume-role-policy-document file://trust-policy.json \
        --description "IAM role for LGCSE blockchain instances" || true
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name "$IAM_ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    
    aws iam attach-role-policy \
        --role-name "$IAM_ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/AmazonEFSFullAccess
    
    aws iam attach-role-policy \
        --role-name "$IAM_ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess
    
    aws iam attach-role-policy \
        --role-name "$IAM_ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/AmazonSSMFullAccess
    
    # Create instance profile
    aws iam create-instance-profile --instance-profile-name "$IAM_ROLE_NAME-profile" || true
    aws iam add-role-to-instance-profile \
        --instance-profile-name "$IAM_ROLE_NAME-profile" \
        --role-name "$IAM_ROLE_NAME" || true
    
    print_color $GREEN "✅ IAM role created"
}

# Function to create security group
create_security_group() {
    print_color $CYAN "🔒 Creating security group..."
    
    # Get VPC ID
    VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
    
    # Create security group
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SECURITY_GROUP_NAME" \
        --description "Security group for LGCSE blockchain" \
        --vpc-id "$VPC_ID" \
        --query "GroupId" \
        --output text)
    
    # Add inbound rules
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --description "SSH access"
    
    # Fabric ports
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 7050-7054 \
        --cidr 0.0.0.0/0 \
        --description "Fabric CA and Orderer ports"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 8054-12054 \
        --cidr 0.0.0.0/0 \
        --description "Fabric peer ports"
    
    # Monitoring ports
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 3000 \
        --cidr 0.0.0.0/0 \
        --description "Grafana"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 8080 \
        --cidr 0.0.0.0/0 \
        --description "Blockchain Explorer"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 9090 \
        --cidr 0.0.0.0/0 \
        --description "Prometheus"
    
    # Backend API port
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --description "Backend API"
    
    print_color $GREEN "✅ Security group created: $SG_ID"
}

# Function to create EFS file system
create_efs() {
    print_color $CYAN "📁 Creating EFS file system..."
    
    # Get VPC ID
    VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
    
    # Get subnets
    SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values="$VPC_ID" --query "Subnets[0:2].SubnetId" --output text)
    
    # Create EFS
    EFS_ID=$(aws efs create-file-system \
        --creation-token "lgcse-blockchain-$(date +%s)" \
        --performance-mode generalPurpose \
        --throughput-mode bursting \
        --tags Key=Name,Value=lgcse-blockchain \
        --query "FileSystemId" \
        --output text)
    
    # Create mount targets
    for subnet in $SUBNETS; do
        aws efs create-mount-target \
            --file-system-id "$EFS_ID" \
            --subnet-id "$subnet" \
            --security-group-ids "$SG_ID"
    done
    
    print_color $GREEN "✅ EFS created: $EFS_ID"
}

# Function to create S3 bucket
create_s3_bucket() {
    print_color $CYAN "🪣 Creating S3 bucket for backups..."
    
    # Create S3 bucket
    aws s3api create-bucket \
        --bucket "$S3_BUCKET_NAME" \
        --region "$AWS_REGION" \
        --create-bucket-configuration LocationConstraint="$AWS_REGION" || true
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$S3_BUCKET_NAME" \
        --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "$S3_BUCKET_NAME" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    
    # Create lifecycle policy
    aws s3api put-bucket-lifecycle-configuration \
        --bucket "$S3_BUCKET_NAME" \
        --lifecycle-configuration '{
            "Rules": [
                {
                    "ID": "BackupLifecycle",
                    "Status": "Enabled",
                    "Transitions": [
                        {
                            "Days": 30,
                            "StorageClass": "STANDARD_IA"
                        },
                        {
                            "Days": 90,
                            "StorageClass": "GLACIER"
                        }
                    ]
                }
            ]
        }'
    
    print_color $GREEN "✅ S3 bucket created: $S3_BUCKET_NAME"
}

# Function to create EC2 instances
create_ec2_instances() {
    print_color $CYAN "🖥️ Creating EC2 instances..."
    
    # User data script
    cat > user-data.sh << 'EOF'
#!/bin/bash
# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Python and required packages
yum install -y python3 python3-pip git
pip3 install psutil pyyaml

# Create directories
mkdir -p /opt/lgcse
cd /opt/lgcse

# Clone repository (replace with your repository)
git clone https://github.com/your-repo/lgcse-blockchain.git .

# Set permissions
chmod +x scripts/*.sh

# Create EFS mount point
mkdir -p /mnt/efs
echo "$EFS_ID.efs.$AWS_REGION.amazonaws.com:/ /mnt/efs efs defaults,_netdev,tls 0 0" >> /etc/fstab
mount -a -t efs

# Configure backup to S3
echo "0 2 * * * /opt/lgcse/scripts/disaster-recovery.sh full_backup && aws s3 cp /backup/fabric/ s3://$S3_BUCKET_NAME/ --recursive" >> /etc/crontab

# Start the blockchain system
cd /opt/lgcse
./scripts/deploy-menu.sh --standard

# Configure CloudWatch monitoring
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CLOUDWATCH_EOF'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/docker/*.log",
            "log_group_name": "/aws/ec2/lgcse-blockchain/docker",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
CLOUDWATCH_EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -a start
EOF
    
    # Replace placeholders in user data
    sed -i "s/\$EFS_ID/$EFS_ID/g" user-data.sh
    sed -i "s/\$S3_BUCKET_NAME/$S3_BUCKET_NAME/g" user-data.sh
    
    # Create EC2 instances
    for i in {1..3}; do
        INSTANCE_NAME="lgcse-blockchain-$i"
        
        INSTANCE_ID=$(aws ec2 run-instances \
            --image-id ami-0c55b159cbfafe1f0 \
            --instance-type "$INSTANCE_TYPE" \
            --key-name "$KEY_NAME" \
            --security-group-ids "$SG_ID" \
            --subnet-id "$(echo "$SUBNETS" | head -1)" \
            --iam-instance-profile Name="$IAM_ROLE_NAME-profile" \
            --user-data file://user-data.sh \
            --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME},{Key=Environment,Value=production},{Key=Project,Value=lgcse-blockchain}]" \
            --query "Instances[0].InstanceId" \
            --output text)
        
        print_color $WHITE "Created instance $INSTANCE_NAME: $INSTANCE_ID"
        
        # Wait for instance to be running
        aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
    done
    
    print_color $GREEN "✅ EC2 instances created"
}

# Function to configure Route 53 (if domain provided)
configure_route53() {
    if [ -n "$DOMAIN_NAME" ] && [ -n "$SSL_ARN" ]; then
        print_color $CYAN "🌐 Configuring Route 53..."
        
        # Get public IP of first instance
        PUBLIC_IP=$(aws ec2 describe-instances \
            --filters "Name=tag:Name,Values=lgcse-blockchain-1" \
            --query "Reservations[0].Instances[0].PublicIpAddress" \
            --output text)
        
        # Create hosted zone if needed
        ZONE_ID=$(aws route53 list-hosted-zones \
            --query "HostedZones[?Name==\`$DOMAIN_NAME.\`].Id" \
            --output text)
        
        if [ -z "$ZONE_ID" ]; then
            ZONE_ID=$(aws route53 create-hosted-zone \
                --name "$DOMAIN_NAME" \
                --caller-reference "$(date +%s)" \
                --query "HostedZone.Id" \
                --output text)
        fi
        
        # Create A record
        aws route53 change-resource-record-sets \
            --hosted-zone-id "$ZONE_ID" \
            --change-batch '{
                "Comment": "A record for LGCSE blockchain",
                "Changes": [
                    {
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": "'$DOMAIN_NAME'",
                            "Type": "A",
                            "TTL": 300,
                            "ResourceRecords": [
                                {
                                    "Value": "'$PUBLIC_IP'"
                                }
                            ]
                        }
                    }
                ]
            }'
        
        print_color $GREEN "✅ Route 53 configured for $DOMAIN_NAME"
    fi
}

# Function to setup monitoring
setup_monitoring() {
    print_color $CYAN "📊 Setting up monitoring..."
    
    # Create CloudWatch dashboards
    cat > cloudwatch-dashboard.json << EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/EC2", "CPUUtilization", "InstanceId", "i-1234567890abcdef0"]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "$AWS_REGION",
        "title": "EC2 CPU Utilization",
        "period": 300
      }
    }
  ]
}
EOF
    
    # Create dashboard
    aws cloudwatch put-dashboard \
        --dashboard-name "LGCSE-Blockchain-Monitoring" \
        --dashboard-body file://cloudwatch-dashboard.json
    
    # Create CloudWatch alarms
    aws cloudwatch put-metric-alarm \
        --alarm-name "LGCSE-High-CPU" \
        --alarm-description "High CPU utilization on LGCSE blockchain instances" \
        --metric-name CPUUtilization \
        --namespace AWS/EC2 \
        --statistic Average \
        --period 300 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --alarm-actions-enabled \
        --alarm-actions arn:aws:sns:$AWS_REGION:123456789012:lgcse-alerts \
        --unit Percent
    
    print_color $GREEN "✅ Monitoring setup completed"
}

# Function to generate deployment report
generate_deployment_report() {
    print_color $CYAN "📋 Generating deployment report..."
    
    REPORT_FILE="aws-deployment-report-$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$REPORT_FILE" << EOF
{
  "deployment": {
    "timestamp": "$(date -Iseconds)",
    "environment": "production",
    "platform": "AWS",
    "region": "$AWS_REGION"
  },
  "infrastructure": {
    "instances": {
      "type": "$INSTANCE_TYPE",
      "count": 3,
      "iam_role": "$IAM_ROLE_NAME"
    },
    "networking": {
      "security_group": "$SECURITY_GROUP_NAME",
      "vpc_id": "$VPC_ID"
    },
    "storage": {
      "efs_id": "$EFS_ID",
      "s3_bucket": "$S3_BUCKET_NAME"
    },
    "monitoring": {
      "cloudwatch": true,
      "alarms": true,
      "dashboards": true
    }
  },
  "services": {
    "blockchain": {
      "type": "hyperledger-fabric",
      "organizations": 4,
      "peers": 4,
      "orderers": 3,
      "certificate_authorities": 5
    },
    "monitoring": {
      "prometheus": true,
      "grafana": true,
      "blockchain_explorer": true
    },
    "backup": {
      "s3": true,
      "efs": true,
      "automated": true
    }
  },
  "access": {
    "ssh_key": "$KEY_NAME",
    "domain": "$DOMAIN_NAME",
    "ssl_certificate": "$SSL_ARN"
  },
  "endpoints": {
    "blockchain_explorer": "http://$DOMAIN_NAME:8080",
    "grafana": "http://$DOMAIN_NAME:3000",
    "api": "http://$DOMAIN_NAME:8000"
  },
  "next_steps": [
    "1. SSH into instances to verify deployment",
    "2. Check blockchain status with docker ps",
    "3. Access monitoring dashboards",
    "4. Configure SSL certificate",
    "5. Set up backup verification"
  ]
}
EOF
    
    print_color $GREEN "✅ Deployment report generated: $REPORT_FILE"
}

# Function to show help
show_help() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  (no args)  - Deploy complete AWS production environment"
    echo "  --infra     - Create infrastructure only (IAM, SG, EFS, S3)"
    echo "  --instances  - Create EC2 instances only"
    echo "  --monitoring - Setup monitoring only"
    echo "  --report    - Generate deployment report only"
    echo "  --help      - Show this help message"
    echo ""
    echo "Requirements:"
    echo "  • AWS CLI configured with appropriate permissions"
    echo "  • EC2 key pair created"
    echo "  • Domain name (optional)"
    echo "  • SSL certificate (optional)"
    echo ""
}

# Main execution
main() {
    local action=${1:-"deploy"}
    
    case "$action" in
        "deploy")
            print_header
            check_aws_cli || exit 1
            create_iam_role
            create_security_group
            create_efs
            create_s3_bucket
            create_ec2_instances
            configure_route53
            setup_monitoring
            generate_deployment_report
            ;;
        "--infra")
            print_header
            check_aws_cli || exit 1
            create_iam_role
            create_security_group
            create_efs
            create_s3_bucket
            ;;
        "--instances")
            print_header
            check_aws_cli || exit 1
            create_ec2_instances
            ;;
        "--monitoring")
            print_header
            check_aws_cli || exit 1
            setup_monitoring
            ;;
        "--report")
            generate_deployment_report
            ;;
        "--help")
            show_help
            ;;
        *)
            print_color $RED "❌ Unknown option: $action"
            show_help
            exit 1
            ;;
    esac
    
    print_color $GREEN "🎉 AWS deployment completed successfully!"
}

# Run main function
main "$@"
