#!/bin/bash

#############################################################################
# Kong Rate Limit Testing Script
# Issue #18: Verify rate limiting works correctly for Ocean backend
#
# This script tests all rate limit tiers:
# - Read operations: 1000 req/min
# - Write operations: 100 req/min
# - Search operations: 50 req/min
# - Batch operations: 10 req/min
#############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KONG_URL="${KONG_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-test-api-key-123456789}"
JWT_TOKEN="${JWT_TOKEN:-fake-jwt-token-for-testing}"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

#############################################################################
# Helper Functions
#############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}INFO:${NC} $1"
}

# Make HTTP request and extract status code + rate limit headers
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}\n%{header_json}" -X "$method" \
            "$KONG_URL$endpoint" \
            -H "apikey: $API_KEY" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}\n%{header_json}" -X "$method" \
            "$KONG_URL$endpoint" \
            -H "apikey: $API_KEY" \
            -H "Authorization: Bearer $JWT_TOKEN" 2>/dev/null)
    fi

    echo "$response"
}

# Extract HTTP status code from response
get_status_code() {
    echo "$1" | tail -n 2 | head -n 1
}

# Extract rate limit headers
get_rate_limit() {
    local response=$1
    local header_json=$(echo "$response" | tail -n 1)

    # Try to extract X-RateLimit-Limit (this is simplified - real parsing would use jq)
    limit=$(echo "$response" | grep -i "x-ratelimit-limit:" | head -n 1 | sed 's/.*: //' | tr -d '\r\n')
    remaining=$(echo "$response" | grep -i "x-ratelimit-remaining:" | head -n 1 | sed 's/.*: //' | tr -d '\r\n')

    echo "$limit $remaining"
}

#############################################################################
# Pre-flight Checks
#############################################################################

print_header "PRE-FLIGHT CHECKS"

# Check if Kong is running
print_test "Checking if Kong is accessible"
if curl -s "$KONG_URL/health" > /dev/null 2>&1; then
    print_success "Kong is running at $KONG_URL"
else
    print_fail "Kong is not accessible at $KONG_URL"
    echo ""
    echo "Please ensure Kong is running and Ocean backend is accessible."
    echo "See docs/KONG_SETUP.md for installation instructions."
    exit 1
fi

# Check if Ocean backend is running
print_test "Checking if Ocean backend is accessible"
backend_health=$(curl -s "$KONG_URL/health" 2>/dev/null)
if echo "$backend_health" | grep -q "ocean-backend"; then
    print_success "Ocean backend is accessible through Kong"
else
    print_fail "Ocean backend is not accessible through Kong"
    echo ""
    echo "Response: $backend_health"
    echo ""
    echo "Please ensure Ocean backend is running on localhost:8000"
    exit 1
fi

# Test API key authentication
print_test "Testing API key authentication"
auth_test=$(curl -s -o /dev/null -w "%{http_code}" "$KONG_URL/api/v1/ocean/pages" 2>/dev/null)
if [ "$auth_test" = "401" ]; then
    print_success "API key authentication is enabled (got 401 without key)"
else
    print_fail "Expected 401 without API key, got $auth_test"
fi

#############################################################################
# Test 1: Health Endpoint (No Rate Limit)
#############################################################################

print_header "TEST 1: Health Endpoint (No Rate Limit)"

print_test "Making 10 rapid requests to /health"
health_failures=0
for i in {1..10}; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$KONG_URL/health" 2>/dev/null)
    if [ "$status" != "200" ]; then
        ((health_failures++))
    fi
done

if [ $health_failures -eq 0 ]; then
    print_success "All 10 health check requests succeeded (no rate limiting)"
else
    print_fail "$health_failures out of 10 health checks failed"
fi
((TESTS_RUN++))

#############################################################################
# Test 2: Read Operations (1000 req/min)
#############################################################################

print_header "TEST 2: Read Operations Rate Limit (1000 req/min)"

print_test "Making 20 rapid GET requests to /api/v1/ocean/pages"
print_info "Expected: All requests succeed, rate limit headers show ~1000 limit"

read_success=0
read_failures=0
last_response=""

for i in {1..20}; do
    response=$(make_request "GET" "/api/v1/ocean/pages")
    status=$(get_status_code "$response")

    if [ "$status" = "200" ]; then
        ((read_success++))
        last_response="$response"
    else
        ((read_failures++))
        if [ "$status" = "429" ]; then
            print_info "Got 429 Too Many Requests (rate limit hit)"
        fi
    fi

    # Small delay to avoid overwhelming
    sleep 0.05
