# Deployment Guide

## DigitalOcean Droplet Deployment

This project uses GitHub Actions for CI/CD to deploy to a DigitalOcean Droplet.

### Prerequisites

1. **DigitalOcean Droplet** with Docker installed
2. **DigitalOcean Container Registry** (DOCR)
3. **GitHub Secrets** configured

### Required GitHub Secrets

Configure these in your GitHub repository settings under `Settings > Secrets and variables > Actions`:

#### Environment Setup

**Important**: Create a GitHub Actions Environment named `DigitalOcean` for deployment secrets:

1. Go to `Settings > Environments`
2. Click `New environment`
3. Name it: `DigitalOcean`
4. Add the secrets below to this environment

#### Secrets Table

| Secret | Description | Example |
|--------|-------------|---------|
| `DO_TOKEN` | DigitalOcean API token | `dop_v1_...` |
| `REGISTRY_NAME` | Your DOCR registry name | `my-registry` |
| `DROPLET_HOST` | Droplet IP address | `157.230.x.x` |
| `DROPLET_USER` | SSH user (usually `root`) | `root` |
| `SSH_PRIVATE_KEY` | SSH private key for droplet access | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

**Note**: All of the above secrets should be added to the `DigitalOcean` environment. The deploy workflow is configured to use secrets from this environment.

### Droplet Setup

#### 1. Install Docker

```bash
# Update package list
apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify installation
docker --version
```

#### 2. Create Docker Network

```bash
docker network create squeaky_knees_network
```

#### 3. Set Up PostgreSQL Container

```bash
# Create volume for data persistence
docker volume create postgres_data

# Run PostgreSQL container
docker run -d \
  --name postgres \
  --restart unless-stopped \
  --network squeaky_knees_network \
  -v postgres_data:/var/lib/postgresql/data \
  -e POSTGRES_DB=squeaky_knees \
  -e POSTGRES_USER=squeaky_knees \
  -e POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE> \
  postgres:16
```

#### 4. Create Environment Files

Create the `.envs/.production/` directory structure locally, then transfer via FileZilla:

```bash
# Create directory structure on droplet
mkdir -p /opt/squeaky_knees/.envs/.production
```

**Using FileZilla to Transfer Environment Files:**

1. Connect to your droplet via SFTP:
   - Host: `sftp://your-droplet-ip`
   - Port: `22`
   - Username: `root` (or your SSH user)
   - Password: Your SSH key or password

2. Create `.django` file locally with these settings:
```
# Django Settings
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

# Static/Media (if using S3)
DJANGO_AWS_ACCESS_KEY_ID=<YOUR_AWS_KEY>
DJANGO_AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET>
DJANGO_AWS_STORAGE_BUCKET_NAME=squeaky-knees-static
```

3. Create `.postgres` file locally with these settings:
```
# PostgreSQL Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=squeaky_knees
POSTGRES_USER=squeaky_knees
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>
DATABASE_URL=postgres://squeaky_knees:<PASSWORD>@postgres:5432/squeaky_knees
```

4. Transfer both files to `/opt/squeaky_knees/.envs/.production/` via FileZilla

5. Set proper permissions on the droplet:
```bash
chmod 600 /opt/squeaky_knees/.envs/.production/.django
chmod 600 /opt/squeaky_knees/.envs/.production/.postgres
```

**Note**: The project uses a nested `.envs` structure:
- `.envs/.local/.django` and `.envs/.local/.postgres` for local development
- `.envs/.production/.django` and `.envs/.production/.postgres` for production

#### 5. Set Up Nginx (Reverse Proxy)

Install and configure Nginx:

