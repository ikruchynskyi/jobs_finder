# Database Schema Documentation

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           USERS                                 │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)                  INTEGER                                │
│ email                    VARCHAR UNIQUE NOT NULL                │
│ username                 VARCHAR UNIQUE NOT NULL                │
│ hashed_password          VARCHAR NOT NULL                       │
│ full_name                VARCHAR                                │
│ is_active                BOOLEAN DEFAULT true                   │
│ is_verified              BOOLEAN DEFAULT false                  │
│ created_at               TIMESTAMP DEFAULT now()                │
│ updated_at               TIMESTAMP DEFAULT now()                │
└─────────────────────────────────────────────────────────────────┘
                              ▲ │
                              │ │ (1:M)
                              │ ▼
┌─────────────────────────────────────────────────────────────────┐
│                       USER_PROFILES                             │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)                  INTEGER                                │
│ user_id (FK)             INTEGER NOT NULL → users.id            │
│ resume_url               VARCHAR                                │
│ cover_letter_template    TEXT                                   │
│ skills                   JSON                                   │
│ experience_years         INTEGER                                │
│ linkedin_url             VARCHAR                                │
│ github_url               VARCHAR                                │
│ portfolio_url            VARCHAR                                │
│ phone                    VARCHAR                                │
│ location                 VARCHAR                                │
│ job_preferences          JSON                                   │
│ created_at               TIMESTAMP DEFAULT now()                │
│ updated_at               TIMESTAMP DEFAULT now()                │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                           JOBS                                  │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)                  INTEGER                                │
│ external_id              VARCHAR UNIQUE                         │
│ title                    VARCHAR NOT NULL                       │
│ company                  VARCHAR NOT NULL                       │
│ location                 VARCHAR                                │
│ description              TEXT                                   │
│ requirements             TEXT                                   │
│ salary_min               INTEGER                                │
│ salary_max               INTEGER                                │
│ job_type                 VARCHAR (full-time, contract, etc.)    │
│ remote                   BOOLEAN DEFAULT false                  │
│ source                   ENUM (linkedin, indeed, etc.)          │
│ source_url               VARCHAR NOT NULL                       │
│ posted_date              TIMESTAMP                              │
│ expires_date             TIMESTAMP                              │
│ metadata                 JSON                                   │
│ is_active                BOOLEAN DEFAULT true                   │
│ created_at               TIMESTAMP DEFAULT now()                │
│ updated_at               TIMESTAMP DEFAULT now()                │
└─────────────────────────────────────────────────────────────────┘
                              ▲ │
                              │ │ (M:M via job_applications)
                              │ ▼
┌─────────────────────────────────────────────────────────────────┐
│                    JOB_APPLICATIONS                             │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)                  INTEGER                                │
│ user_id (FK)             INTEGER NOT NULL → users.id            │
│ job_id (FK)              INTEGER NOT NULL → jobs.id             │
│ status                   ENUM (pending, in_progress, etc.)      │
│ resume_used              VARCHAR                                │
│ cover_letter_used        TEXT                                   │
│ applied_at               TIMESTAMP                              │
│ error_message            TEXT                                   │
│ automation_log           JSON                                   │
│ created_at               TIMESTAMP DEFAULT now()                │
│ updated_at               TIMESTAMP DEFAULT now()                │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                        SAVED_JOBS                               │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)                  INTEGER                                │
│ user_id (FK)             INTEGER NOT NULL → users.id            │
│ job_id (FK)              INTEGER NOT NULL → jobs.id             │
│ notes                    TEXT                                   │
│ created_at               TIMESTAMP DEFAULT now()                │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                      CRAWLER_JOBS                               │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)                  INTEGER                                │
│ user_id (FK)             INTEGER → users.id                     │
│ search_query             VARCHAR NOT NULL                       │
│ location                 VARCHAR                                │
│ source                   ENUM (linkedin, indeed, etc.)          │
│ status                   VARCHAR (queued, running, etc.)        │
│ jobs_found               INTEGER DEFAULT 0                      │
│ started_at               TIMESTAMP                              │
│ completed_at             TIMESTAMP                              │
│ error_message            TEXT                                   │
│ created_at               TIMESTAMP DEFAULT now()                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Relationships

### Users ↔ User Profiles
- **Type:** One-to-Many
- **Description:** Each user can have multiple profiles (though typically one)
- **Cascade:** Delete user → Delete all profiles

### Users ↔ Job Applications
- **Type:** One-to-Many
- **Description:** Each user can have many job applications
- **Cascade:** Delete user → Delete all applications

### Users ↔ Saved Jobs
- **Type:** One-to-Many
- **Description:** Each user can save many jobs
- **Cascade:** Delete user → Delete all saved jobs

### Jobs ↔ Job Applications
- **Type:** One-to-Many
- **Description:** Each job can have many applications
- **Cascade:** Delete job → Set application job_id to NULL or restrict

### Jobs ↔ Saved Jobs
- **Type:** One-to-Many
- **Description:** Each job can be saved by many users

---

## Indexes

