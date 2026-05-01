# SOP: Database Migrations

## Creating a Migration

```bash
# Make sure your models are updated first
cd backend
source .venv/bin/activate

# Create migration from model changes
alembic revision --autogenerate -m "describe change"

# Review the generated migration in alembic/versions/
# Edit if needed

# Apply migration
alembic upgrade head
```

## Migration Best Practices

1. **Always use autogenerate** for new tables and column changes
2. **Manual migrations** only for complex data migrations
3. **Review generated SQL** before applying
4. **Test downgrade** in development: `alembic downgrade -1`
5. **Never edit applied migrations** in shared branches

## Rolling Back

```bash
# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision>
```