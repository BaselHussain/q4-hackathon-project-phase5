---
name: database-schema
description: Design relational database schemas, create tables, and manage migrations following best practices.
---

# Database Schema Design

## Instructions

1. **Schema planning**
   - Identify entities and relationships
   - Define primary and foreign keys
   - Normalize data where appropriate

2. **Table creation**
   - Use clear and consistent naming conventions
   - Choose correct data types
   - Apply constraints (NOT NULL, UNIQUE, DEFAULT)

3. **Migrations**
   - Create version-controlled migration files
   - Separate schema changes into small, reversible steps
   - Include rollback (down) migrations

4. **Relationships**
   - One-to-one, one-to-many, many-to-many
   - Use junction tables when needed
   - Enforce referential integrity

## Best Practices
- Avoid premature optimization
- Keep schemas simple and readable
- Always index foreign keys
- Test migrations in a staging environment
- Never edit applied migrations directly

## Example Structure
```sql
-- users table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- posts table
CREATE TABLE posts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  content TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
