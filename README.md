# Squeaky Knees

Personal and research blog with a focus on osteoarthritis of the knee.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Features

### Blog & Content

Blog posts are authored in the Wagtail CMS admin (`/cms/`) using a StreamField body that supports rich text blocks and syntax-highlighted code blocks. Each post can have a header image, intro text, and tags via django-taggit.

- **Code blocks** -- a `CodeBlock` Wagtail StructBlock with an optional `language` field and a `code` textarea. Rendered as `<pre><code class="language-{lang}">` for client-side syntax highlighting. Available in both post bodies (via the CMS editor) and user comments/replies (via the JS block editor).
- **Threaded comments** -- authenticated users can comment and reply at any depth. Replies are visually indented and rendered recursively. Comments support both rich text and code blocks, serialized as StreamField JSON via a lightweight JS block editor with "Add Text" and "Add Code" buttons, bold/italic/link formatting, and a language selector for code.
- **Comment moderation** -- all comments require staff approval before appearing. A dedicated moderation queue at `/blog/actions/moderate/` lets staff approve or delete pending comments with search filtering. Bulk approve/unapprove actions are also available in the Django admin.
- **Email notifications** -- post authors receive an HTML email when a new comment is submitted; commenters are notified when their comment is approved. Sent via Mailgun (Anymail) in production.

### Discovery & SEO

- **Full-text search** -- Wagtail's search backend indexes post titles, intros, and body content. Accessible at `/blog/actions/search/?query=...` with query sanitization (min 2 chars, max 200, stripped angle brackets/quotes).
- **Tag search** -- clicking a tag anywhere on the site filters posts by tag slug. The homepage displays all tags from published posts as clickable links.
- **Pagination** -- the blog index paginates at 10 posts per page with full Bootstrap navigation (first/prev/numbered/next/last).
- **RSS feed** -- hand-written RSS 2.0 XML at `/feed.xml` with the latest 20 posts including `content:encoded` (full body) and `<category>` tags.
- **Sitemap & robots.txt** -- `/sitemap.xml` includes the blog index and all published posts with `lastmod` timestamps. `/robots.txt` allows all crawlers and disallows admin paths. Both are cached.

### Safety & Anti-Abuse

- **reCAPTCHA v3** on comment and signup forms. Reply forms fetch tokens asynchronously via the Google reCAPTCHA JS API.
- **Rate limiting** -- cache-backed limiter keyed by user ID (authenticated) or IP (anonymous). Comments are capped at 10 per hour per user.
- **Input sanitization** -- `sanitize_html()` strips `<script>`, event handlers, `<iframe>`, and `<style>` tags. Code blocks are capped at 10,000 characters; comment text at 5,000 (after stripping HTML for counting).
- **Security headers** -- custom middleware adds `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, and `X-Frame-Options: DENY`. Production uses HSTS, secure cookies (`__Secure-` prefix), and Argon2 password hashing.
- **Custom error pages** -- styled 403, 404, and 500 templates.
- **Sentry** integration for error tracking and structured logging.

## Getting Started

### Prerequisites

- Python 3.13 or higher
- PostgreSQL (for production) or SQLite (for development)
- pip or uv package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Spiewart/squeaky_knees.git
   cd squeaky_knees
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or with uv:
   uv sync
   ```

3. Set up environment variables:
   - Local defaults live in `.envs/.local/.django` and `.envs/.local/.postgres`
   - Ensure `RECAPTCHA_V3_SITE_KEY` and `RECAPTCHA_V3_SECRET_KEY` are set
   - If you prefer environment variables, you can also export:
     ```bash
     export DJANGO_SETTINGS_MODULE=config.settings.local
     export DATABASE_URL=postgres://username:password@localhost:5432/squeaky_knees
     ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Creating Your First Blog

1. Access the Wagtail admin interface at `http://localhost:8000/cms/`
2. Log in with your superuser credentials
3. Navigate to **Pages** in the sidebar
4. Create a **Blog Index Page** as a child of the home page
5. Add a site under settings > sites and nest under the Blog Index Page (ensures correct routing)
6. Under the Blog Index Page, create **Blog Page** instances for individual posts
7. Add featured images, tags, and rich content to your blog posts
8. Publish your pages to make them visible on the site

### Useful Endpoints

- Home: `http://localhost:8000/`
- Blog: `http://localhost:8000/blog/`
- Blog search: `http://localhost:8000/blog/actions/search/`
- RSS feed: `http://localhost:8000/feed.xml`
- Sitemap: `http://localhost:8000/sitemap.xml`
- Robots: `http://localhost:8000/robots.txt`

### Managing Comments

1. Access the Django admin at `http://localhost:8000/admin/`
2. Navigate to **Blog** → **Comments**
3. Review submitted comments
4. Use the **Approve selected comments** action to publish comments
5. Comments will appear on the blog post once approved

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    mypy squeaky_knees

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    coverage run -m pytest
    coverage html
    open htmlcov/index.html