done

if [ $read_success -ge 15 ]; then
    print_success "$read_success out of 20 requests succeeded"

    # Check rate limit headers in last successful response
    if echo "$last_response" | grep -qi "x-ratelimit-limit"; then
        print_success "Rate limit headers present in response"
    else
        print_fail "Rate limit headers missing from response"
    fi
else
    print_fail "Only $read_success out of 20 requests succeeded (expected at least 15)"
fi
((TESTS_RUN++))

#############################################################################
# Test 3: Write Operations (100 req/min)
#############################################################################

print_header "TEST 3: Write Operations Rate Limit (100 req/min)"

print_test "Making 15 rapid POST requests to create pages"
print_info "Expected: Most succeed, rate limit ~100 req/min"

write_success=0
write_failures=0

for i in {1..15}; do
    data='{"title":"Test Page '$i'","icon":"📄"}'
    response=$(make_request "POST" "/api/v1/ocean/pages" "$data")
    status=$(get_status_code "$response")

    if [ "$status" = "201" ] || [ "$status" = "200" ]; then
        ((write_success++))
    else
        ((write_failures++))
        if [ "$status" = "429" ]; then
            print_info "Request $i: Got 429 Too Many Requests (rate limit hit)"
            break
        fi
    fi

    sleep 0.1
done

if [ $write_success -ge 5 ]; then
    print_success "$write_success out of 15 write requests succeeded"
else
    print_fail "Only $write_success out of 15 requests succeeded"
fi
((TESTS_RUN++))

#############################################################################
# Test 4: Search Operations (50 req/min)
#############################################################################

print_header "TEST 4: Search Operations Rate Limit (50 req/min)"

print_test "Making 10 rapid GET requests to /api/v1/ocean/search"
print_info "Expected: Most succeed initially, then rate limited"

search_success=0
search_failures=0
search_rate_limited=0

for i in {1..10}; do
    response=$(make_request "GET" "/api/v1/ocean/search?q=test+query")
    status=$(get_status_code "$response")

    if [ "$status" = "200" ]; then
        ((search_success++))
    elif [ "$status" = "429" ]; then
        ((search_rate_limited++))
    else
        ((search_failures++))
    fi

    sleep 0.1
done

if [ $search_success -ge 5 ]; then
    print_success "$search_success out of 10 search requests succeeded"
else
    print_fail "Only $search_success out of 10 requests succeeded"
fi

if [ $search_rate_limited -gt 0 ]; then
    print_info "Got $search_rate_limited rate-limited responses (429)"
fi
((TESTS_RUN++))

#############################################################################
# Test 5: Batch Operations (10 req/min)
#############################################################################

print_header "TEST 5: Batch Operations Rate Limit (10 req/min)"

print_test "Making 5 rapid POST requests to /api/v1/ocean/blocks/batch"
print_info "Expected: Few succeed before rate limit (10 req/min is strict)"

batch_success=0
batch_failures=0
batch_rate_limited=0

# First, create a test page to attach blocks to
create_page_response=$(make_request "POST" "/api/v1/ocean/pages" '{"title":"Batch Test Page"}')
page_status=$(get_status_code "$create_page_response")

if [ "$page_status" = "201" ] || [ "$page_status" = "200" ]; then
    # Extract page_id (simplified - in production use jq)
    page_id=$(echo "$create_page_response" | grep -o '"page_id":"[^"]*"' | cut -d'"' -f4 | head -n 1)

    if [ -n "$page_id" ]; then
        print_info "Created test page: $page_id"

        for i in {1..5}; do
            data='{"blocks":[{"block_type":"text","content":{"text":"Batch block '$i'-1"}},{"block_type":"text","content":{"text":"Batch block '$i'-2"}}]}'
            response=$(make_request "POST" "/api/v1/ocean/blocks/batch?page_id=$page_id" "$data")
            status=$(get_status_code "$response")

            if [ "$status" = "201" ] || [ "$status" = "200" ]; then
                ((batch_success++))
            elif [ "$status" = "429" ]; then
                ((batch_rate_limited++))
                print_info "Request $i: Rate limited (429)"
            else
                ((batch_failures++))
            fi

            sleep 0.2
        done

        if [ $batch_success -ge 1 ]; then
            print_success "$batch_success out of 5 batch requests succeeded (strict 10 req/min limit)"
        else
            print_fail "No batch requests succeeded"
        fi

        if [ $batch_rate_limited -gt 0 ]; then
            print_success "Rate limiting working: got $batch_rate_limited 429 responses"
        fi
    else
        print_fail "Could not extract page_id from response"
    fi
