# Reset Admin Password

This guide explains how to reset the admin user's password in the JEA Meeting Web Scraper application.

## Quick Steps

1. **Update your `.env` file** with the new password:
   ```bash
   APP_PASSWORD=your_new_password_here
   ```

2. **Run the reset script:**
   ```bash
   uv run python src/jea_meeting_web_scraper/scripts/reset_admin_password.py
   ```

3. **Restart your FastAPI server** (if running):
   ```bash
   # Press Ctrl+C to stop, then:
   uv run uvicorn src.jea_meeting_web_scraper.main:app --reload
   ```

4. **Login** at `http://localhost:8000/docs` with:
   - **Username:** `admin`
   - **Password:** (your new password from `.env`)

## What the Script Does

The `reset_admin_password.py` script:

1. ✅ Reads the password from your `.env` file (`APP_PASSWORD`)
2. 🔒 Generates a secure bcrypt hash
3. 🗑️ Deletes the old password hash from the Turso database
4. ➕ Inserts the new password hash
5. ✔️ Verifies the new password works

## Important Notes

⚠️ **Environment Variable Override:**
- If you have `APP_PASSWORD` set as a shell environment variable, it will override the `.env` file
- To fix this, run: `unset APP_PASSWORD` before running the script
- Check your current environment: `echo $APP_PASSWORD`

⚠️ **Server Restart Required:**
- FastAPI caches the `.env` file at startup
- You MUST restart the server after changing the password
- The `--reload` flag only reloads code changes, not environment variables

## Troubleshooting

### Password still not working after reset?

1. **Check if environment variable is set:**
   ```bash
   echo $APP_PASSWORD
   ```
   If this shows a value, unset it:
   ```bash
   unset APP_PASSWORD
   ```

2. **Verify the `.env` file is being read:**
   ```bash
   uv run python src/jea_meeting_web_scraper/scripts/check_env_password.py
   ```

3. **Ensure you restarted the FastAPI server** completely (Ctrl+C and restart, don't rely on auto-reload)

### Script fails with "Admin credentials not found"?

This means the admin user doesn't exist in the database. Run the seed script first:
```bash
uv run python src/jea_meeting_web_scraper/scripts/seed_admin_credential.py
```

## Security Best Practices

- ✅ Use a strong password (minimum 12 characters)
- ✅ Include uppercase, lowercase, numbers, and special characters
- ✅ Never commit `.env` files to version control
- ✅ Don't share your password in plain text
- ✅ Consider using a password manager to generate secure passwords

## Example Password Requirements

Good passwords:
- `MyS3cur3P@ssw0rd!2024`
- `Admin_2024_Secure#Pass`
- `J3@Sc4ap3r!Admin#2024`

Avoid:
- ❌ `admin` (too simple)
- ❌ `password123` (too common)
- ❌ `12345678` (sequential)