#### Running tests with pytest

    pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Project Structure

```text
squeaky_knees/
├── squeaky_knees/
│   ├── blog/           # Blog application with Wagtail models
│   ├── users/          # User management
│   ├── templates/      # Django templates
│   └── static/         # Static files (CSS, JS, images)
├── config/             # Django settings and configuration
├── docs/               # Documentation
└── tests/              # Test files
```

## Technology Stack

- **Framework**: Django 5.2
- **CMS**: Wagtail
- **Authentication**: Django Allauth (username login, mandatory email verification, MFA support)
- **Frontend**: Bootstrap 5
- **Database**: PostgreSQL 16 (production), SQLite (development)
- **Cache**: Redis 7 (production), local memory (development)
- **Image Processing**: Pillow, Wagtail Images
- **Tags**: django-taggit
- **Email**: Mailgun via django-anymail
- **Package Manager**: uv

## Deployment

The site runs on a DigitalOcean $4/month Droplet (512 MB RAM, 1 vCPU). The entire stack -- application, database, cache, and reverse proxy -- runs as four Docker containers managed by Docker Compose on this single machine.

### Architecture

```text
Internet
  │
  ▼
Traefik v3.1  ──  TLS termination (Let's Encrypt) + HTTP→HTTPS redirect
  │                 Config: compose/production/traefik/traefik.yml
  ▼
Gunicorn  ──  1 worker, 120s timeout (tuned for 512 MB RAM)
  │
  ├── PostgreSQL 16  ──  shared_buffers=64MB, max_connections=25
  ├── Redis 7  ──  64MB max, allkeys-lru eviction
  └── AWS S3  ──  static files + media (served directly, not through Django)
```

Traefik routes all traffic via file-based configuration (`traefik.yml`). There is no Nginx layer -- Traefik proxies directly to Gunicorn.

### Container Stack

| Service | Image | Purpose | Memory tuning |
|---------|-------|---------|---------------|
| `web` | `python:3.13-alpine` (via GHCR) | Django/Gunicorn | 1 worker, Alpine (~60% smaller than slim) |
| `postgres` | `postgres:16` | Database | `shared_buffers=64MB`, `work_mem=4MB`, `max_connections=25` |
| `redis` | `redis:7-alpine` | Cache/sessions | `--maxmemory 64mb --maxmemory-policy allkeys-lru` |
| `traefik` | `traefik:v3.1` | Reverse proxy + TLS | Minimal footprint |

The `web` container waits for `postgres` and `redis` health checks to pass (`condition: service_healthy`) before starting.

### CI/CD Pipeline

Two GitHub Actions workflows in `.github/workflows/`:

**CI** (`ci.yml`) -- runs on PRs and pushes to `main`:

- Linting via pre-commit (ruff, djLint, django-upgrade)
- pytest against a PostgreSQL 18 service container
- Migration consistency check (`makemigrations --check`)

**Deploy** (`deploy.yml`) -- triggers on pushes to `main`:

1. Build the Docker image and push to GitHub Container Registry (`:latest` + `:<sha>` tags)
2. Run `collectstatic` in CI with AWS credentials (uploads to S3, avoids running on the memory-constrained droplet)
3. SCP `docker-compose.production.yml` and `compose/production/traefik/` to the droplet
4. SSH into the droplet and deploy:
   - Create a 1 GB swapfile if absent (OOM protection)
   - Stop running containers and prune old images/build cache to free disk space
   - Pull the new image and start services with `docker compose up -d`
   - Run migrations with a 10-minute timeout
5. Verify deployment: wait for container health check, then curl `https://squeakyknees.blog/health/` for HTTP 200

### Static & Media Files

Static and media files are stored on AWS S3 with public-read ACLs and cache headers. `collectstatic` runs during CI -- not on the droplet -- using collectfasta for incremental uploads. django-compressor handles CSS/JS minification, also backed by S3.

### Low-Memory Design Decisions

Every layer is tuned for the 512 MB RAM constraint:

- **`collectstatic` runs in CI, not on the droplet.** Offloads S3 upload work to GitHub Actions runners.
- **Alpine base image.** ~60% smaller than Debian slim, reducing pull time and disk usage.
- **Single Gunicorn worker.** Prevents OOM kills from multiple worker processes.
- **Stop-before-pull pattern.** The deploy script stops containers and removes old images before pulling new ones, ensuring enough disk/memory for the pull.
- **1 GB swap at deploy time.** Cushions against OOM spikes during image pulls and migrations.
- **`AWS_EC2_METADATA_DISABLED=true`** during migrations prevents boto3 from hanging while trying to reach the EC2 metadata service on a non-AWS host.
