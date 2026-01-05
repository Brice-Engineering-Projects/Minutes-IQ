# 🔒 Indexing & Foreign Key Cascade Rules (v1)

This document defines **intentional database behavior** for indexing and referential integrity.
It is authoritative for **Schema v1** and complements the core schema documentation.

---

## 1. Indexing Strategy

### Guiding Principles

- Primary keys and UNIQUE constraints automatically create indexes
- Additional indexes are added **only when justified by access patterns**
- Premature indexing is avoided in v1
- Index decisions are documented before implementation

---

### 1.1 Automatically Indexed (Implicit)

The following are indexed by default due to PRIMARY KEY or UNIQUE constraints:

- All `*_id` primary keys
- Composite primary keys:
  - `user_client_favorites (user_id, client_id)`
  - `role_permission (role_id, permission_id)`
  - `saved_search_keywords (saved_search_id, keyword_id)`
  - `saved_search_sources (saved_search_id, source_id)`
- Declared UNIQUE constraints:
  - `User.username`
  - `User.email`
  - `Client.name`
  - `Keywords.keyword`
  - `Auth_credentials (provider_id, user_id)`
  - `Client_sources (client_id, source_key)`
  - `Saved_searches (user_id, client_id, name)`

No additional indexes are required for correctness.

---

### 1.2 Candidate Indexes (Deferred)

The following indexes are **intentionally deferred** until usage patterns justify them:

| Table | Column(s) | Rationale |
|------|-----------|-----------|
| `Saved_searches` | `user_id` | Frequent user-scoped reads |
| `Client_sources` | `(client_id, is_active)` | Active source filtering |
| `Auth_credentials` | `user_id` | User lookup during authentication |
| `Saved_searches` | `client_id` | Client-scoped searches |

These indexes should be added **only if query volume or latency warrants it**.

---

## 2. Foreign Key Cascade Rules

### Guiding Principles

- **RESTRICT is the default**
- The database must never silently delete related data
- Destructive actions must be **explicit and intentional**
- Cleanup logic belongs in application or admin workflows

This approach prioritizes:
- Safety
- Auditability
- Predictability

---

### 2.1 Cascade Rule Summary (v1)

All foreign keys use the following rules unless explicitly revised in a future version:

```sql
ON DELETE RESTRICT
ON UPDATE RESTRICT
```

---

### 2.2 Rationale for RESTRICT

Using `RESTRICT` ensures:

- No accidental data loss
- Orphaned records cannot exist
- Deletions fail loudly instead of cascading silently
- Engineers must reason about impact before destructive actions

This is **intentional friction**.

---

### 2.3 Table-by-Table Implications

#### User Deletion

Deleting a `User` will fail if dependent records exist in:
- `Profile`
- `Auth_credentials`
- `Saved_searches`
- `User_client_favorites`

**Recommended action:**  
Use soft-deactivation (`is_active = false`) or explicitly clean dependent records.

---

#### Client Deletion

Deleting a `Client` will fail if referenced by:
- `Client_sources`
- `Saved_searches`
- `User_client_favorites`

This prevents accidental removal of active scraping targets.

---

#### Keyword Deletion

Deleting a `Keyword` will fail if referenced by:
- `Saved_search_keywords`

**Recommended action:**  
Deactivate keywords using `is_active = false`.

---

#### Role & Permission Deletion

Deleting a `Role` or `Permission` will fail if referenced by:
- `Role_permission`
- `User` (via `role_id`)

This prevents corruption of the authorization model.

---

## 3. Future Considerations (Not v1)

The following changes may be considered in later versions:

- Selective `CASCADE` rules for non-critical child tables
- Soft-delete patterns replacing physical deletes
- Read-optimized indexes based on real query telemetry
- Partial indexes on `is_active = true`

None of these are required for v1.

---

## 4. Design Status

- **Indexing:** Conservative, correctness-first
- **FK behavior:** Explicit, restrictive, safe
- **Schema stability:** High
- **Operational risk:** Low

This document is **authoritative for v1** and should be revisited only when:
- Table sizes grow materially
- Query latency becomes measurable
- Admin workflows mature
