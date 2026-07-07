# Code Review & Cross-Port — July 7, 2026

Evaluation of squeaky_knees plus a two-way port with tabitha_talking. **All 431 tests (+12 subtests) pass** after the changes, verified on a fresh database with the upgraded dependencies, plus an end-to-end smoke test covering every route, the login page, and the comment submission/moderation flow. `ruff`, `djlint`, `manage.py check`, and `makemigrations --check` are clean.

## Evaluation of squeaky_knees

The feature work here is solid: nested comments with moderation and email notifications, allauth accounts with MFA and mandatory email verification, a custom CodeBlock, comment rate limiting + reCAPTCHA, and an unusually thorough test suite (431 tests). The Wagtail routing fixes in recent commits (mount at root, Site migration, blog_view cleanup) were already mirrored in tabitha_talking, so there was less to port back than expected — the two codebases had mostly diverged by *features*, not fixes. The main issues found were the same family of bugs fixed on the wife's site last session (it inherited them from here), and dependencies that had fallen behind (Django 5 security patches behind; Wagtail 6.4 out of support).

## Ported here from tabitha_talking

**Dependencies** (uv.lock regenerated; test suite + fresh-DB migrations verify the jump):

| Package | Was | Now |
|---|---|---|
| django | 5.2.10 | **5.2.15** (5 security patches) |
| wagtail | 6.4.2 | **7.4.2 (LTS**, supported to Nov 2027; 6.4 was out of support) |
| django-allauth | 65.14.0 | 65.18.0 |
| pillow / gunicorn / sentry-sdk | 11.3 / 24.1.1 / 2.50 | 12.3 / 26.0 / 2.64 |
| crispy-forms / crispy-bootstrap5 / environ / recaptcha / hiredis / psycopg | — | minor bumps |
| django-model-utils | 5.0.0 | **removed** (unused) |

Held back deliberately (production-only, untestable here — upgrade one at a time watching Sentry): django-anymail 14→15, django-redis 6→7, redis 7→8.

**Bug fixes**

- Search results never showed dates/intros (`result.blogpage.date` doesn't exist on BlogPage results; Django templates fail silently). Fixed in `search_results.html`.
- Mailgun (`AnymailError`) failures were uncaught in the contact view **and both comment-notification helpers** (`blog/email.py`) — only `OSError` (SMTP) was handled, so a Mailgun outage meant a 500 on contact and on comment submission. Now caught.
- RSS feed exposed the post owner's email address publicly; removed.
- Sitemap was missing the homepage and /about/; added.
- Blog search now filters `.public()` pages like the tag search already did.
- Deleted dead `contrib/recaptcha.py` (+ widgets): unused, and it referenced settings that don't exist, so it would have crashed if ever called.
- `WAGTAILADMIN_BASE_URL` now set in production (was localhost — CMS notification emails/preview links pointed to the wrong host).
- `.dockerignore` now excludes `.envs/` (local env files were being copied into the image).

**Performance (low-memory Droplet)**

- Blog index N+1 removed: direct `BlogPage.objects.child_of(...).select_related("header_image")` instead of `get_children().specific()` + per-post image queries. Root comments also `select_related("author")`.
- Header images render as Wagtail renditions (`fill-800x450` / `width-1000`) instead of original multi-MB uploads.
- Response caching: home 5 min, sitemap/feed 1 h (robots was already 24 h). Safe with logged-in users: `Vary: Cookie` gives each session its own entry.
- Gunicorn: 1 worker + 4 threads (a slow Mailgun call no longer blocks every visitor), `--max-requests 1000` worker recycling, heartbeat in `/dev/shm`.
- Dockerfile: multi-stage — compilers stay in the builder; runtime carries only `libpq` + `gettext`. **Validate with one CI build before relying on it.**

**Structure & editor QoL**

- Page-tree rules: `BlogPage` only under `BlogIndexPage`; one blog index max. Posts can no longer be created somewhere that silently drops them from the index/feed.
- `{% wagtailuserbar %}` in base.html — logged-in editors get the Wagtail quick-edit bar.
- Tag badges on posts now link to tag search (they were inert `<span>`s here; the search view already existed).
- URL-resolution-order documentation in `config/urls.py`.
- Autouse cache-clearing test fixtures (required now that views are cached).

## New in both sites (per your choice)

Blog post bodies gained **image** and **video-embed** blocks (`blog/migrations/0008` here, `0003` on tabitha_talking). Images render as 800-px renditions via `blog/blocks/image_block.html`; embeds accept YouTube/Vimeo URLs. CodeBlock remains squeaky_knees-only — no obvious use on a voice-acting blog.

## Ported to tabitha_talking from here

Less than expected: your recent routing fixes (Wagtail mounted at root, Site data migration, blog_view cleanup) had already been carried over before last session. The `/about/`-as-named-route pattern was deliberately **not** ported — on her site About is a Wagtail page she can edit in the CMS, which is the better fit (her one failing test came from copying this repo's `reverse("about")` test without that context). The homepage tag-links idea is nice and would transfer easily if she ever wants it; skipped as a content decision.

## Suggestions (not implemented)

- `blog/email.py` builds admin links from a `SITE_URL` setting that isn't defined (falls back to localhost). Point it at `WAGTAILADMIN_BASE_URL` when convenient.
- Comment threads render replies recursively (one query per reply). Fine at current volume; if a post ever gets hundreds of comments, fetch the whole thread in one query and nest in Python.
- Same notes as her site: HSTS still 60 s (the TODO.md tracker already flags it), X-XSS-Protection header is obsolete but pinned by tests, rate limiter trusts `X-Forwarded-For` (fine behind Traefik).
- allauth `ACCOUNT_ALLOW_REGISTRATION` defaults to True — if comment spam signups ever become a nuisance, it's env-toggleable without a deploy.
