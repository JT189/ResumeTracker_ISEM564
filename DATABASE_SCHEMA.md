# Database schema and ER diagram

The application uses SQLite via SQLAlchemy. The default database file is `backend/jobs.db`.

This document describes the current schema at a conceptual level so the team can reason about data ownership, relationships, and analytics.

## ER diagram

```mermaid
erDiagram
  USERS ||--o{ JOBS : owns
  USERS ||--o{ RESUMES : owns
  USERS ||--o{ RSS_SOURCES : owns
  USERS ||--o{ RANKING_RULES : owns
  USERS ||--o{ AI_CONNECTIONS : owns
  USERS ||--o{ JOB_WEIGHT_PROMPTS : owns
  USERS ||--o{ TELEMETRY_EVENTS : owns
  USERS ||--o{ PASSWORD_RESET_TOKENS : owns

  RESUMES ||--o{ JOBS : used_for_scoring

  USERS {
    int id PK
    string email UNIQUE
    string hashed_password
    string full_name
    bool analytics_ai_enabled
    datetime created_at
  }

  RSS_SOURCES {
    int id PK
    int user_id FK
    string name
    string url
    bool is_enabled
    datetime created_at
  }

  JOBS {
    int id PK
    int user_id FK
    int resume_id FK
    string title
    string company
    string location
    string description
    string url
    string status
    float rank_score
    bool is_tracked
    string source_url
    datetime date_added
    datetime updated_at
  }

  RESUMES {
    int id PK
    int user_id FK
    string file_name
    string file_hash UNIQUE_PER_USER
    string file_path
    string content_type
    datetime created_at
  }

  RANKING_RULES {
    int id PK
    int user_id FK
    string name
    string logic
    int weight
    bool is_active
    datetime created_at
  }

  AI_CONNECTIONS {
    int id PK
    int user_id FK
    string provider
    string model
    string base_url
    string encrypted_api_key
    bool is_default
    datetime created_at
    datetime updated_at
  }

  JOB_WEIGHT_PROMPTS {
    int id PK
    int user_id FK
    string prompt
    bool is_enabled
    datetime created_at
  }

  TELEMETRY_EVENTS {
    int id PK
    int user_id FK
    string event_type
    string meta_json
    datetime created_at
  }

  PASSWORD_RESET_TOKENS {
    int id PK
    int user_id FK
    string token_hash
    datetime expires_at
    datetime created_at
  }
```

## Notes and conventions

### Multi tenant ownership

All tables that store user data include a `user_id` foreign key. API endpoints are scoped to the authenticated user.

### Resume and scoring linkage

`jobs.resume_id` records which resume was used when the role was scored. This supports later audit and analytics.

### AI connections and encryption

AI provider API keys are stored in the database encrypted. The backend decrypts keys only when needed for scoring and reporting.

### Telemetry

Telemetry is stored as append only events. Aggregations for analytics are computed by querying `telemetry_events` by type and time window.

