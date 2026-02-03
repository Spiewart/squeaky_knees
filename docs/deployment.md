# Deployment Guide

This guide covers the minimum steps to deploy and operate the blog in production using Docker Compose, Traefik, PostgreSQL, and optional AWS S3 for static/media files.

## Requirements

- DigitalOcean Droplet with Docker
- GitHub Container Registry (GHCR) access
- Domain name pointing to the droplet
- AWS account (only if using S3 for static/media)

## GitHub Actions Secrets

Configure these in the GitHub Actions environment named `DigitalOcean`:

| Secret | Description |
|--------|-------------|
| `DROPLET_HOST` | Droplet IP address |
| `DROPLET_USER` | SSH user (usually `root`) |
| `SSH_PRIVATE_KEY` | SSH private key for droplet access |
| `ACME_EMAIL` | Email for Let's Encrypt (optional) |

**Note**: `GITHUB_TOKEN` is provided automatically by GitHub Actions; you do not need to add it as a secret.

## Droplet Setup

### 1) Install Docker

```bash
apt-get update
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker --version
```

### 2) Create required directories

```bash
mkdir -p /opt/squeaky_knees/.envs/.production
```

## Environment Files

Create these locally and copy to the droplet.

### `.envs/.production/.django`

```
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<GENERATE_STRONG_SECRET_KEY>
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_DEBUG=False

# reCAPTCHA v3
RECAPTCHA_PUBLIC_KEY=<YOUR_RECAPTCHA_SITE_KEY>
RECAPTCHA_PRIVATE_KEY=<YOUR_RECAPTCHA_SECRET_KEY>

# Email (example with Mailgun)
DJANGO_DEFAULT_FROM_EMAIL=noreply@yourdomain.com
MAILGUN_API_KEY=<YOUR_MAILGUN_API_KEY>
MAILGUN_DOMAIN=yourdomain.com

# AWS S3 (optional)
DJANGO_AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY_ID>
DJANGO_AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_ACCESS_KEY>
DJANGO_AWS_STORAGE_BUCKET_NAME=<YOUR_BUCKET_NAME>
DJANGO_AWS_S3_REGION_NAME=us-east-1
DJANGO_AWS_S3_CUSTOM_DOMAIN=<optional: CloudFront or custom domain>
```

### `.envs/.production/.postgres`

```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=squeaky_knees
POSTGRES_USER=squeaky_knees
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>
DATABASE_URL=postgres://squeaky_knees:<PASSWORD>@postgres:5432/squeaky_knees
```

Copy to the droplet:

```bash
scp .envs/.production/.django root@<DROPLET_IP>:/opt/squeaky_knees/.envs/.production/
scp .envs/.production/.postgres root@<DROPLET_IP>:/opt/squeaky_knees/.envs/.production/
ssh root@<DROPLET_IP>
chmod 600 /opt/squeaky_knees/.envs/.production/*
```

## AWS S3 (Optional for Static/Media)

If you want static/media files on S3, do the following:

1) Create a bucket
```bash
aws s3 mb s3://<YOUR_BUCKET_NAME> --region us-east-1
```

2) Create an IAM user with S3 access (List/Get/Put/Delete) and add its keys to `.django`.

3) Make the bucket public for reads (static/media)
```bash
aws s3api put-bucket-policy --bucket <YOUR_BUCKET_NAME> --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::<YOUR_BUCKET_NAME>/*"
    }
  ]
}'
```

4) Static files are updated by the deployment workflow.

## DNS

Create A records for your domain:

| Type | Host | Value |
|------|------|-------|
| A | @ | <DROPLET_IP> |
| A | www | <DROPLET_IP> |

## Deploy

```bash
ssh root@<DROPLET_IP>
cd /opt/squeaky_knees

# Clone repo (or copy docker-compose.production.yml and compose/)
git clone <your-repo> .

# Docker Compose env
cat > /opt/squeaky_knees/.env << 'EOF'
IMAGE_NAME=your-github-username/squeaky_knees
ACME_EMAIL=your-email@example.com
EOF

# Log in and start
echo "<GHCR_TOKEN>" | docker login ghcr.io -u <GHCR_USERNAME> --password-stdin
docker-compose -f docker-compose.production.yml up -d

# Migrate
docker-compose -f docker-compose.production.yml exec web uv run python manage.py migrate --noinput

# Optional: create admin
docker-compose -f docker-compose.production.yml exec web uv run python manage.py createsuperuser

# Update static files (required if using S3)
docker-compose -f docker-compose.production.yml exec web uv run python manage.py collectstatic --noinput
```

## Operations

### View logs
```bash
docker-compose -f docker-compose.production.yml logs -f
```

### Update to latest image
```bash
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.production.yml exec web uv run python manage.py migrate --noinput
```

### Backups
```bash
docker-compose -f docker-compose.production.yml exec postgres \
  pg_dump -U squeaky_knees squeaky_knees > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Troubleshooting

- **HTTPS not working**: verify DNS points to the droplet and ports 80/443 are open.
- **502 errors**: check application logs and container health.
- **S3 403**: verify bucket policy and IAM credentials.

## Security Basics

- `DJANGO_DEBUG=False` in production
- Strong `DJANGO_SECRET_KEY` and database password
- Firewall open only on 22/80/443
- SSH key authentication only
