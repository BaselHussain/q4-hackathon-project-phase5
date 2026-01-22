# Multi-User Todo Web App Constitution

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)
All development must follow Spec-Driven Development (SDD) methodology. Features must be fully specified before implementation. Specs must include clear acceptance criteria, error paths, and constraints. No manual coding allowed - all implementation must be agent-driven using Claude Code tools.

### II. Full-Stack Modern Architecture
The application must use Next.js 16+ (App Router) for frontend and FastAPI + SQLModel for backend. Architecture must be cleanly separated with REST API contracts. Frontend and backend must be independently deployable and testable.

### III. Secure Authentication & Authorization
User authentication must use Better Auth with JWT tokens. All API endpoints must have JWT verification middleware. User isolation must be strictly enforced - each user can only access their own tasks. Passwords must be securely hashed and never stored in plain text.

### IV. Persistent Data Storage
All user tasks must be stored in Neon Serverless PostgreSQL. Database schema must be properly designed with appropriate relationships, indexes, and constraints. Data integrity must be maintained at all times.

### V. Test-First Development
TDD methodology must be strictly followed: tests written first, user approval obtained, tests fail initially, then implementation. Red-Green-Refactor cycle must be enforced. All code must have comprehensive unit and integration tests.

### VI. REST API Security
All API endpoints must be secured with proper authentication and authorization. Unauthorized access must return 401 status codes. Sensitive operations must use appropriate HTTP methods and validation. Rate limiting should be implemented for public endpoints.

### VII. Responsive & Accessible UI
Frontend must be responsive and work across all device sizes. UI must follow modern design principles and be accessible (WCAG 2.1 AA compliance). Components must be reusable and properly documented.

## Technology Stack Requirements

### Frontend Requirements
- Next.js 16+ with App Router
- TypeScript for type safety
- Responsive design using modern CSS framework
- State management with React context or appropriate library
- Comprehensive error handling and user feedback

### Backend Requirements
- FastAPI with SQLModel for data access
- JWT authentication with Better Auth integration
- RESTful API design with proper HTTP methods
- Comprehensive input validation and error handling
- Proper CORS configuration for frontend access

### Database Requirements
- Neon Serverless PostgreSQL
- Proper schema design with relationships
- Data migration strategy for schema changes
- Backup and recovery procedures
- Connection pooling for performance

### Security Requirements
- All passwords hashed with bcrypt or equivalent
- JWT tokens with appropriate expiration
- CSRF protection for state-changing operations
- Input validation on both client and server
- Secure headers and CORS configuration

## Development Workflow

### Code Quality Standards
- All code must follow consistent style guidelines
- Comprehensive documentation for all public APIs
- Meaningful commit messages following conventional commits
- Code reviews required for all changes
- No direct pushes to main branch

### Testing Requirements
- Unit tests for all functions and components
- Integration tests for API endpoints
- End-to-end tests for critical user flows
- Test coverage must be maintained above 80%
- All tests must pass before deployment

### Documentation Standards
- README.md must contain complete setup instructions
- All environment variables must be documented
- API documentation must be up-to-date
- Architecture decisions must be recorded in ADRs
- Change log must be maintained

## Governance

The constitution supersedes all other development practices. All team members must comply with these principles. Amendments require:
- Documentation of the change and rationale
- Team approval through pull request process
- Migration plan for existing code if needed
- Version update following semantic versioning

All PRs and code reviews must verify compliance with this constitution. Complexity must be justified and kept to minimum viable implementation. Use CLAUDE.md for runtime development guidance and tool usage.

**Version**: 1.0.0 | **Ratified**: 2026-01-19 | **Last Amended**: 2026-01-19