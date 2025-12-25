---
name: Bug Report
about: Report a bug found during beta testing
title: '[BUG] '
labels: 'bug, beta-testing'
assignees: ''
---

## Bug Description

<!-- Provide a clear and concise description of the bug -->

**Summary**:

## Severity

<!-- Select one: Critical / High / Medium / Low -->

- [ ] **Critical** - Data loss, security breach, multi-tenant isolation failure, API completely down
- [ ] **High** - Major functionality broken, incorrect data returned, significant performance issue
- [ ] **Medium** - Feature partially broken, minor data issues, moderate performance degradation
- [ ] **Low** - UI/UX improvement, documentation issue, minor edge case

## Environment

**API Endpoint**: <!-- e.g., https://ocean-backend-staging.railway.app -->
**Organization ID**: <!-- Your test organization ID -->
**Date/Time**: <!-- When did this occur? -->
**API Client**: <!-- Postman / cURL / HTTPie / Custom -->
**Operating System**: <!-- macOS 14 / Windows 11 / Linux Ubuntu 22.04 -->

## Steps to Reproduce

<!-- Provide detailed steps to reproduce the bug -->

1.
2.
3.
4.

## Expected Behavior

<!-- What should happen? -->



## Actual Behavior

<!-- What actually happens? -->



## API Request

<!-- Provide the complete API request (curl command preferred) -->

```bash
curl -X POST "{{base_url}}/api/v1/ocean/pages" \
  -H "Authorization: Bearer {{api_key}}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Page"
  }'
```

## API Response

<!-- Provide the complete API response -->

```json
{
  "error": "Internal Server Error",
  "detail": "..."
}
```

**HTTP Status Code**: <!-- e.g., 500 -->
**Response Time**: <!-- e.g., 2.3s -->

## Screenshots / Logs

<!-- If applicable, add screenshots or log excerpts -->



## Impact on Testing

<!-- How does this bug affect your ability to test Ocean Backend? -->

- [ ] Blocking - Cannot continue testing
- [ ] High Impact - Major feature unusable
- [ ] Medium Impact - Workaround available
- [ ] Low Impact - Minor inconvenience

## Workaround

<!-- If you found a workaround, describe it here -->



## Additional Context

<!-- Add any other context about the problem -->

**Frequency**: <!-- How often does this occur? Always / Sometimes / Rarely -->
**Related Features**: <!-- Are other features affected? -->
**Similar Issues**: <!-- Link to related issues if any -->

## Suggested Fix

<!-- Optional: If you have ideas on how to fix this, share them -->



---

**Beta Tester Information** (Optional)

**Name**:
**Email**:
**Beta Tester ID**:

---

## For Maintainers Only

**Priority**: <!-- P0 / P1 / P2 / P3 -->
**Assigned To**:
**Sprint**:
**Fix ETA**:
**Related PR**:

---

**Thank you for helping make Ocean Backend better!** 🙏
