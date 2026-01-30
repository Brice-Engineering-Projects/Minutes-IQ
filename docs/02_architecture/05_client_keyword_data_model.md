# Client & Keyword Data Model

This document describes the data model for clients (government agencies) and keywords used for filtering meeting minutes.

## Overview

The Client & Keyword Management system consists of five main tables:
1. **clients** - Government agencies being tracked
2. **keywords** - Search terms for filtering meetings
3. **client_keywords** - Many-to-many relationship between clients and keywords
4. **user_client_favorites** - User favorites (many-to-many)
5. **client_sources** - Data sources for client information

---

## Entity Relationship Diagram

```
┌─────────────────┐
│     users       │
│─────────────────│
│ user_id (PK)    │
│ username        │
│ email           │
│ role_id (FK)    │
└────────┬────────┘
         │
         │ created_by
         │
    ┌────┴──────────────────┬──────────────────────┐
    │                       │                      │
    │                       │                      │
┌───▼────────────┐   ┌──────▼──────────┐   ┌──────▼──────────────┐
│   clients      │   │    keywords     │   │user_client_favorites│
│────────────────│   │─────────────────│   │─────────────────────│
│ client_id (PK) │   │ keyword_id (PK) │   │ user_id (FK)        │
│ name           │   │ keyword         │   │ client_id (FK)      │
│ description    │   │ category        │   │ favorited_at        │
│ website_url    │   │ description     │   └─────────────────────┘
│ is_active      │   │ is_active       │
│ created_at     │   │ created_at      │
│ created_by (FK)│   │ created_by (FK) │
│ updated_at     │   └────────┬────────┘
└────────┬───────┘            │
         │                    │
         └────────┬───────────┘
                  │
         ┌────────▼────────────┐
         │  client_keywords    │
         │─────────────────────│
         │ client_id (FK)      │
         │ keyword_id (FK)     │
         │ added_at            │
         │ added_by (FK)       │
         └─────────────────────┘

┌──────────────────┐
│  client_sources  │
│──────────────────│
│ source_id (PK)   │
│ client_id (FK)   │
│ source_type      │
│ source_url       │
│ last_scraped_at  │
│ is_active        │
└──────────────────┘
```

---

## Table: clients

Represents government agencies or organizations being tracked.

### Schema

```sql
CREATE TABLE IF NOT EXISTS clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    website_url TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    updated_at INTEGER,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_is_active ON clients(is_active);
CREATE INDEX idx_clients_created_by ON clients(created_by);
```

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| client_id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| name | TEXT | NOT NULL, UNIQUE | Client organization name (e.g., "JEA") |
| description | TEXT | NULLABLE | Optional description of the client |
| website_url | TEXT | NULLABLE | Official website URL |
| is_active | INTEGER | NOT NULL, DEFAULT 1 | Soft delete flag (1=active, 0=inactive) |
| created_at | INTEGER | NOT NULL | Unix timestamp of creation |
| created_by | INTEGER | NOT NULL, FOREIGN KEY | User ID of admin who created this |
| updated_at | INTEGER | NULLABLE | Unix timestamp of last update |

### Business Rules

1. **Name Uniqueness**: Client names must be unique (case-sensitive)
2. **Soft Delete**: Deletion sets `is_active=0` rather than removing the record
3. **Audit Trail**: `created_by` tracks who added the client
4. **URL Validation**: If provided, `website_url` must start with http:// or https://
5. **Name Length**: Must be 3-200 characters
6. **Description Length**: Max 1000 characters
7. **URL Length**: Max 500 characters

### Example Records

```sql
INSERT INTO clients VALUES
    (1, 'JEA', 'Jacksonville Electric Authority', 'https://www.jea.com', 1, 1706198400, 1, NULL),
    (2, 'City of Jacksonville', 'Municipal government', 'https://www.coj.net', 1, 1706198400, 1, NULL),
    (3, 'Duval County Schools', 'Public school district', 'https://dcps.duvalschools.org', 1, 1706198400, 1, NULL);
```

