# 🧰 Operational Runbook

## Purpose
Provides step-by-step guidance for common operational scenarios.

---

## Scenario: User Cannot Log In

1. Confirm email exists in database
2. Check user is_active flag
3. Verify JWT secret has not rotated unexpectedly
4. Review auth logs

---

## Scenario: Password Reset Email Not Received

1. Verify SMTP credentials
2. Check spam filters
3. Confirm reset token created
4. Inspect mail service logs

---

## Scenario: Scraper Job Fails

1. Identify client involved
2. Review scraper logs
3. Test source URL manually
4. Disable client if necessary

---

## Scenario: Client Website Changed

1. Disable affected client
2. Update scraper logic
3. Re-test onboarding checklist
4. Re-enable client

---

**Operational Rule:**  
> _Stability first, features second._
