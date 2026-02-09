# AI Instructions for Squeaky Knees Blog Development

This document provides comprehensive guidelines for AI assistants working on the Squeaky Knees blog codebase. Following these instructions will help avoid linting errors and maintain code quality standards.

## Table of Contents

1. [Overview](#overview)
2. [Running Linters Locally](#running-linters-locally)
3. [Ruff Configuration and Common Errors](#ruff-configuration-and-common-errors)
4. [Django Template Linting (djLint)](#django-template-linting-djlint)
5. [Python Code Standards](#python-code-standards)
6. [Django and Wagtail Specific Patterns](#django-and-wagtail-specific-patterns)
7. [Pre-commit Hooks](#pre-commit-hooks)
8. [EditorConfig Standards](#editorconfig-standards)
9. [Common Mistakes to Avoid](#common-mistakes-to-avoid)

## Overview

This project uses multiple linting and formatting tools to maintain code quality:

- **Ruff**: Python linting and formatting (replaces Black, isort, flake8)
- **djLint**: Django/Wagtail template linting and formatting
- **Pre-commit**: Git hooks that run linters before commits
- **Django Upgrade**: Automatically upgrades Django syntax to target version 5.2

## Running Linters Locally

### Before Committing

**Always run these commands before committing code:**

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Or run specific hooks
pre-commit run ruff-check --all-files
pre-commit run ruff-format --all-files
pre-commit run djlint-django --all-files
```

### Auto-fix Issues

```bash
# Ruff can auto-fix many issues
ruff check --fix .

# Format code with ruff
ruff format .

# Format Django templates (use quotes for glob patterns)
djlint --reformat "**/*.html"
# Or reformat all templates in current directory
djlint --reformat .
```

### Install Pre-commit Hooks

```bash
# Install hooks to run automatically on git commit
pre-commit install
```

## Ruff Configuration and Common Errors

### Selected Rule Categories

The project enables extensive ruff rules (see `pyproject.toml`). Key categories:

- **F**: Pyflakes (basic Python errors)
- **E, W**: Pycodestyle (PEP 8 style)
- **I**: Import sorting (isort replacement)
- **N**: PEP 8 naming conventions
- **UP**: Python upgrade suggestions
- **S**: Security checks (bandit)
- **B**: Bugbear (likely bugs)
- **DJ**: Django-specific checks
- **PLR, PLC**: Pylint rules
- **RUF**: Ruff-specific rules

### Ignored Rules

These rules are explicitly ignored in the configuration:

- **S101**: Use of assert (allowed in tests)
- **RUF012**: Mutable class attributes (false positives with Django)
- **SIM102**: Nested conditionals sometimes preferred
- **PLR2004**: Magic values (test status codes acceptable)
- **RUF005**: Iterable unpacking (false positive with Wagtail patterns)
- **PLC0415**: Top-level imports (lazy imports allowed for performance)
- **S106**: Hardcoded passwords (false positive in test fixtures)
- **DTZ011**: date.today() without timezone (acceptable in tests)

### Common Ruff Errors and Fixes

#### PLR2004: Magic Value Used in Comparison

**Problem:**
```python
if len(text) > 50:
    return text[:50]

assert response.status_code == 200
```

**Solution - Use Constants:**
```python
PREVIEW_LENGTH = 50

if len(text) > PREVIEW_LENGTH:
    return text[:PREVIEW_LENGTH]

# For HTTP status codes in tests - this is IGNORED, but good practice:
from http import HTTPStatus
assert response.status_code == HTTPStatus.OK
```

**Note:** PLR2004 is ignored for tests, but using `http.HTTPStatus` is still recommended.

#### RUF005: Consider Iterable Unpacking

**Problem:**
```python
content_panels = Page.content_panels + [
    FieldPanel("intro"),
]
```

**Solution - THIS IS IGNORED for Wagtail:**
```python
# This pattern is ACCEPTABLE in Wagtail code
content_panels = Page.content_panels + [
    FieldPanel("intro"),
]
```

**Why:** RUF005 is explicitly ignored because Wagtail patterns require concatenation. The linter suggestion to use unpacking (`[*Page.content_panels, FieldPanel("intro")]`) doesn't work well with Wagtail.

#### PLC0415: Import Should Be at Top-Level

**Problem:**
```python
def get_context(self, request):
    from .forms import CommentForm  # Import inside function
    ...
```

**Solution - THIS IS IGNORED When Necessary:**
```python
# Top-level import (preferred):
from .forms import CommentForm

class MyView:
    def get_context(self, request):
        ...

# BUT lazy imports are ALLOWED for:
# - Circular import resolution
# - Performance optimization
# - Dynamic imports
def get_context(self, request):
    from .forms import CommentForm  # OK if needed for circular imports
    ...
```

#### S106: Possible Hardcoded Password

**Problem:**
```python
User.objects.create_user(
    username="testuser",
    password="testpass123",  # Flagged as hardcoded
)
```

**Solution - THIS IS IGNORED in Test Files:**
```python
# In test fixtures/conftest.py - this is ACCEPTABLE:
@pytest.fixture
def user():
    return User.objects.create_user(
        username="testuser",
        password="testpass123",  # OK in tests
    )

# In production code - use environment variables:
import os
password = os.environ.get("USER_PASSWORD")
```

#### DTZ011: datetime.date.today() Without Timezone

**Problem:**
```python
from datetime import date

blog_post = BlogPage(
    date=date.today(),  # Flagged
)
```

**Solution - THIS IS IGNORED in Test Files:**
```python
# In test fixtures - this is ACCEPTABLE:
from datetime import date

@pytest.fixture
def blog_post():
    return BlogPage(
        date=date.today(),  # OK in tests
    )

# In production code - use timezone-aware:
from django.utils import timezone

blog_post = BlogPage(
    date=timezone.now().date(),
)
```

### Import Sorting (isort)

Ruff enforces single-line imports:

```python
# CORRECT:
from django.conf import settings
from django.contrib import admin
from django.db import models

# WRONG:
from django.conf import settings
from django.contrib import admin, messages
from django.db import models
```

Configuration in `pyproject.toml`:
```toml
[tool.ruff.lint.isort]
force-single-line = true
```

## Django Template Linting (djLint)

### Configuration

From `pyproject.toml`:
```toml
[tool.djlint]
blank_line_after_tag = "load,extends"
close_void_tags = true
format_css = true
format_js = true
ignore = "H006,H030,H031,T002,T003,D018"
include = "H017,H035"
indent = 2
max_line_length = 119
profile = "django"
```

### Template Standards

#### Indentation

```django
{# CORRECT: 2-space indentation #}
{% extends "base.html" %}

{% block content %}
  <div class="container">
    <h1>{{ title }}</h1>
    {% if user.is_authenticated %}
      <p>Welcome, {{ user.username }}!</p>
    {% endif %}
  </div>
{% endblock %}
```

#### Blank Lines

```django
{# CORRECT: Blank line after load and extends #}
{% extends "base.html" %}

{% load static %}

{% block content %}
  ...
{% endblock %}
```

#### Void Tag Closing

```django
{# CORRECT: Close void tags #}
<img src="{% static 'image.jpg' %}" alt="Description" />
<br />
<hr />

{# WRONG: #}
<img src="{% static 'image.jpg' %}" alt="Description">
<br>
```

## Python Code Standards

### Code Formatting

Ruff format follows Black-compatible style:

```python
# Line length: 88 characters (default for ruff format)
# But djLint uses 119 for templates

# Strings: Double quotes preferred
message = "Hello, world!"

# Trailing commas in multi-line structures:
items = [
    "first",
    "second",
    "third",
]
```

### Type Hints

While not currently enforced (ANN rules commented out), consider adding them:

```python
from django.http import HttpRequest, HttpResponse

def my_view(request: HttpRequest) -> HttpResponse:
    ...
```

### Docstrings

```python
def complex_function(param1: str, param2: int) -> dict:
    """
    Brief description of the function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
    ...
```

## Django and Wagtail Specific Patterns

### Migrations

Migrations are excluded from linting:
```toml
extend-exclude = [
    "*/migrations/*.py",
    "staticfiles/*",
]
```

Never manually edit migration files except to resolve conflicts.

### Wagtail Panel Definitions

**CORRECT Pattern (RUF005 ignored):**
```python
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page

class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    # This pattern is ACCEPTABLE
    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]
```

### Django Settings

Use environment variables for sensitive data:

```python
import environ

env = environ.Env()

# CORRECT:
SECRET_KEY = env("DJANGO_SECRET_KEY")
DATABASE_PASSWORD = env("POSTGRES_PASSWORD")

# WRONG:
SECRET_KEY = "***NEVER-PUT-REAL-SECRETS-HERE***"  # Never hardcode!
```

### Model Best Practices

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

class BlogPost(models.Model):
    """Model representing a blog post."""

    # Use verbose_name for better admin display
    title = models.CharField(
        _("title"),
        max_length=200,
        help_text=_("The title of the blog post"),
    )

    # Always set blank and null explicitly
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Optional description"),
    )

    # Use auto_now_add and auto_now for timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("blog post")
        verbose_name_plural = _("blog posts")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
```

### Views

```python
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

@login_required
def blog_post_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Display a single blog post."""
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect("blog:post-detail", pk=post.pk)
    else:
        form = CommentForm()

    context = {
        "post": post,
        "form": form,
    }
    return render(request, "blog/post_detail.html", context)
```

### Forms and Crispy Forms Integration

#### Django-ReCAPTCHA v3 with Crispy Forms

When using `django-recaptcha` with `ReCaptchaV3` widget and `crispy-forms`, follow this pattern to ensure forms submit correctly:

**Problem:** By default, `{% crispy form %}` renders a complete `<form>` element including opening and closing tags. If you place a submit button after `{% crispy form %}`, the button will be **outside** the form element, causing form submissions to fail silently.

**Solution:** Use `FormHelper` with `form_tag=False` to render only the form fields, then manually wrap them in `<form>` tags with your button inside.

##### Step 1: Configure FormHelper in Form Class

```python
from allauth.account.forms import SignupForm
from crispy_forms.helper import FormHelper
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3


class UserSignupForm(SignupForm):
    """Form for user signup with reCAPTCHA v3."""

    captcha = ReCaptchaField(
        widget=ReCaptchaV3(attrs={"data-action": "signup"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure helper to NOT render <form> tags
        self.helper = FormHelper()
        self.helper.form_tag = False  # Critical: prevents crispy from rendering form tags
```

##### Step 2: Use Manual Form Tags in Template

```django
{% load crispy_forms_tags %}

{{ form.media }}  {# Critical: renders reCAPTCHA widget JavaScript #}
<form method="post" action="{% url 'account_signup' %}">
  {% csrf_token %}
  {% crispy form %}  {# Renders only fields, no <form> tags #}
  <button type="submit" class="btn btn-primary">Sign Up</button>
</form>
```

##### Why This Works

1. **`{{ form.media }}`**: Renders the JavaScript required by `ReCaptchaV3` widget. Without this, the reCAPTCHA widget won't initialize and forms will fail silently.

2. **`FormHelper.form_tag = False`**: Tells crispy-forms to render only the form fields (input elements, labels, errors) without wrapping them in `<form>` tags.

3. **Manual `<form>` tags**: You control the form wrapper, ensuring the submit button is placed **inside** the form element. This is required for the submit event to fire correctly.

4. **Button placement**: The submit button must be inside the `<form>` element for the form's submit event listener to capture button clicks.

##### Common Mistakes

**❌ DON'T:**
```django
{# BAD: Button is outside the form element #}
{{ form.media }}
{% crispy form %}  {# This renders <form>...</form> completely #}
<button type="submit">Submit</button>  {# This is OUTSIDE the form! #}
```

**✅ DO:**
```django
{# GOOD: Button is inside manual form tags #}
{{ form.media }}
<form method="post">
  {% csrf_token %}
  {% crispy form %}  {# form_tag=False means only fields rendered #}
  <button type="submit">Submit</button>  {# Inside the form ✓ #}
</form>
```

##### Verification in Browser DevTools

To verify the fix works:
```javascript
// In browser console:
const form = document.querySelector('form');
const button = document.querySelector('button[type="submit"]');
console.log(form.contains(button));  // Should return true
```

If `form.contains(button)` returns `false`, the button is outside the form and submissions won't work.

## Pre-commit Hooks

### Configured Hooks

From `.pre-commit-config.yaml`:

1. **pre-commit-hooks**: Basic checks
   - Trailing whitespace removal
   - End-of-file fixer
   - JSON, TOML, YAML validation
   - Debug statement detection
   - Private key detection

2. **django-upgrade**: Upgrades Django syntax to 5.2

3. **ruff-pre-commit**: Python linting and formatting
   - `ruff-check`: Linting with auto-fix
   - `ruff-format`: Code formatting

4. **djLint**: Django template linting and formatting
   - `djlint-reformat-django`: Format templates
   - `djlint-django`: Lint templates

### Running Specific Hooks

```bash
# Run only ruff checks
pre-commit run ruff-check --all-files

# Run only formatting
pre-commit run ruff-format --all-files
pre-commit run djlint-reformat-django --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

### Updating Hooks

```bash
pre-commit autoupdate
```

## EditorConfig Standards

The project uses `.editorconfig` for consistent formatting across editors:

### Python Files (*.py)
- Charset: utf-8
- End of line: LF
- Indent style: space
- Indent size: 4
- Insert final newline: true
- Trim trailing whitespace: true

### HTML, CSS, JSON, YAML, TOML
- Indent style: space
- Indent size: 2

### Makefile
- Indent style: tab

**Ensure your editor respects EditorConfig settings.**

## Common Mistakes to Avoid

### 1. Not Running Linters Before Committing

```bash
# ALWAYS run before commit:
pre-commit run --all-files
```

### 2. Using Concatenation for Test Status Codes

```python
# DON'T WORRY - PLR2004 is ignored for these patterns
# But consider using HTTPStatus for clarity:
from http import HTTPStatus

# Good practice (even though not required):
assert response.status_code == HTTPStatus.OK  # 200
assert response.status_code == HTTPStatus.FOUND  # 302
```

### 3. Ignoring Import Order

```python
# WRONG:
from django.contrib import admin, messages
from .models import BlogPost
import os

# CORRECT:
import os

from django.contrib import admin
from django.contrib import messages

from .models import BlogPost
```

### 4. Not Using Lazy Imports When Needed

```python
# If you get circular import errors, use lazy imports:
def get_form_class(self):
    from .forms import MyForm  # OK - avoids circular import
    return MyForm
```

### 5. Hardcoding Secrets in Production Code

```python
# WRONG (production):
API_KEY = "***NEVER-PUT-REAL-KEYS-HERE***"

# CORRECT:
import os
API_KEY = os.environ.get("API_KEY")
```

### 6. Modifying Working Code Unnecessarily

When adding new features:
- Only modify files that need changes
- Don't "fix" unrelated code
- Don't reformat files unless making substantive changes

### 7. Template Formatting Issues

```django
{# WRONG: Missing blank line after extends #}
{% extends "base.html" %}
{% load static %}

{# CORRECT: Blank line after extends #}
{% extends "base.html" %}

{% load static %}

{# WRONG: Unclosed void tags #}
<img src="image.jpg">
<br>

{# CORRECT: Close void tags #}
<img src="image.jpg" />
<br />
```

## Quick Reference Commands

```bash
# Install dependencies
uv sync

# Install pre-commit hooks
pre-commit install

# Run all linters
pre-commit run --all-files

# Run specific linters
ruff check .
ruff format .
djlint --lint .

# Auto-fix issues
ruff check --fix .
djlint --reformat .

# Run tests
# If using virtualenvwrapper:
workon squeaky_knees
pytest

# Or directly:
pytest

# Run specific test files:
pytest tests/test_blog_search.py
pytest tests/test_url_routing.py

# Run with verbose output:
pytest -v

# Check migrations
python manage.py makemigrations --check

# Run Django development server
python manage.py runserver
```

## CI Pipeline

The GitHub Actions CI pipeline runs:

1. **Linter Job**:
   - Runs all pre-commit hooks
   - Fails if any linting errors exist

2. **Pytest Job**:
   - Checks for new migrations
   - Runs database migrations
   - Executes all tests

**Both jobs must pass before merging.**

## Troubleshooting

### Ruff Errors Won't Fix

```bash
# Try unsafe fixes (use with caution)
ruff check --fix --unsafe-fixes .

# Check specific file
ruff check squeaky_knees/blog/models.py --show-fixes
```

### Pre-commit Hook Fails

```bash
# Clear pre-commit cache
pre-commit clean

# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Import Sorting Issues

```bash
# Let ruff handle it
ruff check --select I --fix .
```

## Summary

To ensure your code passes CI:

1. ✅ Run `pre-commit run --all-files` before committing
2. ✅ Use constants for magic values (or accept PLR2004 in tests)
3. ✅ Keep imports single-line and sorted
4. ✅ Don't worry about RUF005 with Wagtail patterns (it's ignored)
5. ✅ Lazy imports are OK when needed (PLC0415 ignored)
6. ✅ Hardcoded test passwords are OK (S106 ignored in tests)
7. ✅ Format templates with 2-space indentation
8. ✅ Close void tags in HTML templates
9. ✅ Add blank lines after `{% extends %}` and `{% load %}`
10. ✅ Never commit secrets or API keys

Following these guidelines will help prevent the linting errors that have caused recent CI failures.
