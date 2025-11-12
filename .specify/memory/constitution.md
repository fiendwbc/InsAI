<!--
VERSION: 1.0.0 → New constitution established
MODIFIED PRINCIPLES: N/A (initial version)
ADDED SECTIONS: All (initial establishment)
REMOVED SECTIONS: N/A

TEMPLATE STATUS:
✅ plan-template.md - Constitution Check section present and compatible
✅ spec-template.md - User scenarios and requirements structure compatible
✅ tasks-template.md - Task structure supports principle-driven development

FOLLOW-UP TODOS: None
-->

# InsAI Trading Platform Constitution

## Core Principles

### I. Code Quality First

Code MUST be clear, maintainable, and self-documenting. Every module MUST have a single, well-defined responsibility. Complex logic MUST be broken into comprehensible units with explicit naming that reveals intent.

**Non-negotiables**:
- No functions exceeding 100 lines without documented justification
- No magic numbers or unexplained constants - use named constants with clear intent
- All public interfaces MUST have comprehensive docstrings (Google style for Python, JSDoc for TypeScript)
- Code reviews MUST verify readability before merge - "clever" code is rejected unless proven necessary
- Type hints MUST be used for all Python functions; TypeScript strict mode MUST be enabled

**Rationale**: Trading systems require rapid debugging under pressure. Opaque code costs time and money. Clear code is maintainable code.

### II. Testing Standards (NON-NEGOTIABLE)

All features MUST follow Test-Driven Development (TDD). Tests MUST be written before implementation, verified to fail, then implementation proceeds to green state.

**Testing hierarchy** (all MUST be present):
1. **Contract tests**: API/interface contracts MUST not break without major version bump
2. **Integration tests**: Component interactions MUST be verified (e.g., sentiment analyzer + data fetcher)
3. **Unit tests**: Individual functions/classes MUST be independently testable
4. **Performance tests**: MUST verify response time, throughput constraints per feature spec

**Coverage requirements**:
- Minimum 80% line coverage for business logic
- 100% coverage for risk/financial calculation modules
- All error paths MUST have explicit test cases

**Test organization**:
```
tests/
├── contract/     # API stability tests
├── integration/  # Component interaction tests
├── unit/         # Isolated component tests
└── performance/  # Load, latency, throughput tests
```

**Rationale**: Financial systems cannot afford production bugs. Tests are insurance. TDD ensures testability by design.

### III. User Experience Consistency

All user-facing interfaces (UI, CLI, API) MUST provide predictable, intuitive interactions. Error messages MUST be actionable. Feedback MUST be immediate for user actions (<200ms visual acknowledgment).

**UI/UX requirements**:
- All async operations MUST show loading states within 100ms
- Error messages MUST specify what happened, why, and what the user should do
- UI state MUST be recoverable - no data loss on navigation/refresh
- Accessibility MUST meet WCAG 2.1 AA standards (keyboard nav, screen reader support)
- Design system components MUST be reused - no one-off UI patterns without design review

**API requirements**:
- REST endpoints MUST follow consistent naming (plural nouns for collections)
- Responses MUST use standard HTTP status codes semantically
- Errors MUST include machine-readable error codes + human-readable messages
- Pagination MUST be consistent across all list endpoints
- API versioning MUST be explicit in path (e.g., `/api/v1/trades`)

**Rationale**: Inconsistent UX destroys user confidence in trading tools. Predictability reduces cognitive load under market stress.

### IV. Performance Requirements

All features MUST define and meet performance budgets before merging. Performance regressions MUST be caught in CI.

**Standard performance budgets**:
- **API latency**: p95 < 200ms for read operations, p95 < 500ms for write operations
- **UI rendering**: First Contentful Paint < 1.5s, Time to Interactive < 3.5s
- **Real-time data**: Market data updates MUST reflect within 100ms of reception
- **Database queries**: MUST complete in <50ms (p95), MUST use indexes for frequently queried fields
- **Memory**: Backend services MUST NOT exceed 512MB under normal load (10k requests/min)

**Monitoring requirements**:
- All critical paths MUST have performance instrumentation (logging, metrics)
- Performance tests MUST run in CI for any PR touching critical paths
- Performance dashboard MUST track p50/p95/p99 latencies for all API endpoints

**Rationale**: Slow systems lose money in trading. Performance is a feature, not an optimization.

### V. Observability & Debugging

Every component MUST be introspectable in production. Logs MUST tell a story. Metrics MUST be actionable.

