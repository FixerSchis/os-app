# Deployment Guide

This guide explains how to set up Continuous Deployment (CD) for the OS App Flask application.

## Overview

The CD pipeline automatically deploys your application to a production server whenever code is pushed to the `master` branch and the CI pipeline passes successfully.

## Architecture

```
GitHub Repository
       ↓
   CI Pipeline (tests, linting, security)
       ↓
   CD Pipeline (deployment)
       ↓
   Production Server (Debian)
       ↓
   Nginx (reverse proxy)
       ↓
   Gunicorn (WSGI server)
       ↓
   Flask Application
```

## Prerequisites

### Server Requirements

- **OS**: Debian 11+ or Ubuntu 20.04+
- **Python**: 3.10+
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 10GB+ free space
- **Network**: Public IP or domain name

### Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-venv python3-pip nginx supervisor git curl
```

## Setup Instructions

### 1. Server Preparation

Run the automated setup script on your production server:

```bash
# Clone the repository (temporarily)
git clone <your-repo-url>
cd os-app

# Run the setup script
python3 scripts/setup_production_server.py
```

This script will:
- Check system requirements
- Create a deployment user
- Set up necessary directories
- Configure Nginx
- Generate SSH keys
- Create environment templates

### 2. Manual Server Setup (Alternative)

If you prefer to set up manually:

#### Create Deployment User

```bash
sudo useradd -m -s /bin/bash os-app
sudo usermod -aG sudo os-app
```

#### Set Up Directories

```bash
sudo mkdir -p /opt/os-app
sudo mkdir -p /opt/backups/os-app
sudo mkdir -p /var/log/os-app
sudo chown os-app:os-app /opt/os-app /opt/backups/os-app /var/log/os-app
```

#### Generate SSH Key

```bash
sudo -u os-app ssh-keygen -t ed25519 -f /home/os-app/.ssh/os-app-deploy -N ''
sudo -u os-app cat /home/os-app/.ssh/os-app-deploy.pub
```

#### Configure Nginx

Create `/etc/nginx/sites-available/os-app`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/os-app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /data {
        alias /opt/os-app/data;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:

```bash
sudo ln -sf /etc/nginx/sites-available/os-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. GitHub Repository Configuration

#### Add Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

1. **DEPLOY_HOST**: Your server's IP address or domain
2. **DEPLOY_USER**: The deployment username (e.g., `os-app`)
3. **DEPLOY_SSH_KEY**: The private SSH key content (from `/home/os-app/.ssh/os-app-deploy`)
4. **DEPLOY_PORT**: SSH port (default: `22`)

#### Get SSH Private Key

```bash
sudo cat /home/os-app/.ssh/os-app-deploy
```

Copy the entire output (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`).

### 4. Environment Configuration

Create and configure your `.env` file on the server:

```bash
sudo -u os-app nano /opt/os-app/.env
```

Example configuration:

```env
# Database Configuration
DATABASE_URL=sqlite:///os_app.db
# For PostgreSQL: postgresql://username:password@localhost/os_app

# Flask Configuration
SECRET_KEY=your-very-secure-secret-key-here
FLASK_ENV=production
FLASK_APP=app.py

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security
WTF_CSRF_ENABLED=True
SESSION_COOKIE_SECURE=True
REMEMBER_COOKIE_SECURE=True

# Application Settings
UPLOAD_FOLDER=/opt/os-app/uploads
MAX_CONTENT_LENGTH=16777216
```

### 5. SSL Setup (Optional but Recommended)

Install Certbot and get SSL certificate:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## How the CD Pipeline Works

### Trigger Conditions

The deployment is triggered when:
1. Code is pushed to the `master` branch
2. The CI pipeline completes successfully
3. All tests pass
4. Code quality checks pass

### Deployment Process

1. **Package Creation**: Creates a deployment archive excluding development files
2. **Backup**: Creates a backup of the current deployment
3. **Deployment**: Extracts new code and sets up the environment
4. **Database Migration**: Runs any pending database migrations
5. **Service Restart**: Restarts the application service
6. **Health Check**: Verifies the service is running correctly

### Rollback

If deployment fails, the pipeline will:
1. Stop the deployment process
2. Keep the previous version running
3. Log the error for debugging

Manual rollback is also available:

```bash
# On the server
sudo systemctl stop os-app
cd /opt/backups/os-app
sudo tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz -C /opt/
sudo systemctl start os-app
```

## Monitoring and Maintenance

### Service Management

```bash
# Check service status
sudo systemctl status os-app

# View logs
sudo journalctl -u os-app -f

# Restart service
sudo systemctl restart os-app

# Enable/disable auto-start
sudo systemctl enable os-app
sudo systemctl disable os-app
```

### Log Files

- **Application logs**: `/var/log/os-app/`
- **Nginx logs**: `/var/log/nginx/`
- **System logs**: `sudo journalctl -u os-app`

### Backup Management

Backups are automatically created before each deployment and stored in `/opt/backups/os-app/`. The system keeps the last 5 backups.

### Database Management

```bash
# Run migrations manually
cd /opt/os-app
source venv/bin/activate
export FLASK_APP=app.py
flask db upgrade

# Create database backup
sqlite3 os_app.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"
```

## Troubleshooting

### Common Issues

#### Deployment Fails

1. **Check GitHub Actions logs** for specific error messages
2. **Verify SSH connectivity**:
   ```bash
   ssh -i /path/to/key os-app@your-server
   ```
3. **Check server logs**:
   ```bash
   sudo journalctl -u os-app -n 50
   ```

#### Service Won't Start

1. **Check configuration**:
   ```bash
   sudo systemctl status os-app
   ```
2. **Verify environment variables**:
   ```bash
   sudo -u os-app cat /opt/os-app/.env
   ```
3. **Check file permissions**:
   ```bash
   ls -la /opt/os-app/
   ```

#### Database Issues

1. **Check database file permissions**:
   ```bash
   ls -la /opt/os-app/os_app.db
   ```
2. **Run migrations manually**:
   ```bash
   cd /opt/os-app
   source venv/bin/activate
   flask db upgrade
   ```

### Performance Optimization

#### Gunicorn Configuration

Edit the systemd service file to optimize Gunicorn:

```bash
sudo nano /etc/systemd/system/os-app.service
```

Recommended settings for a 2GB server:
```ini
ExecStart=/opt/os-app/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:8000 --timeout 120 app:app
```

#### Nginx Optimization

Add to your Nginx configuration:

```nginx
# Enable gzip compression
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# Increase client body size for file uploads
client_max_body_size 16M;
```

## Security Considerations

### Firewall Configuration

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /opt/os-app
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Monitoring

Consider setting up monitoring tools:
- **Log monitoring**: `logwatch` or `fail2ban`
- **System monitoring**: `htop`, `iotop`
- **Application monitoring**: Custom health check endpoints

## Support

For issues with the deployment:

1. Check the GitHub Actions logs
2. Review server logs
3. Verify configuration files
4. Test SSH connectivity
5. Check service status

The deployment pipeline includes comprehensive logging to help diagnose issues quickly.
