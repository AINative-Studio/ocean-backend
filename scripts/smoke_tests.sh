#!/bin/bash

# Ocean Backend - Smoke Tests for Railway Deployment
# Run these tests after deployment to verify all endpoints work

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STAGING_URL="${RAILWAY_STAGING_URL:-https://ocean-backend-staging.up.railway.app}"
TIMEOUT=5

echo "========================================"
echo "Ocean Backend - Smoke Tests"
echo "========================================"
echo "Target URL: $STAGING_URL"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Test counter
PASSED=0
FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_code=${4:-200}
    local data=$5

    echo -n "Testing ${name}... "

    if [ -z "$data" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
            -m "$TIMEOUT" \
            "${STAGING_URL}${endpoint}")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
            -m "$TIMEOUT" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${STAGING_URL}${endpoint}")
    fi

    if [ "$response" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $response)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (Expected HTTP $expected_code, got $response)"
        ((FAILED++))
    fi
}

# Test endpoint with JSON response validation
test_json_endpoint() {
    local name=$1
    local endpoint=$2
    local expected_field=$3

    echo -n "Testing ${name}... "

    response=$(curl -s -m "$TIMEOUT" "${STAGING_URL}${endpoint}")

    if echo "$response" | grep -q "$expected_field"; then
        echo -e "${GREEN}✓ PASSED${NC} (Contains '$expected_field')"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (Missing '$expected_field')"
        echo "Response: $response"
        ((FAILED++))
    fi
}

echo "========================================"
echo "1. Core Endpoints"
echo "========================================"

test_endpoint "Root endpoint" "GET" "/"
test_endpoint "Health check" "GET" "/health"
test_json_endpoint "Health check content" "/health" "healthy"
test_endpoint "API info" "GET" "/api/v1/info"
test_endpoint "OpenAPI docs" "GET" "/docs" 200

echo ""
echo "========================================"
echo "2. API Endpoints"
echo "========================================"

# Test creating a page
echo -n "Testing create page... "
create_page_response=$(curl -s -m "$TIMEOUT" -X POST \
    -H "Content-Type: application/json" \
    -d '{"title":"Smoke Test Page","content":"Testing deployment"}' \
    "${STAGING_URL}/api/v1/ocean/pages")

if echo "$create_page_response" | grep -q "id"; then
    page_id=$(echo "$create_page_response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo -e "${GREEN}✓ PASSED${NC} (Created page: $page_id)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "Response: $create_page_response"
    ((FAILED++))
    page_id=""
fi

# Test listing pages (should work even if no page_id)
test_endpoint "List pages" "GET" "/api/v1/ocean/pages"

# Test getting page by ID (only if we created one)
if [ -n "$page_id" ]; then
    test_endpoint "Get page by ID" "GET" "/api/v1/ocean/pages/${page_id}"

    # Test creating a block
    echo -n "Testing create block... "
    create_block_response=$(curl -s -m "$TIMEOUT" -X POST \
        -H "Content-Type: application/json" \
        -d "{\"page_id\":\"$page_id\",\"type\":\"text\",\"content\":\"Test block content\"}" \
        "${STAGING_URL}/api/v1/ocean/blocks")

    if echo "$create_block_response" | grep -q "id"; then
        block_id=$(echo "$create_block_response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo -e "${GREEN}✓ PASSED${NC} (Created block: $block_id)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Response: $create_block_response"
        ((FAILED++))
        block_id=""
    fi

    # Test getting blocks for page
    test_endpoint "Get page blocks" "GET" "/api/v1/ocean/pages/${page_id}/blocks"
fi

echo ""
echo "========================================"
echo "3. Search Endpoints"
echo "========================================"

test_endpoint "Semantic search" "GET" "/api/v1/ocean/search?query=test&limit=5"

echo ""
echo "========================================"
echo "4. Tags Endpoints"
echo "========================================"

test_endpoint "List tags" "GET" "/api/v1/ocean/tags"

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    echo ""
    echo "Deployment is ready for use:"
    echo "  - API: $STAGING_URL"
    echo "  - Docs: ${STAGING_URL}/docs"
    echo "  - Health: ${STAGING_URL}/health"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed!${NC}"
    echo ""
    echo "Please review the failures above and check:"
    echo "  - Railway logs: railway logs"
    echo "  - Environment variables: railway variables list"
    echo "  - ZeroDB connection status"
    exit 1
fi