**Logging requirements**:
- Structured logging MUST be used (JSON format) with consistent fields: `timestamp`, `level`, `service`, `trace_id`, `message`
- Log levels MUST be semantic: ERROR = needs immediate action, WARN = degraded but functional, INFO = key business events
- Sensitive data (API keys, user credentials) MUST NEVER be logged
- All external API calls MUST log request/response metadata (duration, status, endpoint)

**Metrics requirements**:
- All services MUST expose health/readiness endpoints
- Business metrics MUST be tracked: trade execution count, sentiment analysis latency, data fetch success rate
- System metrics MUST be tracked: CPU, memory, request rate, error rate
- Alerts MUST be configured for SLO violations (e.g., error rate >1%, p95 latency >500ms)

**Distributed tracing**:
- All requests MUST carry a unique `trace_id` through the entire call chain
- Critical flows (trade execution, data pipeline) MUST be traceable end-to-end

**Rationale**: You can't fix what you can't see. Observability is the foundation of reliability.

## Security & Risk Management

All code handling financial data or external APIs MUST follow security best practices.

**Authentication/Authorization**:
- API keys MUST be rotated quarterly
- Secrets MUST be stored in environment variables or secret management system (never in code)
- JWT tokens MUST expire within 1 hour; refresh tokens within 7 days
- All API endpoints MUST validate authorization before processing

**Input validation**:
- All user inputs MUST be validated at API boundary (type, range, format)
- SQL injection, XSS, command injection MUST be prevented through parameterization
- File uploads MUST be scanned for malware and size-limited

**Data protection**:
- User credentials MUST be hashed with bcrypt (cost factor ≥12)
- Financial data MUST be encrypted at rest (AES-256)
- API communication MUST use TLS 1.3+

**Risk controls**:
- Trading operations MUST have rate limits (e.g., max 100 trades/user/day)
- Large trades MUST require confirmation
- System MUST have circuit breakers for anomalous activity (e.g., 10x average trade volume)

**Rationale**: Security breaches destroy trust and expose legal liability. Defense in depth is mandatory.

## Development Workflow

### Code Review Standards

All code MUST be reviewed before merge. Reviewers MUST verify:

1. **Constitution compliance**: Does code follow all principles above?
2. **Test coverage**: Are tests present, meaningful, and passing?
3. **Performance**: Does this meet performance budgets?
4. **Security**: Are there potential vulnerabilities?
5. **Readability**: Can a new team member understand this in 6 months?

PRs MUST be small (<500 lines diff) to enable thorough review. Large changes MUST be broken into smaller, reviewable increments.

### Version Control

- `main` branch MUST always be deployable
- Feature branches MUST be named `###-feature-name` (e.g., `042-sentiment-analysis`)
- Commits MUST have clear messages describing why (not what) - the diff shows what
- No force push to `main` - ever
- All merges MUST be via PR with passing CI

### CI/CD Requirements

CI MUST run on every PR and verify:
- All tests pass (unit, integration, contract, performance)
- Code coverage meets minimum thresholds
- Linting passes (flake8, eslint with project configs)
- Type checking passes (mypy for Python, tsc for TypeScript)
- Security scanning passes (dependencies, code patterns)
- Build succeeds

CD MUST deploy automatically to staging on `main` merge. Production deploys MUST be manual approval.

## Governance

This constitution supersedes all conflicting practices, style guides, or conventions. When in doubt, this document is the source of truth.

**Amendment process**:
1. Propose change via PR to this file
2. Document rationale: what problem does this solve? what alternatives were considered?
3. Requires approval from 2+ maintainers
4. Version MUST be bumped (MAJOR for principle removal/redefinition, MINOR for additions, PATCH for clarifications)
5. All dependent templates MUST be updated in same PR
6. Migration plan MUST be documented for backward-incompatible changes

**Complexity justification**:
If a feature violates a principle (e.g., exceeds performance budget, skips test requirement), it MUST be justified in the implementation plan's "Complexity Tracking" section. Justifications MUST explain:
- Why the violation is necessary
- What simpler alternatives were tried/rejected
- What technical debt this creates
- Remediation plan

**Compliance verification**:
- All PRs MUST include a constitution checklist (see plan-template.md)
- Quarterly retrospectives MUST review adherence and update principles if patterns emerge
- New team members MUST read this document during onboarding

**Version**: 1.0.0 | **Ratified**: 2025-11-11 | **Last Amended**: 2025-11-11
