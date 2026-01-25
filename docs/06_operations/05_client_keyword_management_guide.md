# Client & Keyword Management Operational Guide

This guide provides step-by-step instructions for administrators to manage clients (government agencies) and keywords used for filtering meeting minutes.

---

## Table of Contents

1. [Overview](#overview)
2. [Admin Setup](#admin-setup)
3. [Managing Clients](#managing-clients)
4. [Managing Keywords](#managing-keywords)
5. [Managing Associations](#managing-associations)
6. [User Experience](#user-experience)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Overview

### What Are Clients?

**Clients** are government agencies or organizations whose meeting minutes you want to track. Examples:
- JEA (Jacksonville Electric Authority)
- City of Jacksonville
- Duval County Schools
- Jacksonville Transportation Authority

### What Are Keywords?

**Keywords** are search terms used to filter and identify relevant discussions in meeting minutes. Examples:
- "water" - for tracking water service discussions
- "budget" - for financial planning topics
- "infrastructure" - for development projects

### System Architecture

```
Admin Creates → Clients + Keywords → Associates Them
                     ↓
Users View Active Clients → Add to Favorites → See Associated Keywords
                     ↓
Scraper Uses Keywords → Filters Meeting Minutes
```

---

## Admin Setup

### Prerequisites

1. **Admin Account**: You must have an admin role (role_id=1)
2. **Authentication**: Obtain your JWT token via login
3. **API Access**: Access to the API endpoints (typically http://localhost:8000)

### Getting Your Admin Token

```bash
# Login to get your token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password"

# Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}

# Save token for future requests
export ADMIN_TOKEN="eyJhbGc..."
```

---

## Managing Clients

### Creating a New Client

#### Step 1: Prepare Client Information

Gather:
- **Name** (required): Official organization name
- **Description** (optional): Brief description of the organization
- **Website URL** (optional): Official website

#### Step 2: Create the Client

```bash
curl -X POST http://localhost:8000/admin/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "JEA",
    "description": "Jacksonville Electric Authority - provides electric, water, and sewer services",
    "website_url": "https://www.jea.com"
  }'
```

**Success Response (201):**
```json
{
  "client_id": 1,
  "name": "JEA",
  "description": "Jacksonville Electric Authority - provides electric, water, and sewer services",
  "website_url": "https://www.jea.com",
  "is_active": true,
  "created_at": 1706198400,
  "created_by": 1,
  "updated_at": null,
  "keywords": null
}
```

**Common Errors:**
- `400`: Client name already exists
- `422`: Validation error (name too short, invalid URL, etc.)

#### Step 3: Verify Creation

```bash
# List all clients
curl -X GET http://localhost:8000/admin/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get specific client
curl -X GET http://localhost:8000/admin/clients/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Listing Clients

#### List All Clients

```bash
curl -X GET "http://localhost:8000/admin/clients?limit=100&offset=0" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Filter by Status

```bash
# Only active clients
curl -X GET "http://localhost:8000/admin/clients?is_active=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Only inactive clients
curl -X GET "http://localhost:8000/admin/clients?is_active=false" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Include Keywords

```bash
curl -X GET "http://localhost:8000/admin/clients?include_keywords=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Updating a Client

#### Update Name or Description

```bash
curl -X PUT http://localhost:8000/admin/clients/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "JEA - Jacksonville Electric Authority",
    "description": "Updated description with more details"
  }'
```

#### Deactivate a Client

```bash
curl -X PUT http://localhost:8000/admin/clients/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

**Note:** Deactivating a client:
- Hides it from regular users
- Preserves all associations and favorites
- Can be reactivated by setting `is_active: true`

### Deleting a Client

```bash
# Soft delete (sets is_active to false)
curl -X DELETE http://localhost:8000/admin/clients/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response:** `204 No Content`

**Important:** This is a soft delete. The client record remains in the database but is hidden from users.

---

## Managing Keywords

### Creating Keywords

#### Step 1: Plan Your Keyword Taxonomy

Organize keywords by category:

**Finance Keywords:**
- budget, revenue, rates, bonds, taxes, audit

**Infrastructure Keywords:**
- roads, bridges, construction, maintenance, repair

**Utilities Keywords:**
- water, electricity, wastewater, stormwater, sewer

**Public Works Keywords:**
- parks, facilities, sanitation, garbage

#### Step 2: Create Keywords

```bash
# Single keyword
curl -X POST http://localhost:8000/admin/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "water",
    "category": "Utilities",
    "description": "Water service, infrastructure, and quality discussions"
  }'

# Another keyword
curl -X POST http://localhost:8000/admin/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "budget",
    "category": "Finance",
    "description": "Budget planning, approval, and amendments"
  }'
```

#### Step 3: Batch Create Script

Create a script to add multiple keywords:

```bash
#!/bin/bash
# create_keywords.sh

KEYWORDS=(
  "water:Utilities:Water service discussions"
  "budget:Finance:Budget and financial planning"
  "rates:Finance:Service rates and pricing"
  "infrastructure:Public Works:Infrastructure projects"
  "maintenance:Public Works:Facility and equipment maintenance"
  "environmental:Environment:Environmental impact and sustainability"
)

for item in "${KEYWORDS[@]}"; do
  IFS=':' read -r keyword category description <<< "$item"

  curl -X POST http://localhost:8000/admin/keywords \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"keyword\": \"$keyword\",
      \"category\": \"$category\",
      \"description\": \"$description\"
    }"

  echo # New line
done
```

### Searching and Browsing Keywords

#### List All Keywords

```bash
curl -X GET http://localhost:8000/admin/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Filter by Category

```bash
curl -X GET "http://localhost:8000/admin/keywords?category=Utilities" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Search Keywords

```bash
# Find keywords containing "water"
curl -X GET "http://localhost:8000/admin/keywords/search?q=water" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Get Autocomplete Suggestions

```bash
# Get suggestions for "infra"
curl -X GET "http://localhost:8000/admin/keywords/suggest?q=infra&limit=5" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### View All Categories

```bash
curl -X GET http://localhost:8000/admin/keywords/categories \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Updating Keywords

```bash
# Update keyword text and category
curl -X PUT http://localhost:8000/admin/keywords/5 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "stormwater",
    "category": "Utilities",
    "description": "Stormwater management and drainage"
  }'

# Deactivate keyword
curl -X PUT http://localhost:8000/admin/keywords/5 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

### Deleting Keywords

```bash
curl -X DELETE http://localhost:8000/admin/keywords/5 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Managing Associations

### Associating Keywords with Clients

#### Step 1: Identify Client and Keywords

```bash
# Get client ID
curl -X GET "http://localhost:8000/admin/clients?limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | grep -A 2 "JEA"

# Get keyword IDs
curl -X GET "http://localhost:8000/admin/keywords?limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | grep -A 2 "water"
```

#### Step 2: Create Associations

```bash
# Associate JEA (client_id=1) with water (keyword_id=5)
curl -X POST http://localhost:8000/admin/clients/1/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword_id": 5}'

# Associate JEA with rates (keyword_id=8)
curl -X POST http://localhost:8000/admin/clients/1/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword_id": 8}'
```

#### Step 3: Verify Associations

```bash
# Get all keywords for a client
curl -X GET http://localhost:8000/admin/clients/1/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get all clients using a keyword
curl -X GET http://localhost:8000/admin/keywords/5/usage \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Bulk Association Script

```bash
#!/bin/bash
# associate_keywords.sh

CLIENT_ID=1
KEYWORD_IDS=(5 8 12 15 20)

for keyword_id in "${KEYWORD_IDS[@]}"; do
  curl -X POST http://localhost:8000/admin/clients/$CLIENT_ID/keywords \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"keyword_id\": $keyword_id}"

  echo "Associated keyword $keyword_id with client $CLIENT_ID"
done
```

### Removing Associations

```bash
# Remove keyword from client
curl -X DELETE http://localhost:8000/admin/clients/1/keywords/5 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## User Experience

### What Users See

Regular users (non-admins) can:
1. View all active clients
2. See keywords associated with each client
3. Add clients to their favorites
4. Remove clients from favorites
5. View their favorite clients list

### User Workflow Example

```bash
# 1. User lists available clients
curl -X GET http://localhost:8000/clients \
  -H "Authorization: Bearer $USER_TOKEN"

# 2. User views client details with keywords
curl -X GET http://localhost:8000/clients/1 \
  -H "Authorization: Bearer $USER_TOKEN"

# 3. User adds to favorites
curl -X POST http://localhost:8000/clients/1/favorite \
  -H "Authorization: Bearer $USER_TOKEN"

# 4. User views all favorites
curl -X GET http://localhost:8000/clients/favorites \
  -H "Authorization: Bearer $USER_TOKEN"
```

---

## Best Practices

### Client Management

1. **Descriptive Names**: Use official organization names
2. **Consistent Naming**: Follow a naming convention (e.g., "City of X" vs "X City")
3. **Complete Information**: Always add description and website when available
4. **Regular Audits**: Review client list quarterly for accuracy
5. **Soft Deletes**: Use deactivation instead of deletion to preserve history

### Keyword Strategy

1. **Start Broad**: Begin with general keywords, add specific ones as needed
2. **Use Categories**: Organize keywords into logical categories
3. **Avoid Duplicates**: Check for existing keywords before creating new ones
4. **Meaningful Descriptions**: Help users understand when to use each keyword
5. **Regular Review**: Remove or deactivate unused keywords

### Association Guidelines

1. **Relevance**: Only associate keywords that are highly relevant to the client
2. **Coverage**: Ensure each client has adequate keyword coverage
3. **Balance**: Avoid over-associating (5-15 keywords per client is typical)
4. **Testing**: Verify associations work as expected in searches

### Categorization

Recommended categories:
- Finance (budget, revenue, rates, taxes, bonds)
- Infrastructure (roads, bridges, construction)
- Utilities (water, electric, sewer, waste)
- Public Works (parks, facilities, maintenance)
- Planning (zoning, development, permits)
- Transportation (transit, traffic, parking)
- Environment (sustainability, conservation)
- Public Safety (police, fire, emergency)

---

## Troubleshooting

### Common Issues

#### Problem: Cannot Create Client
**Error:** `400 Bad Request - Client already exists`

**Solution:**
1. Check if client exists: `GET /admin/clients`
2. If inactive, reactivate it instead of creating new
3. Consider using a more specific name

---

#### Problem: Keyword Not Showing in Search
**Possible Causes:**
1. Keyword is inactive (`is_active=false`)
2. Keyword is not associated with any active client
3. Search query doesn't match keyword text

**Solution:**
```bash
# Check keyword status
curl -X GET http://localhost:8000/admin/keywords/5 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Reactivate if needed
curl -X PUT http://localhost:8000/admin/keywords/5 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}'
```

---

#### Problem: User Cannot See Client
**Possible Causes:**
1. Client is inactive
2. User lacks authentication
3. Client was recently created (cache issue)

**Solution:**
```bash
# Verify client is active
curl -X GET http://localhost:8000/admin/clients/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Reactivate if needed
curl -X PUT http://localhost:8000/admin/clients/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}'
```

---

#### Problem: Cannot Remove Keyword Association
**Error:** `404 Not Found`

**Solution:**
- Verify association exists: `GET /admin/clients/{id}/keywords`
- Ensure using correct client_id and keyword_id

---

### Performance Tips

1. **Pagination**: Use limit/offset for large lists
2. **Filtering**: Apply filters to reduce result size
3. **Caching**: Consider caching frequently accessed data
4. **Bulk Operations**: Use scripts for batch operations

---

## FAQ

### Q: What's the difference between deleting and deactivating?

**A:** Both operations set `is_active=false` (soft delete). The record remains in the database but is hidden from regular users. You can reactivate by setting `is_active=true`.

---

### Q: Can users create clients or keywords?

**A:** No. Only admins can create, update, or delete clients and keywords. Regular users can only view active clients and manage their own favorites.

---

### Q: How many keywords should I associate with each client?

**A:** Typically 5-15 keywords is optimal. Focus on the most relevant topics discussed in that client's meetings.

---

### Q: Can a keyword belong to multiple categories?

**A:** No. Each keyword has one category. If needed, create separate keywords (e.g., "water_quality" and "water_rates").

---

### Q: What happens to user favorites when a client is deleted?

**A:** Favorites are preserved but hidden. If the client is reactivated, favorites are restored.

---

### Q: Can I rename a client without losing associations?

**A:** Yes. Use `PUT /admin/clients/{id}` with the new name. All associations and favorites are preserved.

---

### Q: How do I know which keywords are most used?

**A:** Use `GET /admin/keywords/{id}/usage` to see which clients use each keyword. Popular keywords will have many associated clients.

---

### Q: Can I export the client/keyword list?

**A:** Yes, use the API to fetch all records and save to a file:
```bash
curl -X GET "http://localhost:8000/admin/clients?limit=1000" \
  -H "Authorization: Bearer $ADMIN_TOKEN" > clients.json
```

---

## Quick Reference

### Essential Admin Commands

```bash
# Setup
export ADMIN_TOKEN="your_token_here"

# Create client
curl -X POST http://localhost:8000/admin/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Client Name", "description": "Description"}'

# Create keyword
curl -X POST http://localhost:8000/admin/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "keyword", "category": "Category"}'

# Associate keyword with client
curl -X POST http://localhost:8000/admin/clients/1/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keyword_id": 5}'

# List clients
curl -X GET http://localhost:8000/admin/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# List keywords
curl -X GET http://localhost:8000/admin/keywords \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Additional Resources

- **API Documentation**: See `docs/04_api/03_client_keyword_api.md`
- **Data Model**: See `docs/03_architecture/05_client_keyword_data_model.md`
- **User Guide**: See `docs/06_operations/04_user_registration_guide.md`

---

## Support

For issues or questions:
1. Check this guide first
2. Review API documentation
3. Contact system administrator
4. Submit issue on GitHub
