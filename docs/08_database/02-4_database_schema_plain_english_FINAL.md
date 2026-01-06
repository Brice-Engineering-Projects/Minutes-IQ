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

**What this table represents**  
A person who has access to the system.

**Why the system needs it**  
Every action in the system must be tied to a specific person.

**What breaks if this is wrong**  
If a user record is missing or incorrect, that person cannot log in or may be given the wrong access.

| Field | What it means |
|-----|---------------|
| `user_id` | A system-assigned number that uniquely identifies the person. The number itself has no meaning. |
| `username` | The name the person types in when logging in. Changing this affects how they sign in. |
| `email` | The person’s email address. Used for password resets and contact. |
| `phone` | Optional phone number for reference only. |
| `role_id` | Determines what the person is allowed to do. Changing this changes access immediately. |
| `provider_id` | Main login method for the person (for convenience only). |

---

## 2. `profile` — Display Information About a Person

**What this table represents**  
How a person should be shown in the interface.

**Why the system needs it**  
Separates login/security data from display information.

**What breaks if this is wrong**  
Nothing critical. This only affects how the user appears on screen.

| Field | What it means |
|-----|---------------|
| `profile_id` | System number for this profile record. |
| `user_id` | Which person this profile belongs to. |
| `first_name` | First name shown to others. |
| `last_name` | Last name shown to others. |
| `title` | Optional label such as job title. |

---

## 3. `auth_credentials` — Login Secrets

**What this table represents**  
The secure information used to verify a person’s password.

**Why the system needs it**  
Passwords must never be stored directly. This table stores a scrambled (hashed) version instead.

**What breaks if this is wrong**  
The person cannot log in, or security could be compromised.

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

**What this table represents**  
An organization whose documents or data are being monitored.

**Why the system needs it**  
Users choose which organizations they care about.

**What breaks if this is wrong**  
Users may not see or receive data from the correct organization.

| Field | What it means |
|-----|---------------|
| `client_id` | Identifier for the organization. |
| `name` | Name of the organization. |
| `is_active` | Whether the organization is currently active. |
| `created_at` | When the organization was added. |

---

## 5. `auth_provider` — How a Person Logs In

**What this table represents**  
The method a person uses to log in.

**Why the system needs it**  
A person may have different ways to authenticate.

**What breaks if this is wrong**  
Login may fail or route incorrectly.

| Field | What it means |
|-----|---------------|
| `provider_id` | Identifier for this login method. |
| `user_id` | Which person this login method belongs to. |
| `provider_type` | Type of login (for example: password). |

---

## 6. `user_client_favorites` — Favorite Organizations

**What this table represents**  
Which organizations a person has marked as important.

**Why the system needs it**  
So the interface can highlight preferred organizations.

**What breaks if this is wrong**  
Only user preferences are affected.

| Field | What it means |
|-----|---------------|
| `user_id` | The person. |
| `client_id` | The organization they favorited. |

---

## 7. `client_sources` — Where Data Comes From

**What this table represents**  
Specific websites or locations where documents are collected.

**Why the system needs it**  
Organizations publish information in many places.

**What breaks if this is wrong**  
Documents may not be collected correctly.

| Field | What it means |
|-----|---------------|
| `source_id` | Identifier for this source. |
| `client_id` | Which organization this source belongs to. |
| `source_key` | Internal label used by the system. Changing it can break data collection. |
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

**What this table represents**  
Single actions a person may or may not be allowed to perform.

**Why the system needs it**  
The system checks this table to decide access.

**What breaks if this is wrong**  
People may gain or lose access unexpectedly.

| Field | What it means |
|-----|---------------|
| `permission_id` | Identifier for the action. |
| `name` | Exact action name the system checks. Changing it without updating the app will break access. |
| `description` | Plain explanation of the action. |

---

## 9. `role` — Groups of Permissions

**What this table represents**  
A named group of allowed actions.

**Why the system needs it**  
Easier than assigning actions one by one.

**What breaks if this is wrong**  
People may have too much or too little access.

| Field | What it means |
|-----|---------------|
| `role_id` | Identifier for the role. |
| `name` | Role name such as “admin”. |
| `description` | What this role allows. |

---

## 10. `role_permission` — What Each Role Can Do

**What this table represents**  
Which actions belong to which roles.

**Why the system needs it**  
This enforces access rules.

**What breaks if this is wrong**  
Access rules stop making sense.

| Field | What it means |
|-----|---------------|
| `role_id` | The role. |
| `permission_id` | The allowed action. |

---

## 11. `saved_searches` — User-Defined Searches

**What this table represents**  
Searches a person has saved.

**Why the system needs it**  
So users don’t have to recreate searches.

**What breaks if this is wrong**  
Users lose saved configurations.

| Field | What it means |
|-----|---------------|
| `saved_search_id` | Identifier for the saved search. |
| `user_id` | Who owns the search. |
| `client_id` | Organization it targets. |
| `name` | Name chosen by the user. |
| `description` | Optional notes. |
| `created_at` | When it was created. |
| `updated_at` | When it was last changed. |

---

## 12. `saved_search_sources` — Sources Used by a Search

| Field | What it means |
|-----|---------------|
| `saved_search_id` | The saved search. |
| `source_id` | A source included in that search. |

---

## 13. `keywords` — Search Terms

**What this table represents**  
Words or phrases users want to look for.

| Field | What it means |
|-----|---------------|
| `keyword_id` | Identifier for the keyword. |
| `keyword` | The word or phrase being searched for. |
| `description` | Explanation or context. |
| `is_active` | Whether the keyword is currently used. |
| `created_at` | When it was added. |
| `updated_at` | When it was last changed. |

---

## 14. `saved_search_keywords` — Keywords Used in a Search

| Field | What it means |
|-----|---------------|
| `saved_search_id` | The saved search. |
| `keyword_id` | A keyword used in that search. |

---

## Final Status

- Designed for non-technical readers
- Explains what each table represents and why it exists
- Explicitly states what can break if changed
- This document should be understandable without prior project knowledge
