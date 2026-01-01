# ⚙️ Configuration Reference

## Purpose
Defines all configuration values, environment variables, and defaults required to run the application safely across environments.

---

## Environment Variables

### Core Application
- `APP_ENV` — dev | prod
- `APP_NAME` — Application identifier
- `APP_BASE_URL` — Public base URL

### Security
- `SECRET_KEY` — JWT signing secret
- `JWT_EXP_MINUTES` — Access token lifetime
- `BCRYPT_ROUNDS` — Password hashing cost factor

### Registration Control
- `AUTH_CODE_LENGTH` — Default: 6
- `AUTH_CODE_REUSABLE` — true | false

### Database (Turso)
- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

### Email (Password Reset)
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`

---

## Configuration Rules

- No secrets committed to repo
- All secrets injected at runtime
- Defaults allowed only for non-sensitive values

---

**Config Rule:**  
> _If it can break security, it must be explicit._
