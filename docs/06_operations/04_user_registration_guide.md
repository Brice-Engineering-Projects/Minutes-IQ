# 👥 User Registration Guide

*How to onboard new users using Authorization Codes*

This guide explains the complete workflow for adding new users to the JEA Meeting Intelligence Platform.

---

## Overview

The platform uses an **invite-only registration system**:
1. An **admin** creates an authorization code
2. The **admin** shares the code with the new user (via email, message, etc.)
3. The **new user** uses the code to create their account
4. The code is automatically marked as used (or decremented if multi-use)

This ensures only authorized individuals can create accounts.

---

## For Admins: Creating Authorization Codes

### Step 1: Log in as Admin

Access the platform and authenticate with your admin credentials.

### Step 2: Create an Authorization Code

**Via API:**

```bash
curl -X POST "http://localhost:8000/admin/auth-codes" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "expires_in_days": 7,
    "max_uses": 1,
    "notes": "Code for John Doe - Marketing Team"
  }'
```

**Request Parameters:**
- `expires_in_days` (optional): Number of days until the code expires (default: 7)
  - Set to `null` for codes that never expire
- `max_uses` (optional): How many times the code can be used (default: 1)
  - `1` = single-use code
  - `5` = can be used by 5 different users
- `notes` (optional): Internal notes for tracking (e.g., who the code is for)

**Response:**
```json
{
  "code_id": 42,
  "code": "A3B79K2M5PQ8",
  "code_formatted": "A3B7-9K2M-5PQ8",
  "created_by": 1,
  "created_at": 1706000000,
  "expires_at": 1706604800,
  "max_uses": 1,
  "current_uses": 0,
  "is_active": true,
  "notes": "Code for John Doe - Marketing Team"
}
```

⚠️ **Important:** Save the `code_formatted` value (e.g., `A3B7-9K2M-5PQ8`) - this is what you'll share with the user.

### Step 3: Share the Code

Send the authorization code to the new user via a secure channel:

**Example Email:**
```
Hi [User Name],

Welcome to the JEA Meeting Intelligence Platform!

To create your account, please visit:
http://your-domain.com/register

Use this authorization code when registering:
A3B7-9K2M-5PQ8

This code expires in 7 days and can be used once.

Best regards,
Admin Team
```

### Common Code Configurations

**Single-use, expires in 7 days (default):**
```json
{
  "expires_in_days": 7,
  "max_uses": 1,
  "notes": "Individual invite"
}
```

**Multi-use for team onboarding (5 people):**
```json
{
  "expires_in_days": 14,
  "max_uses": 5,
  "notes": "Marketing team batch invite"
}
```

**Long-lived code that never expires:**
```json
{
  "expires_in_days": null,
  "max_uses": 1,
  "notes": "Permanent invite for executive"
}
```

### Managing Authorization Codes

**List all active codes:**
```bash
curl -X GET "http://localhost:8000/admin/auth-codes?status_filter=active" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

**View usage history for a code:**
```bash
curl -X GET "http://localhost:8000/admin/auth-codes/42/usage" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

**Revoke a code (prevent further use):**
```bash
curl -X DELETE "http://localhost:8000/admin/auth-codes/42" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

**Filter codes by status:**
- `status_filter=active` - Unused codes that haven't expired
- `status_filter=used` - Fully used codes
- `status_filter=expired` - Codes past their expiration date
- `status_filter=revoked` - Manually revoked codes
- `status_filter=all` - All codes

---

## For New Users: Creating an Account

### Step 1: Obtain an Authorization Code

Contact an administrator to receive your authorization code. It will look like:
```
A3B7-9K2M-5PQ8
```

### Step 2: Navigate to Registration Page

Visit the registration page (URL provided by your admin):
```
http://your-domain.com/register
```

### Step 3: Complete the Registration Form

**Via Web Form:**
Fill in the registration form with:
- **Username:** Your desired username (unique)
- **Email:** Your email address (unique)
- **Password:** At least 8 characters
- **Authorization Code:** The code provided by the admin

**Via API:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "auth_code": "A3B7-9K2M-5PQ8"
  }'
```

### Step 4: Success!

If registration succeeds, you'll receive:
```json
{
  "message": "User registered successfully",
  "user": {
    "user_id": 123,
    "username": "johndoe",
    "email": "john@example.com",
    "role_id": 2
  }
}
```

