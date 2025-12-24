# Ocean API Code Examples

This directory contains comprehensive code examples for all Ocean API endpoints in multiple languages.

---

## Available Examples

### [Python Examples](./python_examples.md)
Complete Python examples using the `requests` library.

**Includes:**
- Setup and configuration
- Authentication with JWT
- All 27 endpoint examples
- Error handling patterns
- Complete Python client class
- Retry logic and best practices

**Use Cases:**
- Python scripts and automation
- Data migration tools
- Server-side integrations
- CLI tools

---

### [TypeScript/JavaScript Examples](./typescript_examples.md)
TypeScript and JavaScript examples using `fetch` and `axios`.

**Includes:**
- Type definitions
- Fetch API examples
- Axios examples with interceptors
- Complete TypeScript client class
- React hooks for Ocean API

**Use Cases:**
- React/Next.js applications
- Node.js backend services
- TypeScript projects
- Frontend integrations

---

### [cURL Examples](./curl_examples.md)
Shell-friendly cURL command examples for all endpoints.

**Includes:**
- Ready-to-run cURL commands
- Environment variable setup
- Testing script (`test_ocean_api.sh`)
- Pretty printing with `jq`
- Debugging tips

**Use Cases:**
- API testing and debugging
- Shell scripts
- CI/CD pipelines
- Quick manual testing

---

## Quick Start

### Python

```bash
pip install requests
python -c "from requests import Session; session = Session(); session.headers.update({'Authorization': 'Bearer YOUR_TOKEN'}); print(session.get('http://localhost:8000/api/v1/ocean/pages').json())"
```

### TypeScript/JavaScript

```bash
npm install axios
# See typescript_examples.md for full setup
```

### cURL

```bash
export JWT_TOKEN="your_token_here"
curl -X GET "http://localhost:8000/api/v1/ocean/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

---

## Documentation Links

- **[API Reference](../API_REFERENCE.md)** - Complete API documentation with all 27 endpoints
- **[Authentication Guide](../AUTHENTICATION.md)** - JWT auth flows and multi-tenant security
- **[Error Codes](../ERROR_CODES.md)** - Error handling and troubleshooting

---

## Examples by Feature

### Pages Management
- [Python - Pages](./python_examples.md#pages-examples)
- [TypeScript - Pages](./typescript_examples.md#pages)
- [cURL - Pages](./curl_examples.md#pages-endpoints)

### Blocks & Content
- [Python - Blocks](./python_examples.md#blocks-examples)
- [TypeScript - Blocks](./typescript_examples.md#blocks)
- [cURL - Blocks](./curl_examples.md#blocks-endpoints)

### Semantic Search
- [Python - Search](./python_examples.md#search-examples)
- [TypeScript - Search](./typescript_examples.md#search)
- [cURL - Search](./curl_examples.md#search-endpoint)

### Links & Backlinks
- [Python - Links](./python_examples.md#links-examples)
- [TypeScript - Links](./typescript_examples.md#complete-typescript-client)
- [cURL - Links](./curl_examples.md#links-endpoints)

### Tags
- [Python - Tags](./python_examples.md#tags-examples)
- [TypeScript - Tags](./typescript_examples.md#complete-typescript-client)
- [cURL - Tags](./curl_examples.md#tags-endpoints)

---

## Contributing

Found an issue or want to add examples for another language? Please open an issue or submit a PR!

---

**Last Updated:** 2025-12-24
**API Version:** 0.1.0
