# 📚 Database Schema Documentation (v1)

## Global Conventions

- All `*_id` primary key fields:
  - Are **UNIQUE**
  - Are **auto-incrementing integers**
- Composite primary keys are explicitly noted
- Foreign keys reference the listed parent table
- Timestamps use database-native datetime types
- Soft state is represented via `is_active` where present

---

## 1. User

**Purpose:**  
Represents a system user identity.

**Role in the system:**  
Acts as the primary identity anchor for authentication, authorization, profiles, and saved workflows.

### Fields
- `user_id (PK)`
- `username`
- `email`
- `phone`
- `role_id (FK → Role.role_id)`
- `provider_id (FK → Auth_provider.provider_id)`

### UNIQUE constraints
- `user_id`
- `username`
- `email`

### Auto-increment
- `user_id`

---

## 2. Profile

**Purpose:**  
Stores human-facing user metadata.

### Fields
- `profile_id (PK)`
- `user_id (FK → User.user_id)`
- `first_name`
- `last_name`
- `title`

### UNIQUE constraints
- `profile_id`
- `user_id`

### Auto-increment
- `profile_id`

---

## 3. Auth_credentials

**Purpose:**  
Stores authentication secrets for a user-provider pairing.

### Fields
- `auth_id (PK)`
- `provider_id (FK → Auth_provider.provider_id)`
- `user_id (FK → User.user_id)`
- `hashed_password`
- `is_active`
- `created_at`

### UNIQUE constraints
- `auth_id`
- `(provider_id, user_id)`

### Auto-increment
- `auth_id`

---

## 4. Client

### Fields
- `client_id (PK)`
- `name`
- `is_active`
- `created_at`

### UNIQUE constraints
- `client_id`
- `name`

### Auto-increment
- `client_id`

---

## 5. Auth_provider

### Fields
- `provider_id (PK)`
- `user_id (FK → User.user_id)`
- `provider_type`

### UNIQUE constraints
- `provider_id`
- `(user_id, provider_type)`

### Auto-increment
- `provider_id`

---

## 6. User_client_favorites

### Fields
- `user_id (FK)`
- `client_id (FK)`

### UNIQUE constraints
- `(user_id, client_id)`

---

## 7. Client_sources

### Fields
- `source_id (PK)`
- `client_id (FK)`
- `source_key`
- `source_name`
- `base_url`
- `index_url`
- `archive_url`
- `source_type`
- `parser_type`
- `is_active`
- `created_at`

### UNIQUE constraints
- `source_id`
- `(client_id, source_key)`

### Auto-increment
- `source_id`

---

## 8. Permission

### Fields
- `permission_id (PK)`
- `name`
- `description`

### UNIQUE constraints
- `permission_id`
- `name`

### Auto-increment
- `permission_id`

---

## 9. Role

### Fields
- `role_id (PK)`
- `name`
- `description`

### UNIQUE constraints
- `role_id`
- `name`

### Auto-increment
- `role_id`

---

## 10. Role_permission

### Fields
- `role_id (FK)`
- `permission_id (FK)`

### UNIQUE constraints
- `(role_id, permission_id)`

---

## 11. Saved_searches

### Fields
- `saved_search_id (PK)`
- `user_id (FK)`
- `client_id (FK)`
- `name`
- `description`
- `created_at`
- `updated_at`

### UNIQUE constraints
- `saved_search_id`
- `(user_id, client_id, name)`

### Auto-increment
- `saved_search_id`

---

## 12. Saved_search_sources

### Fields
- `saved_search_id (FK)`
- `source_id (FK)`

### UNIQUE constraints
- `(saved_search_id, source_id)`

---

## 13. Keywords

### Fields
- `keyword_id (PK)`
- `keyword`
- `description`
- `is_active`
- `created_at`
- `updated_at`

### UNIQUE constraints
- `keyword_id`
- `keyword`

### Auto-increment
- `keyword_id`

---

## 14. Saved_search_keywords

### Fields
- `saved_search_id (FK)`
- `keyword_id (FK)`

### UNIQUE constraints
- `(saved_search_id, keyword_id)`

---

## Schema Status

- **Version:** v1
- **Design:** Locked
- **Documentation:** Field-accurate
- **Ready for:** SQL migrations and implementation
