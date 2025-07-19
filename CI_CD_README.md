# 🚀 Radio Russell CI/CD Pipeline

This document describes the comprehensive CI/CD pipeline setup for Radio Russell using GitHub Actions.

## 📋 Pipeline Overview

The CI/CD pipeline consists of six main jobs that run automatically on pushes and pull requests:

### 1. 🧪 Tests & Code Quality
- **Runs on**: All pushes and pull requests
- **Services**: PostgreSQL test database
- **Tasks**:
  - Code formatting check (Black, isort)
  - Linting with flake8
  - Unit and integration tests with pytest
  - Code coverage reporting to Codecov

### 2. 🔒 Security Scanning
- **Runs on**: After tests pass
- **Tasks**:
  - Vulnerability scanning with Trivy
  - Python security audit with Bandit
  - Results uploaded to GitHub Security tab

### 3. 🐳 Docker Build & Push
- **Runs on**: Pushes to main/develop (not PRs)
- **Tasks**:
  - Multi-platform Docker image build (amd64, arm64)
  - Push to GitHub Container Registry (ghcr.io)
  - Image tagging with branch, SHA, and latest

### 4. 🔄 Integration Tests
- **Runs on**: After Docker build completes
- **Tasks**:
  - Full stack testing with Docker Compose
  - API endpoint testing
  - Database integration verification

### 5. 🚀 Production Deployment
- **Runs on**: Pushes to main branch only
- **Environment**: Production (requires manual approval)
- **Tasks**:
  - Deploy latest Docker image
  - Run health checks
  - Send deployment notifications

### 6. 🧹 Cleanup
- **Runs on**: After successful deployment
- **Tasks**:
  - Remove old Docker images (keep 5 latest)
  - Clean up untagged versions

## 🔧 Configuration

### Environment Variables
The pipeline uses these environment variables:
- `REGISTRY`: ghcr.io (GitHub Container Registry)
- `IMAGE_NAME`: ${{ github.repository }}

### Secrets Required
- `GITHUB_TOKEN`: Automatically provided by GitHub
- Additional secrets for production deployment (if applicable)

### Branch Strategy
- **main**: Full pipeline including deployment
- **develop**: Build and test only (no deployment)
- **feature branches**: Tests and security scanning only via PRs

## 📊 Code Quality Standards

### Formatting
- **Black**: Python code formatting (88 char line length)
- **isort**: Import sorting and organization

### Linting
- **flake8**: Python linting with custom configuration
- Max line length: 88 characters
- Complexity limit: 10

### Testing
- **pytest**: Test framework with fixtures and parameterization
- **Coverage**: Minimum coverage reporting
- **PostgreSQL**: Test database for integration tests

### Security
- **Trivy**: Vulnerability scanning for dependencies and Docker images
- **Bandit**: Python security linter
- **SARIF**: Security results uploaded to GitHub Security tab

## 🐳 Docker Registry

Docker images are automatically built and pushed to:
```
ghcr.io/ruoguluo/radio_calico:latest
ghcr.io/ruoguluo/radio_calico:main-<sha>
```

### Image Tags
- `latest`: Latest build from main branch
- `main-<sha>`: Specific commit from main branch
- `develop-<sha>`: Specific commit from develop branch
- `<branch-name>`: Latest build from feature branch

## 🚀 Deployment Process

### Automatic Deployment
1. Code pushed to main branch
2. All tests and security scans pass
3. Docker image built and pushed
4. Integration tests pass
5. Deployment job runs (requires environment approval)
6. Health checks verify successful deployment
7. Cleanup removes old images

### Manual Deployment
You can trigger deployment manually using:
```bash
gh workflow run ci-cd.yml
```

## 📈 Monitoring

### GitHub Actions
- View pipeline status in the Actions tab
- Download artifacts (test reports, security scans)
- Check job logs for debugging

### Security
- Security scan results in Security tab
- Dependabot alerts for dependency vulnerabilities
- CodeQL analysis (if enabled)

### Container Registry
- View Docker images in Packages tab
- Check image sizes and scan results
- Manage image retention policies

## 🛠️ Local Development

### Running Tests Locally
```bash
# Install test dependencies
pip install pytest pytest-cov flake8 black isort

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Format code
black .
isort .

# Lint code
flake8 .
```

### Building Docker Images
```bash
# Build production image
docker build --target production -t radio-russell:prod .

# Test with docker-compose
docker-compose --profile prod up --build
```

## 🔧 Troubleshooting

### Common Issues

1. **Test Failures**
   - Check test logs in GitHub Actions
   - Ensure database migrations are applied
   - Verify environment variables

2. **Docker Build Failures**
   - Check Dockerfile syntax
   - Verify all files are committed
   - Check build context size

3. **Deployment Issues**
   - Verify production environment setup
   - Check secrets configuration
   - Review deployment logs

### Getting Help
- Check the Actions tab for detailed logs
- Review this documentation
- Contact the development team

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [pytest Documentation](https://pytest.org/)
- [Flask Testing Guide](https://flask.palletsprojects.com/en/latest/testing/)
