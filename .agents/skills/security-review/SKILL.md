---
name: security-review
description: Perform a comprehensive security audit of a project or subset. Use when the user asks for a security review, security audit, vulnerability scan, penetration test, OWASP check, dependency scan, or security analysis.
---

# Security Review Skill

## Purpose

Perform a comprehensive security analysis of a project or a specified subset.
Identify potential security vulnerabilities, weaknesses, and security-relevant bugs.

## Scope

Unless explicitly stated otherwise: the entire project including all source code, configuration files, metadata, dependencies, and documentation.

## Workflow

Execute these phases in order. Skip phases only if the user explicitly narrows scope.

### Phase 1: Reconnaissance

1. Map the project structure: entry points, API routes, authentication flows, data stores
2. Identify technology stack: frameworks, libraries, languages, infrastructure
3. Locate sensitive files: `.env`, credentials, secrets, keys, tokens
4. Review `.gitignore`, `.dockerignore`, and deployment configs for exposed secrets
5. Check for committed secrets in git history (`git log -p --all -S "password" -S "api_key" -S "secret"`)

### Phase 2: Static Analysis

1. Scan source code for security anti-patterns and vulnerabilities
2. Check for hardcoded secrets, credentials, API keys, and tokens
3. Review input validation, sanitization, and output encoding
4. Analyze authentication and authorization mechanisms
5. Inspect error handling for information leakage
6. Review CORS, CSP, and other security headers
7. Check for SQL injection, XSS, CSRF, SSRF, and injection vectors
8. Verify secure handling of file uploads and path traversal
9. Review session management and cookie attributes (`Secure`, `HttpOnly`, `SameSite`)

### Phase 3: Dependency Analysis

1. Identify outdated libraries and frameworks
2. Check dependencies against known vulnerability databases (CVE, GHSA, SNYK)
3. Review `package.json`, `requirements.txt`, `Pipfile`, `Gemfile`, etc.
4. Flag transitive dependencies with known issues
5. Check for deprecated or unmaintained packages
6. Verify lock file integrity (`package-lock.json`, `poetry.lock`, etc.)
7. Run available vulnerability scanners: `npm audit`, `pip audit`, `safety check`, `cargo audit`

### Phase 4: Build & Runtime Analysis

1. Build the entire project and analyze build output and logs
2. Treat warnings as errors – report all warnings
3. Check for insecure build configurations
4. Review Dockerfiles for security best practices (non-root user, minimal base image, no secrets in layers)
5. Analyze environment variable handling and secret injection
6. Review CI/CD pipelines for security misconfigurations

### Phase 5: OWASP Top 10 Checklist

Check against the current OWASP Top 10 (2021):

| ID | Category | Check |
|----|----------|-------|
| A01 | Broken Access Control | Verify authorization checks on all endpoints and routes |
| A02 | Cryptographic Failures | Ensure TLS everywhere, no weak algorithms, proper hashing (bcrypt, argon2) |
| A03 | Injection | SQL, NoSQL, OS command, LDAP, ORM, XSS – validate all inputs |
| A04 | Insecure Design | Threat modeling, secure by design, defense in depth |
| A05 | Security Misconfiguration | Default credentials, verbose errors, unnecessary features, open ports |
| A06 | Vulnerable and Outdated Components | Dependency scanning, patch management |
| A07 | Identification and Authentication Failures | Brute force protection, MFA, session management, credential recovery |
| A08 | Software and Data Integrity Failures | CI/CD integrity, signed packages, deserialization risks |
| A09 | Security Logging and Monitoring Failures | Audit logs, alerting, log injection prevention |
| A10 | Server-Side Request Forgery (SSRF) | Validate URLs, restrict outbound requests, network segmentation |

### Phase 6: Infrastructure & Deployment

1. Review reverse proxy configuration (Caddy, Nginx) for security headers
2. Verify TLS/SSL configuration and certificate management
3. Check Docker Compose for exposed ports, privileged containers, missing resource limits
4. Review firewall rules and network segmentation
5. Verify secrets management (no secrets in code, use env vars or vault)
6. Check rate limiting and DDoS protection

### Phase 7: Frontend-Specific Checks

1. Content Security Policy (CSP) implementation
2. Subresource Integrity (SRI) for external scripts
3. Secure cookie attributes for session/auth tokens
4. DOM-based XSS prevention
5. Safe usage of `v-html`, `innerHTML`, `dangerouslySetInnerHTML`
6. Protection against clickjacking (X-Frame-Options)
7. Secure localStorage/sessionStorage usage (no sensitive data)

### Phase 8: Backend-Specific Checks

1. Input validation on all API endpoints
2. Parameterized queries / ORM usage (no raw SQL)
3. Authentication middleware applied consistently
4. Authorization checks on every protected resource
5. Rate limiting on authentication and sensitive endpoints
6. Secure password hashing (bcrypt, argon2 – not MD5/SHA1)
7. File upload validation (type, size, path sanitization)
8. Logging of security events without sensitive data
9. Graceful error handling (no stack traces to clients)

### Phase 9: MQTT & IoT-Specific Checks (if applicable)

1. Broker authentication and authorization (ACLs)
2. TLS encryption for MQTT connections
3. Topic namespace isolation
4. Payload validation and sanitization
5. Prevention of topic injection
6. Client certificate validation
7. Bridge security (if connecting multiple brokers)

## Output Format

Always structure findings in this order:

### 1. Executive Summary

One paragraph summarizing the overall security posture, number of findings by severity, and the most critical risk.

### 2. Findings

Group by severity (Critical → High → Medium → Low → Info). Each finding:

```markdown
### [SEVERITY] Title

- **Location**: `path/to/file:line`
- **Category**: OWASP category or custom
- **Description**: What the issue is and why it matters
- **Impact**: What an attacker could achieve
- **Remediation**: Concrete steps to fix with code examples where applicable
- **References**: Relevant CVE, OWASP link, or best practice doc
```

### 3. Summary Table

```markdown
| # | Severity | Category | Location | Status |
|---|----------|----------|----------|--------|
| 1 | Critical | Injection | `src/api/users.py:42` | Open |
| 2 | High | Auth | `src/middleware/auth.ts:15` | Open |
```

### 4. Recommendations

Prioritized list of actions to improve security posture, ordered by impact and effort.

### 5. Dependency Report

List of vulnerable dependencies with current version, fixed version, and CVE references.

## Principles

- **Assume breach mentality**: Think like an attacker
- **Defense in depth**: Multiple layers of security
- **Least privilege**: Minimal permissions everywhere
- **Fail secure**: Default to deny, fail closed
- **Zero trust**: Never trust input, always verify
- **Report everything**: Even info-level findings matter
- **No false positives**: Only report issues you can substantiate with evidence

## Severity Definitions

| Severity | Definition |
|----------|------------|
| Critical | Immediate exploitation risk, direct data breach or system compromise possible |
| High | Significant risk, exploitable under common conditions |
| Medium | Moderate risk, requires specific conditions or partial access |
| Low | Minor risk, defense-in-depth improvement |
| Info | Best practice recommendation, no immediate risk |
