#!/bin/bash
# Build script for Radio Russell Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Building Radio Russell Docker Images${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Function to build image
build_image() {
    local target=$1
    local tag=$2
    
    echo -e "${YELLOW}📦 Building ${target} image...${NC}"
    docker build --target ${target} -t radio-russell:${tag} .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Successfully built radio-russell:${tag}${NC}"
    else
        echo -e "${RED}❌ Failed to build radio-russell:${tag}${NC}"
        exit 1
    fi
}

# Build development image
if [[ "$1" == "dev" || "$1" == "all" ]]; then
    build_image "development" "dev"
fi

# Build production image
if [[ "$1" == "prod" || "$1" == "all" ]]; then
    build_image "production" "prod"
fi

# Build all if no argument provided
if [[ -z "$1" ]]; then
    build_image "development" "dev"
    build_image "production" "prod"
fi

echo -e "${GREEN}🎉 Build completed!${NC}"

# Show built images
echo -e "${YELLOW}📋 Built images:${NC}"
docker images | grep radio-russell
