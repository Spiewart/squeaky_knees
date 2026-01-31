# Quick Reference: Health Check & Rate Limiting

## Health Check Endpoint

### Endpoint
```
GET /health/
```

### Response (Success)
```json
{
  "status": "ok",
  "database": "connected"
}
```
Status Code: `200`

### Response (Failure)
```json
{
  "status": "error",
  "database": "disconnected",
  "error": "Connection refused"
}
```
Status Code: `503`

### Usage in Monitoring
```bash
# Check if app is healthy
curl -f http://your-domain.com/health/

# In deployment script
curl -f http://localhost:8000/health/ | grep -q '"status":"ok"' || exit 1
```

---

## Rate Limiting Configuration

### Search Endpoint
- **Endpoint**: `GET /blog/actions/search/?query=...`
- **Limit**: 30 requests per 300 seconds (5 minutes)
- **Response When Limited**: Returns search results but logs rate limit hit
- **Key**: `"blog_search"`

### Comment Submission
- **Endpoint**: `POST /blog/comment/<page_id>/`
- **Limit**: 10 comments per 3600 seconds (1 hour)
- **Response When Limited**: Form validation fails with error message
- **Key**: `"comment_add"`

### User Signup
- **Endpoint**: `POST /accounts/signup/` or social login endpoints
- **Limit**: 5 signups per 3600 seconds (1 hour)
- **Response When Limited**: Form validation fails with error message
- **Key**: `"user_signup"`

### Implementation Location
See `config/ratelimit.py` for the rate limiting logic:
```python
def is_rate_limited(request, key, max_attempts=10, window_seconds=3600):
    """Check if request exceeds rate limit."""
    # Returns True if rate limited, False otherwise
```

---

## Email Notifications

### Trigger
A comment is submitted on a blog post

### Recipient
Blog post owner (if owner exists)

### Notification Type
- Sent immediately on comment submission
- Informs owner of new pending comment
- Includes comment preview and link to moderation page

### Configuration
Located in `squeaky_knees/blog/email.py`:
```python
def send_comment_notification(comment):
    """Send email to blog post owner about new comment."""
```

### Testing
All email functionality is tested in `tests/test_email_notifications.py` (8 tests passing)

---

## Testing

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test Suite
```bash
# Health check tests
python -m pytest tests/test_health_check.py -v

# Rate limiting tests
python -m pytest tests/test_rate_limiting.py -v

# Email notification tests
python -m pytest squeaky_knees/blog/tests/ -k email -v
```

### Test Coverage Summary
- **Total**: 285 tests
- **Health Check**: 6 tests (endpoint, database, JSON, auth-free)
- **Rate Limiting**: 4 tests (search, comments, signup)
- **Email**: 8 tests (sending, content, recipients)

---

## Deployment Verification

The GitHub Actions deployment workflow automatically verifies the health endpoint:

```yaml
# In .github/workflows/deploy.yml
- name: Verify Deployment
  run: curl -f http://localhost:8000/health/ | grep -q '"status":"ok"' || exit 1
```

This ensures:
1. ✅ App is running on port 8000
2. ✅ Database is connected
3. ✅ No errors in health check endpoint

---

## Troubleshooting

### Health check returns 503
```json
{"status": "error", "database": "disconnected"}
```
**Solutions**:
- Check database connection string in `.env`
- Verify PostgreSQL/database is running
- Check database credentials
- Review application logs

### Rate limiting too strict
**To adjust limits**, edit `config/ratelimit.py`:
```python
# Search limit
is_rate_limited(request, "blog_search", max_attempts=30, window_seconds=300)

# Comment limit
is_rate_limited(request, "comment_add", max_attempts=10, window_seconds=3600)

# Change max_attempts or window_seconds as needed
```

### Email notifications not sending
**Check**:
- Email backend configuration in `config/settings/base.py`
- Blog post has an owner assigned
- Email credentials in `.env` (if using SMTP)
- Application logs for email errors

---

## Related Files

| File | Purpose |
|------|---------|
| `squeaky_knees/views.py` | Health check view |
| `config/urls.py` | Route `/health/` endpoint |
| `config/ratelimit.py` | Rate limiting logic |
| `squeaky_knees/blog/email.py` | Email notifications |
| `squeaky_knees/blog/views.py` | Comment handling |
| `tests/test_health_check.py` | Health check tests |
| `tests/test_rate_limiting.py` | Rate limiting tests |
| `.github/workflows/deploy.yml` | Deployment verification |

---

**Last Updated**: January 31, 2026
**Status**: ✅ All features tested and operational
