# Production Deployment Checklist

Use this checklist for a clean, minimal production setup.

## Local Preparation

- [ ] Set `DJANGO_ALLOWED_HOSTS` in `.envs/.production/.django`
- [ ] Generate strong `DJANGO_SECRET_KEY`
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure email + reCAPTCHA keys
- [ ] Create `.envs/.production/.django`
- [ ] Create `.envs/.production/.postgres`

## Droplet

- [ ] Install Docker
- [ ] Create directories:
  ```bash
  mkdir -p /opt/squeaky_knees/.envs/.production
  ```
- [ ] Copy env files and lock permissions:
  ```bash
  scp .envs/.production/.django root@<DROPLET_IP>:/opt/squeaky_knees/.envs/.production/
  scp .envs/.production/.postgres root@<DROPLET_IP>:/opt/squeaky_knees/.envs/.production/
  ssh root@<DROPLET_IP>
  chmod 600 /opt/squeaky_knees/.envs/.production/*
  ```

## DNS

- [ ] A record for `@` → `<DROPLET_IP>`
- [ ] A record for `www` → `<DROPLET_IP>`

## AWS S3 (Optional)

- [ ] Create S3 bucket
- [ ] Create IAM user with S3 access
- [ ] Add S3 credentials to `.django`
- [ ] Apply public read bucket policy

## Deploy

- [ ] Clone repo to `/opt/squeaky_knees`
- [ ] Create `/opt/squeaky_knees/.env`, optionally with `ACME_EMAIL`
- [ ] `docker-compose -f docker-compose.production.yml up -d`
- [ ] Run migrations
- [ ] Create superuser (optional)

## Verify

- [ ] HTTPS works in browser
- [ ] Admin login works
- [ ] Static files load
