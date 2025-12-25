# Kong API Gateway Setup for Ocean Backend

**Issue #18**: Configure Kong Gateway for rate limiting and API routing

This guide covers setting up Kong API Gateway as a reverse proxy for the Ocean backend with comprehensive rate limiting, API key authentication, and CORS support.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration Deployment](#configuration-deployment)
5. [Testing Setup](#testing-setup)
6. [Rate Limits Summary](#rate-limits-summary)
7. [API Key Management](#api-key-management)
8. [Monitoring & Logs](#monitoring--logs)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

---

## Overview

### What This Configuration Provides

- **Rate Limiting**: Protects backend from abuse with tiered limits per endpoint category
- **API Key Authentication**: Secures all endpoints except health checks
- **CORS Support**: Full cross-origin support for web applications
- **Request Tracking**: Automatic correlation IDs for distributed tracing
- **Response Headers**: Rate limit metadata in all responses
- **Multi-tenant Support**: Configured for organization-scoped access

### Architecture

```
Client Request
    ↓
Kong Gateway (port 8000)
    ↓
Rate Limiting + API Key Auth + CORS
    ↓
Ocean Backend (port 8000 internal)
    ↓
Response with Rate Limit Headers
```

---

## Prerequisites

### Required Software

- **Kong Gateway**: 3.0+ (OSS or Enterprise)
- **PostgreSQL**: 12+ (for Kong database)
- **Ocean Backend**: Running on `http://localhost:8000`
- **curl** or **httpie**: For testing

### System Requirements

- **RAM**: 2GB minimum, 4GB recommended
- **CPU**: 2 cores minimum
- **Disk**: 10GB available

---

## Installation

### Option 1: Docker (Recommended for Development)

#### 1. Create Docker Network

```bash
docker network create ocean-network
```

#### 2. Start PostgreSQL for Kong

```bash
docker run -d \
  --name kong-database \
  --network=ocean-network \
  -e "POSTGRES_USER=kong" \
  -e "POSTGRES_DB=kong" \
  -e "POSTGRES_PASSWORD=kongpass" \
  -p 5433:5432 \
  postgres:14
```

#### 3. Initialize Kong Database

```bash
docker run --rm \
  --network=ocean-network \
  -e "KONG_DATABASE=postgres" \
  -e "KONG_PG_HOST=kong-database" \
  -e "KONG_PG_USER=kong" \
  -e "KONG_PG_PASSWORD=kongpass" \
  kong:3.4 kong migrations bootstrap
```

#### 4. Start Kong Gateway

```bash
docker run -d \
  --name kong-gateway \
  --network=ocean-network \
  -e "KONG_DATABASE=postgres" \
  -e "KONG_PG_HOST=kong-database" \
  -e "KONG_PG_USER=kong" \
  -e "KONG_PG_PASSWORD=kongpass" \
  -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
  -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
  -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_LISTEN=0.0.0.0:8001" \
  -e "KONG_ADMIN_GUI_URL=http://localhost:8002" \
  -p 8000:8000 \
  -p 8001:8001 \
  -p 8002:8002 \
  -p 8443:8443 \
  -p 8444:8444 \
  kong:3.4
```

#### 5. Verify Kong is Running

```bash
curl http://localhost:8001/status
```

**Expected Response:**
```json
{
  "database": {
    "reachable": true
  },
  "server": {
    "total_requests": 1,
    "connections_active": 1,
    "connections_accepted": 1
  }
}
```

### Option 2: Native Installation (macOS)

#### 1. Install Kong via Homebrew

```bash
brew tap kong/kong
brew install kong
```

#### 2. Configure PostgreSQL

```bash
# Install PostgreSQL if not already installed
brew install postgresql@14
brew services start postgresql@14

# Create Kong database
createdb kong
```

#### 3. Set Environment Variables

Create `/etc/kong/kong.conf`:

```conf
database = postgres
pg_host = 127.0.0.1
pg_port = 5432
pg_user = kong
pg_database = kong

admin_listen = 0.0.0.0:8001
proxy_listen = 0.0.0.0:8000
```

#### 4. Initialize and Start Kong

```bash
# Initialize database
kong migrations bootstrap -c /etc/kong/kong.conf

# Start Kong
kong start -c /etc/kong/kong.conf
```

### Option 3: Native Installation (Linux)

#### Ubuntu/Debian

```bash
# Add Kong repository
curl -fsSL https://download.konghq.com/gateway-3.x-ubuntu-$(lsb_release -cs)/kong.key | sudo gpg --dearmor -o /usr/share/keyrings/kong-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/kong-archive-keyring.gpg] https://download.konghq.com/gateway-3.x-ubuntu-$(lsb_release -cs)/ default all" | sudo tee /etc/apt/sources.list.d/kong.list

# Install Kong
sudo apt update
sudo apt install -y kong

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Create Kong database
sudo -u postgres createdb kong
sudo -u postgres createuser kong

# Initialize and start
sudo kong migrations bootstrap
sudo kong start
```

---

## Configuration Deployment

### 1. Ensure Ocean Backend is Running

```bash
# Start Ocean backend on port 8000
cd /Users/aideveloper/ocean-backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify backend is accessible:
```bash
curl http://localhost:8000/health
```

### 2. Deploy Kong Configuration via Deck (Recommended)

#### Install Deck CLI

```bash
# macOS
brew install deck

# Linux
curl -sL https://github.com/Kong/deck/releases/download/v1.29.0/deck_1.29.0_linux_amd64.tar.gz -o deck.tar.gz
tar -xzf deck.tar.gz -C /tmp
sudo cp /tmp/deck /usr/local/bin/
```

#### Validate Configuration

```bash
cd /Users/aideveloper/ocean-backend
deck validate --config kong.yml
```

**Expected Output:**
```
All validation checks passed!
```

#### Deploy Configuration

```bash
deck sync --config kong.yml
```

**Expected Output:**
```
creating service ocean-backend
creating route ocean-health
creating route ocean-pages-create
creating route ocean-pages-list
...
creating consumer ocean-test-user
creating key-auth credential for consumer ocean-test-user
Summary:
  Created: 35 routes, 1 service, 2 consumers
  Updated: 0
  Deleted: 0
```

### 3. Deploy Configuration via Admin API (Alternative)

If Deck is not available, use the Kong Admin API:

```bash
# Create the service
curl -i -X POST http://localhost:8001/services \
  --data name=ocean-backend \
  --data url='http://host.docker.internal:8000'

# Create routes and plugins individually
# (See scripts/deploy_kong_manual.sh for complete script)
```

**Note**: Using Deck is strongly recommended as it's declarative and version-controlled.

---

## Testing Setup

### 1. Test Health Endpoint (No Auth Required)

```bash
curl -i http://localhost:8000/health
```

**Expected Response:**
```
HTTP/1.1 200 OK
X-Kong-Upstream: ocean-backend
X-Kong-Proxy: true
X-Request-ID: <uuid>
Content-Type: application/json

{
  "status": "healthy",
  "service": "ocean-backend",
  "version": "0.1.0"
}
```

### 2. Test Protected Endpoint Without API Key

```bash
curl -i http://localhost:8000/api/v1/ocean/pages
```

**Expected Response:**
```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Key realm="kong"

{
  "message": "No API key found in request"
}
```

### 3. Test Protected Endpoint With API Key

```bash
curl -i http://localhost:8000/api/v1/ocean/pages \
  -H "apikey: test-api-key-123456789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1703432400
X-Kong-Upstream: ocean-backend
X-Kong-Proxy: true
Content-Type: application/json

{
  "pages": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

### 4. Test Rate Limiting

Use the automated test script:

```bash
cd /Users/aideveloper/ocean-backend
./scripts/test_rate_limits.sh
```

(See [Rate Limit Testing Script](#rate-limit-testing-script) section below)

---

## Rate Limits Summary

### Rate Limit Tiers

| Endpoint Category | Rate Limit | Justification |
|------------------|------------|---------------|
| **Health Endpoints** | No limit | Status checks should never be rate limited |
| **Read Operations** | 1000 req/min | High throughput for browsing, listing |
| **Write Operations** | 100 req/min | Moderate limit for creates, updates, deletes |
| **Search Operations** | 50 req/min | Resource-intensive semantic search |
| **Batch Operations** | 10 req/min | Very expensive - creates many resources |

### Detailed Breakdown

#### Read Operations (1000 req/min)
- `GET /api/v1/ocean/pages` - List pages
- `GET /api/v1/ocean/pages/{id}` - Get page
- `GET /api/v1/ocean/blocks` - List blocks
- `GET /api/v1/ocean/blocks/{id}` - Get block
- `GET /api/v1/ocean/blocks/{id}/embedding` - Get embedding metadata
- `GET /api/v1/ocean/pages/{id}/backlinks` - Get page backlinks
- `GET /api/v1/ocean/blocks/{id}/backlinks` - Get block backlinks
- `GET /api/v1/ocean/tags` - List tags

#### Write Operations (100 req/min)
- `POST /api/v1/ocean/pages` - Create page
- `PUT /api/v1/ocean/pages/{id}` - Update page
- `DELETE /api/v1/ocean/pages/{id}` - Delete page
- `POST /api/v1/ocean/pages/{id}/move` - Move page
- `POST /api/v1/ocean/blocks` - Create block
- `PUT /api/v1/ocean/blocks/{id}` - Update block
- `DELETE /api/v1/ocean/blocks/{id}` - Delete block
- `POST /api/v1/ocean/blocks/{id}/move` - Move block
- `PUT /api/v1/ocean/blocks/{id}/convert` - Convert block
- `POST /api/v1/ocean/links` - Create link
- `DELETE /api/v1/ocean/links/{id}` - Delete link
- `POST /api/v1/ocean/tags` - Create tag
- `PUT /api/v1/ocean/tags/{id}` - Update tag
- `DELETE /api/v1/ocean/tags/{id}` - Delete tag
- `POST /api/v1/ocean/blocks/{id}/tags` - Assign tag
- `DELETE /api/v1/ocean/blocks/{id}/tags/{tag_id}` - Remove tag

#### Search Operations (50 req/min)
- `GET /api/v1/ocean/search?q={query}` - Hybrid semantic + metadata search

#### Batch Operations (10 req/min)
- `POST /api/v1/ocean/blocks/batch` - Create multiple blocks

### Rate Limit Headers

Every response includes:
- `X-RateLimit-Limit`: Maximum requests allowed per minute
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### Exceeding Rate Limits

When rate limit is exceeded:

**Response:**
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703432460
Retry-After: 45

{
  "message": "API rate limit exceeded"
}
```

**Client Behavior:**
- Respect `Retry-After` header (seconds until retry)
- Implement exponential backoff
- Cache read operations when possible
- Use batch endpoints for bulk operations

---

## API Key Management

### Creating API Keys via Admin API

#### 1. Create Consumer

```bash
curl -i -X POST http://localhost:8001/consumers \
  --data username=ocean-client-1 \
  --data custom_id=client-001
```

#### 2. Create API Key for Consumer

```bash
curl -i -X POST http://localhost:8001/consumers/ocean-client-1/key-auth \
  --data key=my-unique-api-key-12345
```

**Response:**
```json
{
  "id": "abc123",
  "consumer": {"id": "def456"},
  "key": "my-unique-api-key-12345",
  "created_at": 1703432400
}
```

#### 3. Test API Key

```bash
curl -i http://localhost:8000/api/v1/ocean/pages \
  -H "apikey: my-unique-api-key-12345" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Listing API Keys

```bash
# List all consumers
curl http://localhost:8001/consumers

# List keys for specific consumer
curl http://localhost:8001/consumers/ocean-client-1/key-auth
```

### Revoking API Keys

```bash
# Delete specific key
curl -i -X DELETE http://localhost:8001/consumers/ocean-client-1/key-auth/{key-id}

# Delete entire consumer (revokes all keys)
curl -i -X DELETE http://localhost:8001/consumers/ocean-client-1
```

### Pre-configured Test Keys

The `kong.yml` includes a test consumer:

- **Username**: `ocean-test-user`
- **API Key**: `test-api-key-123456789`
- **Custom ID**: `test-user-123`
- **Tags**: `development`, `testing`

**Use for development only - delete in production!**

---

## Monitoring & Logs

### Viewing Kong Logs

#### Docker

```bash
# Proxy logs (all API requests)
docker logs -f kong-gateway

# Admin API logs
docker logs -f kong-gateway --tail=100 | grep admin
```

#### Native Installation

```bash
# Proxy logs
tail -f /usr/local/kong/logs/access.log

# Error logs
tail -f /usr/local/kong/logs/error.log

# Admin logs
tail -f /usr/local/kong/logs/admin_access.log
```

### Request Tracing

Every request gets a correlation ID:

```bash
curl -i http://localhost:8000/api/v1/ocean/pages \
  -H "apikey: test-api-key-123456789"
```

**Response Headers:**
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Kong-Proxy: true
X-Kong-Upstream: ocean-backend
```

Search logs by correlation ID:
```bash
docker logs kong-gateway | grep "550e8400-e29b-41d4-a716-446655440000"
```

### Kong Admin Dashboard

Access Kong Manager (Enterprise only):
```
http://localhost:8002
```

For OSS, use third-party tools:
- **Konga**: Web UI for Kong (https://github.com/pantsel/konga)
- **Kong Admin GUI**: Community dashboards

### Prometheus Metrics (Optional)

Enable Prometheus plugin:

```bash
curl -i -X POST http://localhost:8001/plugins \
  --data name=prometheus
```

Metrics endpoint:
```
http://localhost:8001/metrics
```

---

## Troubleshooting

### Problem: "Failed to connect to upstream"

**Symptoms:**
```
HTTP/1.1 502 Bad Gateway
{
  "message": "An invalid response was received from the upstream server"
}
```

**Solutions:**

1. **Check Ocean backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check Docker network (if using Docker):**
   ```bash
   # Update kong.yml service URL to:
   # url: http://host.docker.internal:8000  # For Docker Desktop
   # url: http://172.17.0.1:8000            # For Linux Docker
   ```

3. **Verify Kong can reach backend:**
   ```bash
   docker exec kong-gateway curl http://host.docker.internal:8000/health
   ```

### Problem: "No API key found in request"

**Symptoms:**
```
HTTP/1.1 401 Unauthorized
{
  "message": "No API key found in request"
}
```

**Solutions:**

1. **Ensure API key is in header:**
   ```bash
   curl http://localhost:8000/api/v1/ocean/pages \
     -H "apikey: test-api-key-123456789"
   ```

2. **Verify consumer exists:**
   ```bash
   curl http://localhost:8001/consumers/ocean-test-user
   ```

3. **Check key-auth credential:**
   ```bash
   curl http://localhost:8001/consumers/ocean-test-user/key-auth
   ```

### Problem: Rate Limits Not Working

**Symptoms:**
- No `X-RateLimit-*` headers
- No 429 responses when exceeding limits

**Solutions:**

1. **Check rate-limiting plugin is active:**
   ```bash
   curl http://localhost:8001/routes/ocean-pages-create/plugins
   ```

2. **Verify route configuration:**
   ```bash
   curl http://localhost:8001/routes/ocean-pages-create
   ```

3. **Test with burst script:**
   ```bash
   ./scripts/test_rate_limits.sh
   ```

### Problem: CORS Errors in Browser

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/v1/ocean/pages' from origin
'http://localhost:3000' has been blocked by CORS policy
```

**Solutions:**

1. **Verify CORS plugin is enabled:**
   ```bash
   curl http://localhost:8001/routes/ocean-pages-list/plugins | jq '.data[] | select(.name == "cors")'
   ```

2. **Test preflight request:**
   ```bash
   curl -i -X OPTIONS http://localhost:8000/api/v1/ocean/pages \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET"
   ```

   **Expected:**
   ```
   HTTP/1.1 200 OK
   Access-Control-Allow-Origin: *
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
   ```

### Problem: Configuration Deployment Fails

**Symptoms:**
```
deck sync failed: validation error
```

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   deck validate --config kong.yml
   ```

2. **Check Kong version compatibility:**
   ```bash
   kong version
   # Should be 3.0 or higher
   ```

3. **Review specific errors:**
   ```bash
   deck sync --config kong.yml --verbose
   ```

---

## Production Deployment

### Pre-Production Checklist

- [ ] Remove test consumers and API keys
- [ ] Generate production API keys with strong entropy
- [ ] Configure database backups (PostgreSQL)
- [ ] Set up SSL/TLS certificates
- [ ] Configure logging to external service (Datadog, ELK, etc.)
- [ ] Enable Prometheus metrics
- [ ] Set up health check monitoring
- [ ] Configure rate limiting per organization (not global)
- [ ] Review CORS origins (replace `*` with specific domains)
- [ ] Set up Kong clustering (if high availability required)
- [ ] Configure secrets management (Vault, AWS Secrets Manager)
- [ ] Test disaster recovery procedures

### Remove Test Consumers

```bash
# Delete test consumer
curl -i -X DELETE http://localhost:8001/consumers/ocean-test-user
curl -i -X DELETE http://localhost:8001/consumers/ocean-prod-user
```

### Generate Production API Keys

```bash
# Generate cryptographically secure key
API_KEY=$(openssl rand -base64 32)
echo "Generated API Key: $API_KEY"

# Create production consumer
curl -i -X POST http://localhost:8001/consumers \
  --data username=prod-client-001 \
  --data custom_id=production-001

# Assign generated key
curl -i -X POST http://localhost:8001/consumers/prod-client-001/key-auth \
  --data key="$API_KEY"
```

### Enable SSL/TLS

Update `kong.yml` or set environment variables:

```bash
# Environment variables for Kong
export KONG_SSL_CERT=/path/to/cert.pem
export KONG_SSL_CERT_KEY=/path/to/key.pem
export KONG_PROXY_LISTEN="0.0.0.0:8000, 0.0.0.0:8443 ssl"
```

Or use Let's Encrypt plugin:

```bash
curl -i -X POST http://localhost:8001/plugins \
  --data name=acme \
  --data config.account_email=admin@ainative.studio \
  --data config.domains[]=api.ainative.studio
```

### Configure External Logging

```bash
# Datadog
curl -i -X POST http://localhost:8001/plugins \
  --data name=datadog \
  --data config.host=localhost \
  --data config.port=8125

# HTTP Log
curl -i -X POST http://localhost:8001/plugins \
  --data name=http-log \
  --data config.http_endpoint=https://logs.ainative.studio/kong
```

### Environment-Specific Configuration

Create separate configurations:

- `kong.dev.yml` - Development (localhost, test keys)
- `kong.staging.yml` - Staging (staging URLs, staging keys)
- `kong.prod.yml` - Production (production URLs, prod keys)

Deploy with:
```bash
deck sync --config kong.prod.yml
```

### High Availability Setup

For production, deploy Kong in cluster mode:

```
     ┌─────────────┐
     │  Kong Node 1 │
     └──────┬───────┘
            │
   Load Balancer (Nginx/HAProxy)
            │
     ┌──────┴───────┐
     │  Kong Node 2 │
     └──────┬───────┘
            │
     Shared PostgreSQL
```

Configure each node to connect to shared database.

---

## Summary

### What We Achieved

✅ **27 routes configured** with intelligent rate limiting
✅ **API key authentication** on all protected endpoints
✅ **CORS support** for cross-origin requests
✅ **Rate limit tiers** based on operation cost
✅ **Request tracing** with correlation IDs
✅ **Response headers** with rate limit metadata
✅ **Health endpoint** unrestricted for monitoring
✅ **Production-ready** configuration with security best practices

### Next Steps

1. **Deploy to staging** environment and run integration tests
2. **Set up monitoring** with Prometheus and Grafana
3. **Configure alerts** for rate limit violations
4. **Implement API versioning** strategy
5. **Add request/response logging** for audit trails
6. **Enable caching** for read-heavy endpoints
7. **Set up API analytics** to understand usage patterns

### Support & Resources

- **Kong Documentation**: https://docs.konghq.com/gateway/latest/
- **Deck CLI**: https://docs.konghq.com/deck/latest/
- **Kong Community**: https://discuss.konghq.com/
- **Ocean Backend Repo**: https://github.com/ainative-studio/ocean-backend

---

**Configured by**: DevOps Team
**Issue Reference**: #18
**Last Updated**: 2025-12-24
**Kong Version**: 3.4+
**Config Format**: Deck 3.0