You can now log in with your username and password.

### Troubleshooting Registration Errors

**"Invalid authorization code"**
- The code doesn't exist or was typed incorrectly
- Check for typos (codes are case-insensitive, hyphens are optional)
- Contact your admin for a new code

**"Authorization code has expired"**
- The code was valid but has passed its expiration date
- Contact your admin for a new code

**"Authorization code has been fully used"**
- All uses of this code have been consumed
- Contact your admin for a new code

**"Username already exists"** or **"Email already exists"**
- Choose a different username or email
- If you already have an account, use the login page instead

**"Password must be at least 8 characters"**
- Choose a longer password

---

## Code Format & Validation

### Code Format
- **Length:** 12 characters (uppercase letters A-Z and digits 0-9)
- **Display Format:** `XXXX-XXXX-XXXX` (with hyphens for readability)
- **Storage Format:** `XXXXXXXXXXXX` (no hyphens)

### Flexible Input
Users can enter codes in any of these formats:
- `A3B7-9K2M-5PQ8` ✓
- `A3B79K2M5PQ8` ✓
- `a3b7-9k2m-5pq8` ✓ (case-insensitive)
- `a3b79k2m5pq8` ✓

### Code Security
- Generated using Python's `secrets` module (cryptographically secure)
- 62^12 = ~3.2 quintillion possible combinations
- Extremely low collision probability
- Cannot be guessed or brute-forced

---

## Administrative Workflows

### Onboarding a Single User

1. Admin creates single-use code:
   ```bash
   POST /admin/auth-codes
   {"max_uses": 1, "expires_in_days": 7, "notes": "John Doe"}
   ```

2. Admin receives code: `A3B7-9K2M-5PQ8`

3. Admin emails code to user

4. User registers with code

5. Code automatically marked as used

6. Admin can view usage history to confirm

### Onboarding a Team

1. Admin creates multi-use code:
   ```bash
   POST /admin/auth-codes
   {"max_uses": 10, "expires_in_days": 30, "notes": "Q1 2024 Marketing Team"}
   ```

2. Admin receives code: `X7Y2-K9M4-P1Q8`

3. Admin shares code with entire team (email, Slack, etc.)

4. Each team member registers using the same code

5. Code tracks usage (1/10, 2/10, ... 10/10)

6. Admin monitors usage:
   ```bash
   GET /admin/auth-codes/43/usage
   ```

7. If someone leaves before using it, admin can revoke:
   ```bash
   DELETE /admin/auth-codes/43
   ```

### Emergency Code Revocation

If a code is leaked or needs to be invalidated:

1. Find the code ID:
   ```bash
   GET /admin/auth-codes?status_filter=active
   ```

2. Revoke it:
   ```bash
   DELETE /admin/auth-codes/42
   ```

3. Create a new code for legitimate users

4. The revoked code cannot be used for registration

---

## Audit & Compliance

### Tracking Who Invited Whom

Every code tracks:
- Who created it (`created_by` admin user ID)
- When it was created (`created_at` timestamp)
- Who used it (`usage_history` with user IDs)
- When it was used (`used_at` timestamp)

**View complete audit trail:**
```bash
GET /admin/auth-codes/42/usage
```

**Response:**
```json
{
  "code_id": 42,
  "usage_history": [
    {
      "user_id": 123,
      "username": "johndoe",
      "email": "john@example.com",
      "used_at": 1706000000
    }
  ],
  "total_uses": 1
}
```

### Compliance Benefits

- **Accountability:** Every account creation is traceable to an admin
- **Access Control:** Prevents unauthorized account creation
- **Time-Bound Access:** Codes can expire automatically
- **Revocation:** Codes can be invalidated if compromised
- **Audit Trail:** Complete history of who invited whom

---

## Best Practices

### For Admins

1. **Use descriptive notes:** Always include who the code is for
   ```json
   {"notes": "John Doe - Marketing - john@example.com"}
   ```

2. **Set appropriate expiration:**
   - 7 days for individual invites (default)
   - 30 days for team invites
   - No expiration only for permanent/executive invites

3. **Use single-use codes by default:** Multi-use only for controlled team onboarding