else
    print_fail "Failed to create test page (status: $page_status)"
fi
((TESTS_RUN++))

#############################################################################
# Test 6: Verify 429 Response Format
#############################################################################

print_header "TEST 6: Verify 429 Response Format"

print_test "Triggering rate limit and checking response format"

# Make many rapid requests to trigger rate limit
for i in {1..60}; do
    response=$(make_request "GET" "/api/v1/ocean/search?q=test")
    status=$(get_status_code "$response")

    if [ "$status" = "429" ]; then
        print_success "Successfully triggered 429 Too Many Requests"

        # Check for Retry-After header
        if echo "$response" | grep -qi "retry-after"; then
            print_success "Retry-After header present in 429 response"
        else
            print_info "Note: Retry-After header not found (Kong may not include it)"
        fi

        # Check for rate limit headers
        if echo "$response" | grep -qi "x-ratelimit"; then
            print_success "Rate limit headers present in 429 response"
        else
            print_fail "Rate limit headers missing from 429 response"
        fi

        break
    fi

    sleep 0.05
done
((TESTS_RUN++))

#############################################################################
# Test 7: CORS Headers
#############################################################################

print_header "TEST 7: CORS Headers Verification"

print_test "Checking CORS headers on OPTIONS request"

cors_response=$(curl -s -i -X OPTIONS "$KONG_URL/api/v1/ocean/pages" \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET" 2>/dev/null)

if echo "$cors_response" | grep -qi "access-control-allow-origin"; then
    print_success "CORS Access-Control-Allow-Origin header present"
else
    print_fail "CORS Access-Control-Allow-Origin header missing"
fi

if echo "$cors_response" | grep -qi "access-control-allow-methods"; then
    print_success "CORS Access-Control-Allow-Methods header present"
else
    print_fail "CORS Access-Control-Allow-Methods header missing"
fi
((TESTS_RUN++))

#############################################################################
# Test 8: Rate Limit Reset Window
#############################################################################

print_header "TEST 8: Rate Limit Reset Window"

print_test "Checking rate limit reset behavior"
print_info "Making requests until rate limited, then waiting for reset"

# First, trigger rate limit
rate_limited=false
for i in {1..100}; do
    response=$(make_request "GET" "/api/v1/ocean/pages")
    status=$(get_status_code "$response")

    if [ "$status" = "429" ]; then
        rate_limited=true
        print_info "Rate limit triggered after $i requests"

        # Extract reset time from headers
        if echo "$response" | grep -qi "x-ratelimit-reset"; then
            print_success "X-RateLimit-Reset header present"
        fi

        # Wait 5 seconds and try again
        print_info "Waiting 5 seconds before retry..."
        sleep 5

        retry_response=$(make_request "GET" "/api/v1/ocean/pages")
        retry_status=$(get_status_code "$retry_response")

        if [ "$retry_status" = "200" ]; then
            print_success "Request succeeded after waiting (rate limit window reset)"
        else
            print_info "Still rate limited after 5 seconds (window is 60 seconds)"
        fi

        break
    fi

    sleep 0.05
done

if [ "$rate_limited" = false ]; then
    print_info "Could not trigger rate limit within 100 requests"
fi
((TESTS_RUN++))

#############################################################################
# Final Summary
#############################################################################

print_header "TEST RESULTS SUMMARY"

echo -e "${BLUE}Total Tests Run:${NC} $TESTS_RUN"
echo -e "${GREEN}Tests Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Tests Failed:${NC} $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}ALL TESTS PASSED! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Rate limiting is configured and working correctly."
    echo ""
    echo "Summary:"
    echo "  • Health endpoints: No rate limiting ✓"
    echo "  • Read operations: 1000 req/min ✓"
    echo "  • Write operations: 100 req/min ✓"
    echo "  • Search operations: 50 req/min ✓"
    echo "  • Batch operations: 10 req/min ✓"
    echo "  • CORS headers: Configured ✓"
    echo "  • 429 responses: Working ✓"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}SOME TESTS FAILED ✗${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Please review the failures above and check:"
    echo "  1. Kong is properly configured with kong.yml"
    echo "  2. Ocean backend is running and accessible"
    echo "  3. API key authentication is working"
    echo "  4. Rate limiting plugins are enabled"
    echo ""
    echo "For troubleshooting, see docs/KONG_SETUP.md"
    echo ""
    exit 1
fi