---

## Table: keywords

Search terms used to filter meeting minutes and identify relevant discussions.

### Schema

```sql
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    category TEXT,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE INDEX idx_keywords_keyword ON keywords(keyword);
CREATE INDEX idx_keywords_category ON keywords(category);
CREATE INDEX idx_keywords_is_active ON keywords(is_active);
```

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| keyword_id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| keyword | TEXT | NOT NULL, UNIQUE | The search term/phrase |
| category | TEXT | NULLABLE | Optional grouping (e.g., "Finance", "Infrastructure") |
| description | TEXT | NULLABLE | Explanation of keyword usage |
| is_active | INTEGER | NOT NULL, DEFAULT 1 | Soft delete flag |
| created_at | INTEGER | NOT NULL | Unix timestamp of creation |
| created_by | INTEGER | NOT NULL, FOREIGN KEY | User ID of admin who created this |

### Business Rules

1. **Keyword Uniqueness**: Keywords must be unique (case-sensitive)
2. **Soft Delete**: Deletion sets `is_active=0`
3. **Keyword Length**: Must be 2-100 characters
4. **Category Length**: Max 50 characters (optional)
5. **Description Length**: Max 500 characters (optional)
6. **Search Optimization**: Keywords are indexed for fast search operations

### Category Guidelines

Suggested categories for organizing keywords:

- **Finance**: budget, revenue, rates, bonds, taxes
- **Infrastructure**: roads, bridges, construction, maintenance
- **Utilities**: water, electricity, wastewater, stormwater
- **Public Works**: parks, facilities, sanitation
- **Planning**: zoning, development, permits
- **Transportation**: transit, traffic, parking
- **Public Safety**: police, fire, emergency services
- **Environment**: sustainability, conservation, pollution

### Example Records

```sql
INSERT INTO keywords VALUES
    (1, 'water', 'Utilities', 'Water service and infrastructure', 1, 1706198400, 1),
    (2, 'budget', 'Finance', 'Budget discussions and planning', 1, 1706198400, 1),
    (3, 'infrastructure', 'Public Works', 'Infrastructure projects', 1, 1706198400, 1),
    (4, 'rates', 'Finance', 'Service rates and pricing', 1, 1706198400, 1);
```

---

## Table: client_keywords

Junction table for many-to-many relationship between clients and keywords.

### Schema

```sql
CREATE TABLE IF NOT EXISTS client_keywords (
    client_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    added_at INTEGER NOT NULL,
    added_by INTEGER NOT NULL,
    PRIMARY KEY (client_id, keyword_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES users(user_id)
);

CREATE INDEX idx_client_keywords_client ON client_keywords(client_id);
CREATE INDEX idx_client_keywords_keyword ON client_keywords(keyword_id);
```

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| client_id | INTEGER | PRIMARY KEY (composite), FOREIGN KEY | Reference to client |
| keyword_id | INTEGER | PRIMARY KEY (composite), FOREIGN KEY | Reference to keyword |
| added_at | INTEGER | NOT NULL | Unix timestamp when association was created |
| added_by | INTEGER | NOT NULL, FOREIGN KEY | User ID of admin who created association |

### Business Rules

1. **Unique Pairs**: A client-keyword pair can only exist once
2. **Cascade Delete**: If client or keyword is deleted, associations are removed
3. **Active Check**: Service layer prevents associating inactive clients/keywords
4. **Audit Trail**: Tracks who created each association

### Example Records

```sql
-- JEA associated with water, rates, and infrastructure
INSERT INTO client_keywords VALUES
    (1, 1, 1706198400, 1),  -- JEA + water
    (1, 4, 1706198400, 1),  -- JEA + rates
    (1, 3, 1706198400, 1);  -- JEA + infrastructure

-- City of Jacksonville associated with budget and infrastructure
INSERT INTO client_keywords VALUES
    (2, 2, 1706198400, 1),  -- City + budget
    (2, 3, 1706198400, 1);  -- City + infrastructure
```

