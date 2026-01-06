# 📚 Database Schema Documentation
**Audience:** Non-engineers, analysts, managers, auditors  
**Goal:** Understand what data exists, why it exists, and what is safe vs dangerous to change

---

## Plain-English Overview (READ THIS FIRST)

This database supports an application that:

- Lets people log in
- Controls what each person is allowed to do
- Tracks organizations the user is interested in
- Collects documents from those organizations
- Lets users save searches and keywords

The database is organized into five main ideas:

1. People – who is using the system  
2. Login & Security – how people log in safely  
3. Permissions – what people are allowed to do  
4. Organizations & Sources – what data is being tracked  
5. Saved Searches – what users want to monitor  

Each table below represents one real-world concept.

---

## 1. `users` — People Who Use the System

| Field | What it means |
|-----|---------------|
| `user_id` | A system-assigned number that uniquely identifies the person. |
| `username` | The name the person types in when logging in. |
| `email` | The person’s email address, used for password resets. |
| `phone` | Optional phone number for reference only. |
| `role_id` | Determines what the person is allowed to do. |
| `provider_id` | Main login method for the person (for convenience only). |

---

## 2. `profile` — Display Information About a Person

| Field | What it means |
|-----|---------------|
| `profile_id` | System number for this profile record. |
| `user_id` | Which person this profile belongs to. |
| `first_name` | First name shown to others. |
| `last_name` | Last name shown to others. |
| `title` | Optional label such as job title. |

---

## 3. `auth_credentials` — Login Secrets

| Field | What it means |
|-----|---------------|
| `auth_id` | Identifier for this password record. |
| `provider_id` | Which login method this password belongs to. |
| `user_id` | Which person this password is for. |
| `hashed_password` | Scrambled version of the password that cannot be reversed. |
| `is_active` | Whether this password currently works. |
| `created_at` | When the password was created. |

---

## 4. `client` — Organizations Being Tracked

| Field | What it means |
|-----|---------------|
| `client_id` | Identifier for the organization. |
| `name` | Name of the organization. |
| `is_active` | Whether the organization is currently active. |
| `created_at` | When the organization was added. |

---

## 5. `auth_provider` — How a Person Logs In

| Field | What it means |
|-----|---------------|
| `provider_id` | Identifier for this login method. |
| `user_id` | Which person this login method belongs to. |
| `provider_type` | Type of login (for example, password). |

---

## 6. `user_client_favorites` — Favorite Organizations

| Field | What it means |
|-----|---------------|
| `user_id` | The person. |
| `client_id` | The organization they favorited. |

---

## 7. `client_sources` — Where Data Comes From

| Field | What it means |
|-----|---------------|
| `source_id` | Identifier for this source. |
| `client_id` | Which organization this source belongs to. |
| `source_key` | Internal label used by the system. |
| `source_name` | Friendly name shown to users. |
| `base_url` | Main website address. |
| `index_url` | Page used to find documents. |
| `archive_url` | Page used to find older documents. |
| `source_type` | Kind of content expected. |
| `parser_type` | How the system reads the content. |
| `is_active` | Whether this source is currently used. |
| `created_at` | When the source was added. |

---

## 8. `permission` — Individual Allowed Actions

| Field | What it means |
|-----|---------------|
| `permission_id` | Identifier for the action. |
| `name` | Exact action name the system checks. Changing it can break access. |
| `description` | Plain explanation of the action. |

---

## 9. `role` — Groups of Permissions

| Field | What it means |
|-----|---------------|
| `role_id` | Identifier for the role. |
| `name` | Role name such as “admin”. |
| `description` | What this role allows. |

---

## 10. `role_permission` — What Each Role Can Do

| Field | What it means |
|-----|---------------|
| `role_id` | The role. |
| `permission_id` | An action the role is allowed to perform. |

---

## 11. `saved_searches` — User-Defined Searches

| Field | What it means |
|-----|---------------|
| `saved_search_id` | Identifier for the saved search. |
| `user_id` | Who owns the search. |
| `client_id` | Organization the search targets. |
| `name` | Name chosen by the user. |
| `description` | Optional notes. |
| `created_at` | When it was created. |
| `updated_at` | When it was last changed. |

---

## 12. `saved_search_sources`

| Field | What it means |
|-----|---------------|
| `saved_search_id` | The saved search. |
| `source_id` | A source included in that search. |

---

## 13. `keywords` — Search Terms

| Field | What it means |
|-----|---------------|
| `keyword_id` | Identifier for the keyword. |
| `keyword` | The word or phrase being searched for. |
| `description` | Explanation or context. |
| `is_active` | Whether the keyword is used. |
| `created_at` | When it was added. |
| `updated_at` | When it was last changed. |

---

## 14. `saved_search_keywords`

| Field | What it means |
|-----|---------------|
| `saved_search_id` | The saved search. |
| `keyword_id` | A keyword used in that search. |

---

## Final Status

- Designed for non-technical readers
- Explains what each table represents and why it exists
- Avoids technical jargon
