#!/usr/bin/env python3
"""Quick script to check admin users in the database."""

import sqlite3

# Connect to database
conn = sqlite3.connect("minutes_iq.db")
cursor = conn.cursor()

# Check users and their roles
cursor.execute("""
    SELECT u.user_id, u.username, u.email, u.role_id, r.role_name
    FROM users u
    LEFT JOIN roles r ON u.role_id = r.role_id
    ORDER BY u.user_id
""")

print("\n=== Users in Database ===")
print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role ID':<8} {'Role Name':<10}")
print("-" * 80)

users = cursor.fetchall()
for user in users:
    print(
        f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {user[3]:<8} {user[4] or 'N/A':<10}"
    )

print(f"\nTotal users: {len(users)}")
print(f"Admin users (role_id=1): {sum(1 for u in users if u[3] == 1)}")

conn.close()