### Users Table
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### Jobs Table
```sql
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_external_id ON jobs(external_id);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
CREATE INDEX idx_jobs_is_active ON jobs(is_active);
CREATE INDEX idx_jobs_remote ON jobs(remote);

-- Composite indexes for common queries
CREATE INDEX idx_jobs_source_active ON jobs(source, is_active);
CREATE INDEX idx_jobs_location_active ON jobs(location, is_active);
```

### Job Applications Table
```sql
CREATE INDEX idx_applications_user_id ON job_applications(user_id);
CREATE INDEX idx_applications_job_id ON job_applications(job_id);
CREATE INDEX idx_applications_status ON job_applications(status);
CREATE INDEX idx_applications_created_at ON job_applications(created_at);

-- Composite index for user's applications by status
CREATE INDEX idx_applications_user_status ON job_applications(user_id, status);
```

### Saved Jobs Table
```sql
CREATE INDEX idx_saved_jobs_user_id ON saved_jobs(user_id);
CREATE INDEX idx_saved_jobs_job_id ON saved_jobs(job_id);

-- Unique constraint to prevent duplicate saves
CREATE UNIQUE INDEX idx_saved_jobs_unique ON saved_jobs(user_id, job_id);
```

---

## Enums

### ApplicationStatus
```python
- PENDING
- IN_PROGRESS
- APPLIED
- FAILED
- REJECTED
- INTERVIEW
- ACCEPTED
```

### JobSource
```python
- LINKEDIN
- INDEED
- GLASSDOOR
- ZIPRECRUITER
- MONSTER
- CUSTOM
```

---

## Sample Queries

### Get all active jobs for a user based on preferences:
```sql
SELECT j.* 
FROM jobs j
LEFT JOIN user_profiles up ON up.user_id = :user_id
WHERE j.is_active = true
  AND (j.remote = true OR j.location LIKE '%' || up.location || '%')
  AND j.salary_min >= (up.job_preferences->>'salary_min')::int
ORDER BY j.created_at DESC
LIMIT 50;
```

### Get application statistics for a user:
```sql
SELECT 
    status,
    COUNT(*) as count
FROM job_applications
WHERE user_id = :user_id
GROUP BY status;
```

### Find jobs not yet applied to by user:
```sql
SELECT j.*
FROM jobs j
WHERE j.is_active = true
  AND j.id NOT IN (
    SELECT job_id 
    FROM job_applications 
    WHERE user_id = :user_id
  )
ORDER BY j.created_at DESC
LIMIT 50;
```

---

## Data Volume Estimates

### Storage Projections (1,000 active users)

| Table | Records | Avg Size | Total Size |
|-------|---------|----------|------------|
| users | 1,000 | 500 bytes | 500 KB |
| user_profiles | 1,000 | 2 KB | 2 MB |
| jobs | 100,000 | 5 KB | 500 MB |
| job_applications | 50,000 | 1 KB | 50 MB |
| saved_jobs | 10,000 | 200 bytes | 2 MB |
| crawler_jobs | 5,000 | 500 bytes | 2.5 MB |
| **Total** | | | **~560 MB** |

### Storage Projections (10,000 active users)

| Table | Records | Total Size |
|-------|---------|------------|
| users | 10,000 | 5 MB |
| user_profiles | 10,000 | 20 MB |
| jobs | 1,000,000 | 5 GB |
| job_applications | 500,000 | 500 MB |
| saved_jobs | 100,000 | 20 MB |
| crawler_jobs | 50,000 | 25 MB |
| **Total** | | **~5.6 GB** |

---

## Partitioning Strategy (for scale)

### Jobs Table Partitioning (by date)
```sql
-- Partition by month
CREATE TABLE jobs_2024_01 PARTITION OF jobs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE jobs_2024_02 PARTITION OF jobs
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

### Benefits:
- Faster queries on recent jobs
- Easy archival of old data
- Improved vacuum performance

---

## Backup Strategy

1. **Daily backups** of entire database
2. **Point-in-time recovery** enabled
3. **Replicas** for read scaling
4. **Retention:** 30 days

```bash
# Backup command
pg_dump -U jobautomation jobautomation > backup_$(date +%Y%m%d).sql

# Restore command
psql -U jobautomation jobautomation < backup_20240101.sql
```

---

## Performance Optimization Tips

1. **Use connection pooling** (PgBouncer)
2. **Enable query result caching** in Redis
3. **Regular VACUUM and ANALYZE**
4. **Monitor slow queries** (pg_stat_statements)
5. **Use materialized views** for complex analytics

```sql
-- Example materialized view for user stats
CREATE MATERIALIZED VIEW user_application_stats AS
SELECT 
    user_id,
    COUNT(*) as total_applications,
    COUNT(CASE WHEN status = 'APPLIED' THEN 1 END) as applied_count,
    COUNT(CASE WHEN status = 'INTERVIEW' THEN 1 END) as interview_count
FROM job_applications
GROUP BY user_id;

-- Refresh periodically
REFRESH MATERIALIZED VIEW user_application_stats;
```

---

This schema is designed for:
✅ Scalability (millions of records)
✅ Performance (proper indexes)
✅ Data integrity (foreign keys, constraints)
✅ Flexibility (JSON fields for metadata)
