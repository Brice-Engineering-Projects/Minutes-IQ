# Admin Governance Policy

## Purpose
This document defines the governance model for the JEA Meeting Minutes Scraper web application.  
The goal is to clearly establish **who controls access, who operates the system, and where responsibilities begin and end**.

This application is intended for **private, internal use only**.

---

## Governance Model

**Single-Admin Governance (Owner-Operated)**

- One administrator (project owner)
- No public access
- No self-registration
- No delegated admin roles in MVP

The Admin acts as the sole authority for access control and system configuration.

---

## Roles & Permissions

### Admin
The Admin is the project owner and system operator.

**Capabilities**
- Grant and revoke user access
- Disable accounts if compromised
- Trigger scraper runs
- Access all annotated outputs
- Modify system configuration
- Maintain infrastructure and secrets

**Limitations**
- Does not manage user passwords
- Does not perform password resets
- Does not access user credentials

---

### Authorized User
Users who have been explicitly approved by the Admin.

**Capabilities**
- Log in
- Trigger scraper workflows
- Download annotated PDFs
- View dashboard status

**Restrictions**
- Cannot invite other users
- Cannot modify system configuration
- Cannot access admin-only settings

---

### Unauthenticated Users
- No access
- No visibility into the system

---

## User Lifecycle Policy

- Users are manually approved by the Admin
- No automated onboarding
- No self-service registration
- Access can be revoked at any time
- Account existence does not imply permanence

---

## Data Governance

- No documents stored in the database
- Annotated PDFs stored locally only
- No analytics or tracking
- No third-party data sharing

---

## Change Management

All system changes:
- Are version-controlled
- Are documented
- Are performed by the Admin only

---

## Governance Boundary

This application is:
- A private internal tool
- A decision-support utility

This application is **not**:
- A public SaaS product
- A shared enterprise platform
- A compliance or records system

---

## Status

**Governance Policy: Defined and Active**
