#!/bin/bash
# Deployment script for Radio Russell

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
ACTION="up"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        dev|development)
            ENVIRONMENT="dev"
            shift
            ;;
        prod|production)
            ENVIRONMENT="prod"
            shift
            ;;
        up|start)
            ACTION="up"
            shift
            ;;
        down|stop)
            ACTION="down"
            shift
            ;;
        restart)
            ACTION="restart"
            shift
            ;;
        logs)
            ACTION="logs"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [dev|prod] [up|down|restart|logs]"
            echo ""
            echo "Environments:"
            echo "  dev   - Development environment (default)"
            echo "  prod  - Production environment with nginx"
            echo ""
            echo "Actions:"
            echo "  up      - Start services (default)"
            echo "  down    - Stop services"
            echo "  restart - Restart services"
            echo "  logs    - Show logs"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown parameter: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🎵 Radio Russell Deployment${NC}"
echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}"
echo -e "${YELLOW}Action: ${ACTION}${NC}"
echo ""

# Function to run docker-compose with appropriate profile
run_compose() {
    local cmd=$1
    shift
    
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        docker-compose --profile dev $cmd "$@"
    else
        docker-compose --profile prod --profile nginx $cmd "$@"
    fi
}

# Execute action
case $ACTION in
    up)
        echo -e "${GREEN}🚀 Starting Radio Russell (${ENVIRONMENT})...${NC}"
        run_compose up -d
        
        if [[ "$ENVIRONMENT" == "dev" ]]; then
            echo -e "${GREEN}✅ Development server started!${NC}"
            echo -e "${YELLOW}🌐 Access at: http://localhost:3000${NC}"
        else
            echo -e "${GREEN}✅ Production server started!${NC}"
            echo -e "${YELLOW}🌐 Access at: http://localhost (nginx)${NC}"
            echo -e "${YELLOW}🌐 Direct access at: http://localhost:8000${NC}"
        fi
        ;;
        
    down)
        echo -e "${YELLOW}⏹️ Stopping Radio Russell (${ENVIRONMENT})...${NC}"
        run_compose down
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}🔄 Restarting Radio Russell (${ENVIRONMENT})...${NC}"
        run_compose restart
        echo -e "${GREEN}✅ Services restarted${NC}"
        ;;
        
    logs)
        echo -e "${BLUE}📋 Showing logs for Radio Russell (${ENVIRONMENT})...${NC}"
        run_compose logs -f
        ;;
        
    *)
        echo -e "${RED}❌ Unknown action: ${ACTION}${NC}"
        exit 1
        ;;
esac