### Queries

**Get all keywords for a client:**
```sql
SELECT k.*
FROM keywords k
INNER JOIN client_keywords ck ON k.keyword_id = ck.keyword_id
WHERE ck.client_id = 1
ORDER BY k.keyword ASC;
```

**Get all clients using a keyword:**
```sql
SELECT c.*
FROM clients c
INNER JOIN client_keywords ck ON c.client_id = ck.client_id
WHERE ck.keyword_id = 3
ORDER BY c.name ASC;
```

---

## Table: user_client_favorites

Junction table for user's favorite clients.

### Schema

```sql
CREATE TABLE IF NOT EXISTS user_client_favorites (
    user_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    favorited_at INTEGER NOT NULL,
    PRIMARY KEY (user_id, client_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

CREATE INDEX idx_favorites_user ON user_client_favorites(user_id);
CREATE INDEX idx_favorites_client ON user_client_favorites(client_id);
CREATE INDEX idx_favorites_time ON user_client_favorites(favorited_at);
```

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| user_id | INTEGER | PRIMARY KEY (composite), FOREIGN KEY | Reference to user |
| client_id | INTEGER | PRIMARY KEY (composite), FOREIGN KEY | Reference to client |
| favorited_at | INTEGER | NOT NULL | Unix timestamp when favorited |

### Business Rules

1. **Unique Pairs**: A user can only favorite a client once
2. **Cascade Delete**: If user or client is deleted, favorites are removed
3. **Active Only**: Service layer only allows favoriting active clients
4. **Isolation**: Each user's favorites are completely isolated
5. **Ordering**: Favorites list is ordered by `favorited_at DESC` (most recent first)

### Example Records

```sql
-- User 2 favorites JEA and City of Jacksonville
INSERT INTO user_client_favorites VALUES
    (2, 1, 1706198400),  -- User 2 + JEA
    (2, 2, 1706284800);  -- User 2 + City

-- User 3 favorites only JEA
INSERT INTO user_client_favorites VALUES
    (3, 1, 1706371200);  -- User 3 + JEA
```

### Queries

**Get user's favorites:**
```sql
SELECT c.*, f.favorited_at
FROM clients c
INNER JOIN user_client_favorites f ON c.client_id = f.client_id
WHERE f.user_id = 2
ORDER BY f.favorited_at DESC;
```

**Check if client is favorited:**
```sql
SELECT 1
FROM user_client_favorites
WHERE user_id = 2 AND client_id = 1;
```

**Count favorites for a client:**
```sql
SELECT COUNT(*)
FROM user_client_favorites
WHERE client_id = 1;
```

---

## Table: client_sources

Tracks data sources for scraping client information.

### Schema

```sql
CREATE TABLE IF NOT EXISTS client_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    last_scraped_at INTEGER,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

CREATE INDEX idx_sources_client ON client_sources(client_id);
CREATE INDEX idx_sources_type ON client_sources(source_type);
CREATE INDEX idx_sources_active ON client_sources(is_active);
```

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| source_id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| client_id | INTEGER | NOT NULL, FOREIGN KEY | Reference to client |
| source_type | TEXT | NOT NULL | Type of source (e.g., "agenda_page", "minutes_page") |
| source_url | TEXT | NOT NULL | URL to scrape |
| last_scraped_at | INTEGER | NULLABLE | Unix timestamp of last successful scrape |
| is_active | INTEGER | NOT NULL, DEFAULT 1 | Whether source should be scraped |

### Business Rules

1. **Multiple Sources**: A client can have multiple sources
2. **Source Types**: Standardized types for different data sources
3. **Cascade Delete**: If client is deleted, all sources are removed
4. **Active Flag**: Inactive sources are skipped during scraping

### Source Types