```bash
apt-get install -y nginx certbot python3-certbot-nginx

# Create Nginx config
cat > /etc/nginx/sites-available/squeaky_knees << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/squeaky_knees/static/;
    }

    location /media/ {
        alias /var/www/squeaky_knees/media/;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/squeaky_knees /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Test and reload
nginx -t
systemctl reload nginx

# Get SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### CI/CD Workflow

The deployment happens automatically on push to `main`:

1. **CI Workflow** (`.github/workflows/ci.yml`):
   - Runs linting (pre-commit)
   - Runs tests with PostgreSQL
   - Checks migrations

2. **Deploy Workflow** (`.github/workflows/deploy.yml`):
   - Uses secrets from the `DigitalOcean` GitHub environment
   - Builds Docker image
   - Pushes to DigitalOcean Container Registry
   - SSHs to droplet
   - Pulls latest image
   - Runs migrations
   - Restarts container
   - Verifies deployment

**Important**: The deploy workflow requires the `DigitalOcean` environment to be configured with the deployment secrets. Without it, the workflow will fail with "token: Input required and not supplied".

### Manual Deployment

If you need to deploy manually:

```bash
# SSH to droplet
ssh root@<DROPLET_IP>

# Pull latest image
docker login -u <DO_TOKEN> -p <DO_TOKEN> registry.digitalocean.com
docker pull registry.digitalocean.com/<REGISTRY_NAME>/squeaky-knees:latest

# Stop old container
docker stop squeaky-knees
docker rm squeaky-knees

# Run migrations
docker run --rm \
  --env-file /opt/squeaky_knees/.envs/.production/.django \
  --env-file /opt/squeaky_knees/.envs/.production/.postgres \
  --network squeaky_knees_network \
  registry.digitalocean.com/<REGISTRY_NAME>/squeaky-knees:latest \
  uv run python manage.py migrate --noinput

# Start new container
docker run -d \
  --name squeaky-knees \
  --restart unless-stopped \
  --env-file /opt/squeaky_knees/.envs/.production/.django \
  --env-file /opt/squeaky_knees/.envs/.production/.postgres \
  --network squeaky_knees_network \
  -p 8000:8000 \
  registry.digitalocean.com/<REGISTRY_NAME>/squeaky-knees:latest
```

### Troubleshooting

#### View container logs
```bash
docker logs -f squeaky-knees
```

#### Access container shell
```bash
docker exec -it squeaky-knees /bin/bash
```

#### Check database connection
```bash
docker exec -it postgres psql -U squeaky_knees -d squeaky_knees
```

#### Rebuild and restart
```bash
docker stop squeaky-knees
docker rm squeaky-knees
docker rmi registry.digitalocean.com/<REGISTRY_NAME>/squeaky-knees:latest
# Then re-pull and start
```

### Maintenance

#### Database Backups

```bash
# Create backup
docker exec postgres pg_dump -U squeaky_knees squeaky_knees > backup_$(date +%Y%m%d).sql

# Restore backup
docker exec -i postgres psql -U squeaky_knees squeaky_knees < backup_20260131.sql
```

#### Update Dependencies

1. Update `pyproject.toml` locally
2. Run `uv lock`
3. Commit and push - CI/CD will deploy

#### Clean Up Docker Resources

```bash
# Remove unused images
docker image prune -af

# Remove unused volumes
docker volume prune -f
```

## Security Checklist

- [ ] Strong `DJANGO_SECRET_KEY` generated
- [ ] Database password is strong
- [ ] `DJANGO_DEBUG=False` in production
- [ ] `DJANGO_SECURE_SSL_REDIRECT=True`
- [ ] SSL certificate installed (certbot)
- [ ] Firewall configured (only ports 80, 443, 22)
- [ ] SSH key authentication only (disable password auth)
- [ ] Regular security updates (`apt-get update && apt-get upgrade`)
- [ ] Environment file permissions restricted (`chmod 600 .envs/.production/*`)
- [ ] reCAPTCHA keys configured
- [ ] Email service configured for notifications

## Monitoring

Consider adding:
- DigitalOcean Monitoring (built-in)
- Sentry for error tracking
- Uptime monitoring (UptimeRobot, etc.)
- Log aggregation (Papertrail, etc.)
