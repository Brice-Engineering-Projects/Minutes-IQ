# 📚 Database Schema Documentation (v1.1 – Field-Complete, Tabular)

## Global Conventions

- All `*_id` primary key fields:
  - Are **UNIQUE**
  - Are **auto-incrementing integers**
  - Carry **no business meaning**
- Foreign keys define ownership or authority
- `is_active` indicates soft-enable / disable
- Timestamps are database-native
- **Every field below has an explicit semantic purpose**

---

## 1. `users`

**Purpose:** System identity  
**Answers:** *Who is this user?*

| Field | Key | Description |
|-----|----|------------|
| `user_id` | PK | Immutable system identifier for the user |
| `username` | UNIQUE | Human-readable login identifier |
| `email` | UNIQUE | Contact address and password-reset target |
| `phone` | — | Optional contact metadata |
| `role_id` | FK → `role.role_id` | **Authorization role** determining allowed actions |
| `provider_id` | FK → `auth_provider.provider_id` | Optional pointer to the user’s **primary auth provider** (convenience only) |

---

## 2. `profile`

**Purpose:** Human-facing metadata  
**Answers:** *How should this user be displayed?*

| Field | Key | Description |
|-----|----|------------|
| `profile_id` | PK | Profile record identifier |
| `user_id` | FK → `users.user_id` | Owning user (1-to-1) |
| `first_name` | — | Display first name |
| `last_name` | — | Display last name |
| `title` | — | Optional descriptive title |

---

## 3. `auth_credentials`

**Purpose:** Authentication secrets  
**Answers:** *How does this provider authenticate the user?*

| Field | Key | Description |
|-----|----|------------|
| `auth_id` | PK | Credential record identifier |
| `provider_id` | FK → `auth_provider.provider_id` | Authentication provider |
| `user_id` | FK → `users.user_id` | User being authenticated |
| `hashed_password` | — | Secure password hash |
| `is_active` | — | Enables or disables the credential |
| `created_at` | — | Credential creation timestamp |

---

## 4. `client`

| Field | Key | Description |
|-----|----|------------|
| `client_id` | PK | Client identifier |
| `name` | UNIQUE | Client name |
| `is_active` | — | Whether client is enabled |
| `created_at` | — | Creation timestamp |

---

## 5. `auth_provider`

**Purpose:** Authentication methods

| Field | Key | Description |
|-----|----|------------|
| `provider_id` | PK | Auth provider record identifier |
| `user_id` | FK → `users.user_id` | Owning user |
| `provider_type` | — | Provider type (`local`, `google`, etc.) |

---

## 6. `user_client_favorites`

| Field | Key | Description |
|-----|----|------------|
| `user_id` | FK → `users.user_id` | User |
| `client_id` | FK → `client.client_id` | Favorited client |

---

## 7. `client_sources`

| Field | Key | Description |
|-----|----|------------|
| `source_id` | PK | Source identifier |
| `client_id` | FK → `client.client_id` | Owning client |
| `source_key` | UNIQUE (per client) | Internal source identifier |
| `source_name` | — | Display name |
| `base_url` | — | Root URL |
| `index_url` | — | Listing/index URL |
| `archive_url` | — | Historical archive URL |
| `source_type` | — | Content type |
| `parser_type` | — | Parser strategy |
| `is_active` | — | Enabled/disabled |
| `created_at` | — | Creation timestamp |

---

## 8. `permission`

| Field           | Key    | Description                                                       |
| --------------- | ------ | ----------------------------------------------------------------- |
| `permission_id` | PK     | Internal numeric identifier for the permission                    |
| `name`          | UNIQUE | **Code-level permission identifier** used in authorization checks |
| `description`   | —      | Human-readable explanation of what the permission allows          |


---

## 9. `role`

| Field | Key | Description |
|-----|----|------------|
| `role_id` | PK | Role identifier |
| `name` | UNIQUE | Role name |
| `description` | — | Role intent |

---

## 10. `role_permission`

| Field | Key | Description |
|-----|----|------------|
| `role_id` | FK → `role.role_id` | Role |
| `permission_id` | FK → `permission.permission_id` | Permission |

---

## 11. `saved_searches`

| Field | Key | Description |
|-----|----|------------|
| `saved_search_id` | PK | Saved search identifier |
| `user_id` | FK → `users.user_id` | Owner |
| `client_id` | FK → `client.client_id` | Target client |
| `name` | — | Search name |
| `description` | — | Search description |
| `created_at` | — | Creation timestamp |
| `updated_at` | — | Last update timestamp |

---

## 12. `saved_search_sources`

| Field | Key | Description |
|-----|----|------------|
| `saved_search_id` | FK → `saved_searches.saved_search_id` | Saved search |
| `source_id` | FK → `client_sources.source_id` | Included source |

---

## 13. `keywords`

| Field | Key | Description |
|-----|----|------------|
| `keyword_id` | PK | Keyword identifier |
| `keyword` | UNIQUE | Keyword text |
| `description` | — | Context |
| `is_active` | — | Enabled/disabled |
| `created_at` | — | Creation timestamp |
| `updated_at` | — | Last update timestamp |

---

## 14. `saved_search_keywords`

| Field | Key | Description |
|-----|----|------------|
| `saved_search_id` | FK → `saved_searches.saved_search_id` | Saved search |
| `keyword_id` | FK → `keywords.keyword_id` | Keyword |

---

## Schema Status

- **Version:** v1.1  
- **Design:** Locked  
- **Documentation:** Complete, tabular, semantic  
- **Ready for:** Implementation, RBAC enforcement
