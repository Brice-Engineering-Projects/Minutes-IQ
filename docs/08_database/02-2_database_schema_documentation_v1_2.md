# 📚 Database Schema Documentation (v1.2 – Operational, Unambiguous)

## Global Conventions

- All `*_id` primary keys:
  - Are auto-incrementing integers
  - Are opaque identifiers with no embedded business meaning
- Foreign keys define ownership or authority
- Fields referenced directly in application code are explicitly described as such
- If changing a field requires code changes, this is stated explicitly

---

## 1. `users`

**Purpose:** Canonical system identity record  
**Used by:** Authentication, authorization, ownership checks

| Field | Key | Description |
|-----|----|------------|
| `user_id` | PK | Primary identifier for the user. Referenced by all user-related tables. Never changes. |
| `username` | UNIQUE | Login identifier entered by the user. Changing this affects login behavior. |
| `email` | UNIQUE | Contact and password-reset address. Safe to change; does not affect authorization. |
| `phone` | — | Optional contact metadata. Not referenced by auth or authorization logic. |
| `role_id` | FK → `role.role_id` | Authoritative authorization role. Referenced by backend authorization checks. Changing this immediately changes user privileges. |
| `provider_id` | FK → `auth_provider.provider_id` | Optional pointer to the user’s primary authentication provider. Convenience only; not authoritative. |

---

## 2. `profile`

**Purpose:** Display-only user metadata

| Field | Key | Description |
|-----|----|------------|
| `profile_id` | PK | Identifier for the profile record. |
| `user_id` | FK → `users.user_id` | Owner of this profile. Enforces one profile per user. |
| `first_name` | — | Display value only. Safe to change. |
| `last_name` | — | Display value only. Safe to change. |
| `title` | — | Optional display label. Not used in logic. |

---

## 3. `auth_credentials`

**Purpose:** Stores secrets used to authenticate a user

| Field | Key | Description |
|-----|----|------------|
| `auth_id` | PK | Identifier for the credential record. |
| `provider_id` | FK → `auth_provider.provider_id` | Authentication method this credential belongs to. |
| `user_id` | FK → `users.user_id` | User authenticated by this credential. |
| `hashed_password` | — | bcrypt hash of the password. Compared directly during login. |
| `is_active` | — | If false, login using this credential is denied. |
| `created_at` | — | Timestamp when the credential was created. Audit only. |

---

## 4. `client`

**Purpose:** External organizations being tracked

| Field | Key | Description |
|-----|----|------------|
| `client_id` | PK | Identifier for the client. |
| `name` | UNIQUE | Human-readable client name. |
| `is_active` | — | Controls whether the client is selectable or processed. |
| `created_at` | — | Audit timestamp. |

---

## 5. `auth_provider`

**Purpose:** Declares which authentication methods a user can use

| Field | Key | Description |
|-----|----|------------|
| `provider_id` | PK | Identifier for the provider record. |
| `user_id` | FK → `users.user_id` | Owner of this provider. |
| `provider_type` | — | Authentication mechanism name (e.g. `local`). Referenced by login routing logic. |

---

## 6. `user_client_favorites`

**Purpose:** Stores user-specific preferences

| Field | Key | Description |
|-----|----|------------|
| `user_id` | FK → `users.user_id` | User who favorited the client. |
| `client_id` | FK → `client.client_id` | Favorited client. |

---

## 7. `client_sources`

**Purpose:** Defines scrape targets for a client

| Field | Key | Description |
|-----|----|------------|
| `source_id` | PK | Identifier for the source. |
| `client_id` | FK → `client.client_id` | Client that owns this source. |
| `source_key` | UNIQUE (per client) | Code-referenced identifier used to select parsing logic. |
| `source_name` | — | Display name. |
| `base_url` | — | Root URL. |
| `index_url` | — | URL used to discover documents. |
| `archive_url` | — | URL for historical documents. |
| `source_type` | — | Content type used by parser selection logic. |
| `parser_type` | — | Name of parser implementation. |
| `is_active` | — | If false, source is skipped during scraping. |
| `created_at` | — | Audit timestamp. |

---

## 8. `permission`

**Purpose:** Defines individual actions that can be allowed

| Field | Key | Description |
|-----|----|------------|
| `permission_id` | PK | Internal identifier. |
| `name` | UNIQUE | Exact string used in authorization checks in code. Changing this requires code changes. |
| `description` | — | Human-readable explanation. Safe to change. |

---

## 9. `role`

**Purpose:** Groups permissions into access tiers

| Field | Key | Description |
|-----|----|------------|
| `role_id` | PK | Identifier for the role. |
| `name` | UNIQUE | Role label referenced by seed scripts and admin tooling. |
| `description` | — | Explanation of what the role represents. |

---

## 10. `role_permission`

**Purpose:** Assigns permissions to roles

| Field | Key | Description |
|-----|----|------------|
| `role_id` | FK → `role.role_id` | Role receiving the permission. |
| `permission_id` | FK → `permission.permission_id` | Permission granted to the role. |

---

## 11. `saved_searches`

**Purpose:** Stores user-defined search configurations

| Field | Key | Description |
|-----|----|------------|
| `saved_search_id` | PK | Identifier for the saved search. |
| `user_id` | FK → `users.user_id` | Owner of the search. |
| `client_id` | FK → `client.client_id` | Client the search targets. |
| `name` | — | User-defined name. |
| `description` | — | Optional description. |
| `created_at` | — | Creation timestamp. |
| `updated_at` | — | Last modification timestamp. |

---

## 12. `saved_search_sources`

**Purpose:** Restricts a search to specific sources

| Field | Key | Description |
|-----|----|------------|
| `saved_search_id` | FK → `saved_searches.saved_search_id` | Saved search. |
| `source_id` | FK → `client_sources.source_id` | Included source. |

---

## 13. `keywords`

**Purpose:** Defines searchable terms

| Field | Key | Description |
|-----|----|------------|
| `keyword_id` | PK | Identifier for the keyword. |
| `keyword` | UNIQUE | Literal search term used directly in search logic. |
| `description` | — | Context or clarification. |
| `is_active` | — | If false, keyword is ignored. |
| `created_at` | — | Creation timestamp. |
| `updated_at` | — | Last update timestamp. |

---

## 14. `saved_search_keywords`

**Purpose:** Associates keywords with saved searches

| Field | Key | Description |
|-----|----|------------|
| `saved_search_id` | FK → `saved_searches.saved_search_id` | Saved search. |
| `keyword_id` | FK → `keywords.keyword_id` | Included keyword. |

---

## Schema Status

- **Version:** v1.2
- **Design:** Locked
- **Documentation Standard:** Operational & unambiguous
- **Ready for:** Implementation, review, and handoff
