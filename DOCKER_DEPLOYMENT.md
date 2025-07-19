# Radio Russell - Docker Deployment Guide 🐳

This guide covers deploying Radio Russell using Docker containers for both development and production environments.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB available RAM
- 1GB available disk space

## Quick Start

### Development Deployment

```bash
# Build and start development environment
./scripts/deploy.sh dev up

# Access the application
open http://localhost:3000
```

### Production Deployment

```bash
# Build and start production environment with nginx
./scripts/deploy.sh prod up

# Access the application
open http://localhost
```

## Architecture Overview

### Development Stack
- **App Container**: Flask development server with hot reload
- **Port**: 3000
- **Database**: SQLite in persistent volume
- **Debug**: Enabled

### Production Stack
- **App Container**: Gunicorn WSGI server with 4 workers
- **Reverse Proxy**: Nginx with security headers and rate limiting
- **Ports**: 80 (nginx), 8000 (direct app access)
- **Database**: SQLite in persistent volume
- **Security**: Non-root user, input validation, logging

## Container Details

### Multi-stage Dockerfile

The Dockerfile uses multi-stage builds for optimal image sizes:

1. **Base Stage**: Common Python setup and dependencies
2. **Development Stage**: Adds debug tools, runs as root for development ease
3. **Production Stage**: Minimal setup, non-root user, Gunicorn server

### Image Sizes
- Base layer: ~150MB
- Development: ~200MB  
- Production: ~180MB

## Deployment Commands

### Using Deployment Scripts

```bash
# Build images
./scripts/build.sh [dev|prod|all]

# Deploy development
./scripts/deploy.sh dev up

# Deploy production
./scripts/deploy.sh prod up

# View logs
./scripts/deploy.sh [dev|prod] logs

# Stop services
./scripts/deploy.sh [dev|prod] down

# Restart services
./scripts/deploy.sh [dev|prod] restart
```

### Using Docker Compose Directly

```bash
# Development
docker-compose --profile dev up -d

# Production
docker-compose --profile prod --profile nginx up -d

# Stop all services
docker-compose --profile dev --profile prod --profile nginx down
```

### Using Docker Commands

```bash
# Build development image
docker build --target development -t radio-russell:dev .

# Build production image
docker build --target production -t radio-russell:prod .

# Run development container
docker run -d -p 3000:3000 -v $(pwd):/app --name radio-russell-dev radio-russell:dev

# Run production container
docker run -d -p 8000:8000 --name radio-russell-prod radio-russell:prod
```

## Environment Variables

### Development
- `FLASK_ENV=development`
- `FLASK_DEBUG=1`
- `DATABASE_PATH=/app/data/database.db`

### Production
- `FLASK_ENV=production`
- `FLASK_DEBUG=0`
- `DATABASE_PATH=/app/data/database.db`
- `ALLOWED_ORIGINS=your-domain.com,localhost` (optional)

## Data Persistence

### Volumes
- `radio-russell-data-dev`: Development database storage
- `radio-russell-data-prod`: Production database storage

### Backup Database
```bash
# Development
docker cp radio-russell-dev:/app/data/database.db ./backup-dev.db

# Production
docker cp radio-russell-prod:/app/data/database.db ./backup-prod.db
```

### Restore Database
```bash
# Development
docker cp ./backup-dev.db radio-russell-dev:/app/data/database.db

# Production
docker cp ./backup-prod.db radio-russell-prod:/app/data/database.db
```

## Monitoring and Health Checks

### Health Check Endpoints
- Development: `http://localhost:3000/health`
- Production: `http://localhost:8000/health`
- Nginx Proxy: `http://localhost/health`

### View Container Status
```bash
# Check container health
docker ps

# View container stats
docker stats radio-russell-prod

# Check logs
docker logs radio-russell-prod -f
```

### Production Logs
```bash
# Application logs
docker exec radio-russell-prod tail -f /app/data/app.log

# Nginx logs
docker logs radio-russell-nginx -f
```

## Security Features

### Production Security
- Non-root user (`radiouser`)
- Input validation and sanitization
- Rate limiting via nginx
- Security headers (CSP, XSS protection, etc.)
- Restricted CORS origins
- Error logging without sensitive data exposure

### Network Security
- Internal Docker network isolation
- Only necessary ports exposed
- Nginx reverse proxy with security headers

## Performance Tuning

### Production Configuration
- **Gunicorn Workers**: 4 (adjust based on CPU cores)
- **Worker Timeout**: 120 seconds
- **Database Connection Pooling**: SQLite with WAL mode
- **Static File Caching**: 1 day via nginx

### Scaling Options
```bash
# Scale production app instances
docker-compose --profile prod up -d --scale radio-russell-prod=3

# Update nginx upstream accordingly in nginx.conf
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :3000
   # Kill process or change port in docker-compose.yml
   ```

2. **Permission Denied (Database)**
   ```bash
   # Fix volume permissions
   docker exec -u root radio-russell-prod chown -R radiouser:radiouser /app/data
   ```

3. **Memory Issues**
   ```bash
   # Check container memory usage
   docker stats radio-russell-prod
   
   # Increase Docker memory limit if needed
   ```

4. **Build Fails**
   ```bash
   # Clean Docker cache
   docker system prune -f
   docker builder prune -f
   
   # Rebuild without cache
   docker build --no-cache --target production -t radio-russell:prod .
   ```

### Debug Commands

```bash
# Enter container shell
docker exec -it radio-russell-prod /bin/bash

# Check container environment
docker exec radio-russell-prod env

# Test database connection
docker exec radio-russell-prod python -c "import sqlite3; print(sqlite3.connect('/app/data/database.db').execute('SELECT 1').fetchone())"

# Check file permissions
docker exec radio-russell-prod ls -la /app/data/
```

## Production Deployment Checklist

- [ ] Configure domain name in nginx.conf
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Configure backup strategy
- [ ] Set up monitoring/alerting
- [ ] Test health checks
- [ ] Configure CORS origins
- [ ] Review security headers
- [ ] Test database backup/restore

## Advanced Configuration

### Custom Environment File
Create `.env` file:
```env
FLASK_ENV=production
DATABASE_PATH=/app/data/database.db
ALLOWED_ORIGINS=yourdomain.com,localhost
```

Load with docker-compose:
```yaml
env_file: .env
```

### SSL Setup
1. Obtain SSL certificates (Let's Encrypt recommended)
2. Place certificates in `./ssl/` directory
3. Uncomment HTTPS server block in nginx.conf
4. Update docker-compose.yml to mount SSL directory

### Database Migration
For future schema changes:
```bash
# Create migration script
docker exec radio-russell-prod python migrate.py

# Or manual SQL execution
docker exec -it radio-russell-prod sqlite3 /app/data/database.db
```

## Support

For deployment issues:
1. Check logs first: `./scripts/deploy.sh [env] logs`
2. Verify container health: `docker ps`
3. Test endpoints: `curl http://localhost:3000/health`
4. Review this guide for common solutions

---

**Radio Russell Docker Deployment** - *Containerized for scalability* 🐳
