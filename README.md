# Squeaky Knees

Personal and research blog with a focus on osteoarthritis of the knee.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Features

### Blog Application
- **Wagtail CMS Integration**: Powerful content management system for creating and managing blog posts
- **Rich Text Editor**: Create engaging blog posts with images, formatting, and embedded media
- **Responsive Images**: Automatic image optimization and responsive design support
- **Tags and Categories**: Organize blog posts with tags for easy discovery
- **Comment System**: Registered users can leave comments on blog posts
- **Comment Moderation**: Admin approval workflow for all comments before publication
- **Nested Comment Threads**: Reply to comments with threaded discussions
- **User Authentication**: Built-in user registration and authentication system

### Content Management
- **Blog Posts**: Create and publish articles with featured images, tags, and rich content
- **Admin Interface**: Access the Wagtail admin at `/cms/` or Django admin at `/admin/`
- **Media Management**: Upload and manage images through the Wagtail media library

### Discovery and SEO
- **Blog Search**: Dedicated search page with input sanitization
- **Pagination**: Blog index supports page-based navigation
- **RSS Feed**: Subscribe at `/feed.xml`
- **Sitemap and Robots**: `/sitemap.xml` and `/robots.txt` for crawlers

### User Features
- **User Registration**: Users can create accounts to participate in discussions
- **Comment System**: Authenticated users can comment on blog posts
- **Profile Management**: Users can manage their profiles and view their activity

### Safety and Anti-Abuse
- **reCAPTCHA v3**: Protected signup and comment submission
- **Rate Limiting**: Limits on comment and signup actions
- **Input Validation and Sanitization**: XSS-safe HTML handling and length checks
- **Security Headers**: Protective headers on all responses
- **Custom Error Pages**: Styled 403/404/500 templates
- **Comment Notifications**: Email alerts for new comments and approvals
- **Logging and Error Tracking**: Structured logging for app and security events

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

```
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
- **CMS**: Wagtail 6.4
- **Authentication**: Django Allauth
- **Frontend**: Bootstrap 5
- **Database**: PostgreSQL (production), SQLite (development)
- **Image Processing**: Pillow, Wagtail Images
- **Tags**: django-taggit

## Deployment

The following details how to deploy this application.
# Trigger deployment
