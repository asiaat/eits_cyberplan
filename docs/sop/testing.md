# SOP: Testing

## Backend Tests

```bash
# Run all backend tests
cd backend && pytest

# Run with coverage
pytest --cov=app tests/
```

### Test Types

- **Unit tests**: Individual functions/methods
- **Integration tests**: API endpoints with test database
- **Model tests**: Database operations

## Frontend Tests

```bash
# Run unit tests
cd frontend && pnpm test

# Run e2e tests (requires running backend)
pnpm exec playwright test
```

### Test Types

- **Component tests**: React components
- **Unit tests**: Utility functions
- **E2E tests**: Critical workflows

## Critical E2E Workflows (Playwright)

1. Login and authentication
2. Create business process
3. Create asset
4. Link asset to business process
5. Set protection needs
6. Map E-ITS module
7. Generate IMR item
8. Update IMR status
9. Upload evidence
10. Create risk
11. View dashboard