4. **Monitor usage regularly:**
   ```bash
   GET /admin/auth-codes?status_filter=all
   ```

5. **Revoke unused expired codes:** Clean up periodically
   ```bash
   # List expired codes
   GET /admin/auth-codes?status_filter=expired

   # Revoke if needed
   DELETE /admin/auth-codes/{id}
   ```

6. **Secure code delivery:**
   - Use secure channels (encrypted email, private messages)
   - Don't post codes in public channels
   - Consider using temporary/expiring messages

### For Users

1. **Save your credentials:** After registration, save your username/password securely

2. **Don't share your code:** Even multi-use codes should only be shared within the authorized group

3. **Register promptly:** Codes may expire or be revoked

4. **Contact admin if issues:** Don't try multiple codes - get help instead

---

## Security Considerations

### Why Authorization Codes?

Traditional open registration allows anyone to create an account. This system:
- **Prevents spam accounts**
- **Controls access to sensitive data** (meeting minutes, government documents)
- **Enables compliance** with organizational access policies
- **Provides accountability** through audit trails
- **Allows gradual rollout** during beta/pilot phases

### What This Prevents

- ❌ Unauthorized public access
- ❌ Bot/automated account creation
- ❌ Unrestricted data exposure
- ❌ Anonymous users
- ❌ Account enumeration attacks

### What This Enables

- ✅ Controlled onboarding
- ✅ Invitation-based access
- ✅ Usage tracking and accountability
- ✅ Time-limited access grants
- ✅ Emergency revocation capabilities

---

## Technical Details

### Database Schema

**auth_codes table:**
- `code_id` - Unique identifier
- `code` - The actual code (normalized, no hyphens)
- `created_by` - Admin user ID who created it
- `created_at` - Unix timestamp
- `expires_at` - Unix timestamp (nullable)
- `max_uses` - Maximum number of uses allowed
- `current_uses` - Current number of uses
- `is_active` - Whether code can still be used
- `notes` - Admin notes

**code_usage table:**
- `usage_id` - Unique identifier
- `code_id` - Foreign key to auth_codes
- `user_id` - Foreign key to users (who used it)
- `used_at` - Unix timestamp

### API Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/auth/register` | None | Register new account with code |
| POST | `/admin/auth-codes` | Admin | Create new authorization code |
| GET | `/admin/auth-codes` | Admin | List codes (with filters) |
| DELETE | `/admin/auth-codes/{id}` | Admin | Revoke a code |
| GET | `/admin/auth-codes/{id}/usage` | Admin | View usage history |

### Code Lifecycle

```
Created → Active → Used/Expired/Revoked → Archived
```

1. **Created:** Admin generates code
2. **Active:** Available for registration
3. **Used:** All uses consumed (if single-use) or still active (if multi-use)
4. **Expired:** Past expiration date
5. **Revoked:** Manually deactivated by admin
6. **Archived:** Historical record (never deleted)

---

## FAQ

**Q: Can I reuse a code after it's been used?**
A: Only if it's a multi-use code with remaining uses. Single-use codes cannot be reused.

**Q: What happens if I enter the code wrong?**
A: You'll get an error message. The code is not consumed unless registration succeeds.

**Q: Are codes case-sensitive?**
A: No, codes are case-insensitive. `A3B7` and `a3b7` are equivalent.

**Q: Do I need to include the hyphens?**
A: No, hyphens are optional. `A3B7-9K2M-5PQ8` and `A3B79K2M5PQ8` work the same.

**Q: Can I create my own code?**
A: No, only admins can generate codes. They're cryptographically random.

**Q: How do I become an admin?**
A: Admin access is granted by the system owner. Contact your organization's administrator.

**Q: What if my code expired?**
A: Contact an admin to generate a new code for you.

**Q: Can I see who else used a multi-use code?**
A: No, only admins can view usage history.

**Q: What happens to the code after I register?**
A: Single-use codes are marked as fully used. Multi-use codes decrement remaining uses.

**Q: Can a code be un-revoked?**
A: No, revocation is permanent. Create a new code instead.

---

## Support

For issues or questions:
1. Check this guide first
2. Contact your admin for code-related issues
3. Check the application logs if you're an admin
4. Review `/docs/04_security/` for security policies
5. See `/docs/02_architecture/03_api_contract.md` for API details
