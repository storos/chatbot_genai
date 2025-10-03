#!/bin/bash

# EKS Deployment Script for Chatbot Application
set -e

echo "🚀 Starting EKS deployment for Chatbot application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if cluster is ready
echo "📋 Checking EKS cluster status..."
CLUSTER_STATUS=$(aws eks describe-cluster --region eu-central-1 --name chat-cluster --query 'cluster.status' --output text)

if [ "$CLUSTER_STATUS" != "ACTIVE" ]; then
    echo -e "${RED}❌ EKS cluster is not ready yet. Status: $CLUSTER_STATUS${NC}"
    echo "Please wait for the cluster to be ACTIVE before running this script."
    exit 1
fi

echo -e "${GREEN}✅ EKS cluster is ready!${NC}"

# Update kubeconfig
echo "🔧 Updating kubectl configuration..."
aws eks update-kubeconfig --region eu-central-1 --name chat-cluster

# Check kubectl connection
echo "🔍 Testing kubectl connection..."
kubectl get nodes

# Build and push Docker images to ECR (you'll need to set up ECR repositories first)
echo "🐳 Building Docker images..."

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="eu-central-1"

echo "📦 Building and tagging images..."

# Build order-api
docker build -t chatbot-order-api ./order-api
docker tag chatbot-order-api:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/chatbot-order-api:latest

# Build chat-api  
docker build -t chatbot-chat-api ./chat-api
docker tag chatbot-chat-api:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/chatbot-chat-api:latest

# Build chat-ui
docker build -t chatbot-chat-ui ./chat-ui
docker tag chatbot-chat-ui:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/chatbot-chat-ui:latest

echo -e "${YELLOW}⚠️  Note: You need to create ECR repositories and push images before deploying.${NC}"
echo "Run the following commands to create ECR repos and push images:"
echo ""
echo "aws ecr create-repository --repository-name chatbot-order-api --region $REGION"
echo "aws ecr create-repository --repository-name chatbot-chat-api --region $REGION"  
echo "aws ecr create-repository --repository-name chatbot-chat-ui --region $REGION"
echo ""
echo "aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
echo ""
echo "docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/chatbot-order-api:latest"
echo "docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/chatbot-chat-api:latest"
echo "docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/chatbot-chat-ui:latest"

echo ""
echo -e "${GREEN}📝 Kubernetes manifests are ready in k8s/ directory${NC}"
echo "After pushing images to ECR, run:"
echo "kubectl apply -f k8s/"

echo ""
echo -e "${GREEN}🎉 Setup completed! Next steps:${NC}"
echo "1. Create ECR repositories"  
echo "2. Push Docker images to ECR"
echo "3. Update image URLs in k8s/*.yaml files"
echo "4. Add your OpenAI API key to k8s/secrets-config.yaml"
echo "5. Deploy with: kubectl apply -f k8s/"