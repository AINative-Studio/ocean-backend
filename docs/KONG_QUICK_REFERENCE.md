# Kong Gateway - Quick Reference

**Issue #18** | Ocean Backend API Gateway Configuration

---

## Quick Start

### 1. Start Kong (Docker)

```bash
# Start Kong with Docker Compose
docker-compose up -d kong-database kong-gateway

# Or start manually
docker run -d --name kong-gateway \
  -e KONG_DATABASE=postgres \
  -e KONG_PG_HOST=kong-database \
  -p 8000:8000 -p 8001:8001 \
  kong:3.4
```

### 2. Deploy Configuration

```bash
cd /Users/aideveloper/ocean-backend
deck sync --config kong.yml
```

### 3. Test Setup

```bash
./scripts/test_rate_limits.sh
```

---

## Rate Limits Summary

| Endpoint Category | Rate Limit | Example Endpoints |
|------------------|------------|-------------------|
| **Health** | No limit | `/health`, `/` |
| **Read** | 1000/min | `GET /pages`, `GET /blocks` |
| **Write** | 100/min | `POST /pages`, `PUT /blocks` |
| **Search** | 50/min | `GET /search?q=...` |
| **Batch** | 10/min | `POST /blocks/batch` |

---

## Common Commands

### Kong Admin API

```bash
# Check Kong status
curl http://localhost:8001/status

# List all routes
curl http://localhost:8001/routes

# List all consumers
curl http://localhost:8001/consumers

# View service configuration
curl http://localhost:8001/services/ocean-backend
```

### Consumer Management

```bash
# Create consumer
curl -X POST http://localhost:8001/consumers \
  --data username=my-client

# Create API key
curl -X POST http://localhost:8001/consumers/my-client/key-auth \
  --data key=my-secret-api-key

# Delete consumer
curl -X DELETE http://localhost:8001/consumers/my-client
```

### Testing Endpoints

```bash
# Health check (no auth)
curl http://localhost:8000/health

# Protected endpoint (requires API key)
curl http://localhost:8000/api/v1/ocean/pages \
  -H "apikey: test-api-key-123456789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check rate limit headers
curl -i http://localhost:8000/api/v1/ocean/pages \
  -H "apikey: test-api-key-123456789" | grep -i ratelimit
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `kong.yml` | Main Kong configuration (Deck format) |
| `docs/KONG_SETUP.md` | Complete setup guide |
| `scripts/test_rate_limits.sh` | Rate limit testing script |
| `docs/KONG_QUICK_REFERENCE.md` | This file |

---

## Rate Limit Response Headers

Every response includes:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1703432460
```

When rate limited (429):

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703432520
Retry-After: 45

{
  "message": "API rate limit exceeded"
}
```

---

## Troubleshooting

### Kong Not Starting

```bash
# Check logs
docker logs kong-gateway

# Restart
docker restart kong-gateway
```

### Configuration Not Applying

```bash
# Validate YAML
deck validate --config kong.yml

# Force sync
deck sync --config kong.yml --select-tag development
```

### Rate Limits Not Working

```bash
# Check plugin status
curl http://localhost:8001/routes/ocean-pages-list/plugins

# Run test suite
./scripts/test_rate_limits.sh
```

### Backend Not Accessible

```bash
# Test backend directly
curl http://localhost:8000/health

# Test through Kong
curl http://localhost:8000/health

# Check service config
curl http://localhost:8001/services/ocean-backend
```

---

## Production Checklist

- [ ] Remove test consumers (`ocean-test-user`)
- [ ] Generate strong API keys (32+ bytes)
- [ ] Configure SSL/TLS certificates
- [ ] Set up external logging (Datadog, ELK)
- [ ] Enable Prometheus metrics
- [ ] Update CORS origins (remove `*`)
- [ ] Configure database backups
- [ ] Set up monitoring alerts
- [ ] Test disaster recovery

---

## Resources

- **Full Documentation**: `docs/KONG_SETUP.md`
- **Kong Docs**: https://docs.konghq.com/gateway/latest/
- **Deck CLI**: https://docs.konghq.com/deck/latest/
- **API Reference**: `API_BLOCKS_REFERENCE.md`

---

**Last Updated**: 2025-12-24
**Kong Version**: 3.4+
**Configuration Format**: Deck 3.0