- `agenda_page`: Meeting agenda listing page
- `minutes_page`: Meeting minutes listing page
- `calendar_feed`: Calendar API or feed
- `document_repository`: Document storage system
- `rss_feed`: RSS feed of meetings/documents

### Example Records

```sql
INSERT INTO client_sources VALUES
    (1, 1, 'agenda_page', 'https://www.jea.com/meetings/agendas', NULL, 1),
    (2, 1, 'minutes_page', 'https://www.jea.com/meetings/minutes', NULL, 1),
    (3, 2, 'calendar_feed', 'https://www.coj.net/calendar/feed', NULL, 1);
```

---

## Data Access Patterns

### Repository Pattern

Each entity has a dedicated repository class:

- `ClientRepository` - CRUD operations for clients
- `KeywordRepository` - CRUD for keywords + client-keyword associations
- `FavoritesRepository` - User favorites management

### Service Layer

Business logic is handled in service classes:

- `ClientService` - Client management with validation
- `KeywordService` - Keyword management, search, suggestions

### Key Operations

**Creating a Client with Keywords:**
```python
# 1. Create client
client = client_service.create_client(
    name="JEA",
    created_by=admin_id,
    description="Jacksonville Electric Authority"
)

# 2. Create keywords
water_kw = keyword_service.create_keyword(
    keyword="water",
    created_by=admin_id,
    category="Utilities"
)

# 3. Associate keyword with client
client_service.add_keyword_to_client(
    client_id=client["client_id"],
    keyword_id=water_kw["keyword_id"],
    added_by=admin_id
)
```

**User Browsing Clients:**
```python
# Get all active clients with favorite status
clients, total = client_service.list_clients(
    is_active=True,
    include_keywords=True
)

# Check favorite status (done in service layer)
for client in clients:
    client["is_favorited"] = favorites_repo.is_favorite(
        user_id=current_user_id,
        client_id=client["client_id"]
    )
```

---

## Migration History

### Phase 5: Initial Client & Keyword Management
**File:** `20260125_170000_add_client_keyword_management.sql`

Created all five tables with proper foreign key constraints and indexes.

---

## Performance Considerations

### Indexes

All tables have appropriate indexes for common query patterns:
- Name/keyword lookups
- Category filtering
- Active status filtering
- Foreign key relationships

### Query Optimization

1. **Pagination**: Use LIMIT/OFFSET for large result sets
2. **Filtering**: Apply WHERE clauses early in query execution
3. **Joins**: Use INNER JOIN for required relationships
4. **Soft Deletes**: Always filter by `is_active` where applicable

### Scaling Considerations

Current design supports:
- Hundreds of clients
- Thousands of keywords
- Millions of favorites
- Fast autocomplete search

For larger scale:
- Consider full-text search indexes
- Add caching layer (Redis)
- Implement pagination cursor-based system

---

## Security Considerations

### Access Control

1. **Admin Only Operations:**
   - Create/Update/Delete clients
   - Create/Update/Delete keywords
   - Manage client-keyword associations

2. **User Operations:**
   - View active clients only
   - Manage own favorites only
   - Cannot see other users' favorites

### Data Validation

All inputs are validated at multiple layers:
1. **Pydantic Models**: Request/response validation
2. **Service Layer**: Business logic validation
3. **Repository Layer**: Database constraints

### Audit Trail

All mutations track:
- `created_by`: Who created the record
- `added_by`: Who created associations
- `created_at`/`updated_at`: When changes occurred

---

## Future Enhancements

### Planned Features

1. **Client Sources**: Fully implement scraper integration
2. **Keyword Synonyms**: Map similar terms to primary keywords
3. **Keyword Weights**: Prioritize certain keywords in search
4. **Client Categories**: Group clients by type (utility, municipality, etc.)
5. **Activity Tracking**: Log when clients/keywords are used in searches

### Schema Changes

No breaking changes planned. Future additions will be backward-compatible.
