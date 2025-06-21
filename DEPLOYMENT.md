# Orion Sphere LRP Linux Deployment Guide

This guide provides comprehensive instructions for deploying the Orion Sphere LRP application on Linux servers using our automated deployment script.

## Quick Start

### Prerequisites

- **Linux server** with systemd (Ubuntu 20.04+, CentOS 7+, RHEL 7+, etc.)
- **Python 3.10 or higher**
- **Root access** (or sudo privileges)
- **Git** installed

### Automated Deployment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/os-app.git
   cd os-app
   ```

2. **Run the deployment script:**
   ```bash
   sudo ./deploy.sh deploy
   ```

3. **Configure your environment:**
   ```bash
   sudo nano /opt/orion-sphere-lrp/.env
   ```

4. **Restart the service:**
   ```bash
   sudo systemctl restart orion-sphere-lrp
   ```

That's it! Your application should now be running on `http://your-server-ip:5000`

## Detailed Instructions

### Step 1: Server Preparation

#### System Requirements
- **OS:** Linux with systemd (Ubuntu 20.04+, CentOS 7+, RHEL 7+, Debian 11+)
- **Python:** 3.10 or higher
- **RAM:** Minimum 1GB, recommended 2GB+
- **Storage:** Minimum 5GB free space
- **Network:** Port 5000 accessible (or configure reverse proxy)

#### Install System Dependencies
The deployment script will automatically install required packages, but you can also install them manually:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl wget rsync
```

**CentOS/RHEL/Rocky Linux:**
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip git curl wget rsync
# or for newer versions:
sudo dnf install -y python3 python3-pip git curl wget rsync
```

### Step 2: Application Deployment

#### Fresh Installation
```bash
# Clone the repository
git clone https://github.com/your-username/os-app.git
cd os-app

# Run deployment script
sudo ./deploy.sh deploy
```

#### Update Existing Installation
```bash
# Navigate to your application directory
cd /path/to/your/app

# Pull latest changes
git pull origin master

# Run update script
sudo ./deploy.sh update
```

### Step 3: Configuration

#### Environment Variables
Edit the `.env` file with your production settings:

```bash
sudo nano /opt/orion-sphere-lrp/.env
```

**Required Configuration:**
```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-here
FLASK_DEBUG=0

# Database Configuration
DATABASE_URL=sqlite:///app.db
# For PostgreSQL: postgresql://user:password@localhost/dbname
# For MySQL: mysql://user:password@localhost/dbname

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Server Configuration
FLASK_RUN_HOST=127.0.0.1
DEFAULT_PORT=5000

# SSL Configuration (optional)
SSL_ENABLED=False
SSL_CERT_FILE=/path/to/cert.pem
SSL_KEY_FILE=/path/to/key.pem
```

#### Generate Secure Secret Key
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 4: Web Server Configuration (Optional but Recommended)

#### Nginx Configuration
Create an Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/orion-sphere-lrp
```

**Basic Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/orion-sphere-lrp/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/orion-sphere-lrp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### SSL with Let's Encrypt (Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Step 5: Service Management

#### Service Commands
```bash
# Check service status
sudo systemctl status orion-sphere-lrp

# Start service
sudo systemctl start orion-sphere-lrp

# Stop service
sudo systemctl stop orion-sphere-lrp

# Restart service
sudo systemctl restart orion-sphere-lrp

# Enable auto-start
sudo systemctl enable orion-sphere-lrp

# Disable auto-start
sudo systemctl disable orion-sphere-lrp
```

#### Log Management
```bash
# View logs
sudo journalctl -u orion-sphere-lrp

# Follow logs in real-time
sudo journalctl -u orion-sphere-lrp -f

# View recent logs
sudo journalctl -u orion-sphere-lrp -n 100

# View logs since boot
sudo journalctl -u orion-sphere-lrp -b
```

### Step 6: Backup and Maintenance

#### Automated Backups
The deployment script automatically creates backups in `/opt/backups/orion-sphere-lrp/`

**Manual backup:**
```bash
sudo ./deploy.sh backup
```

**Restore from backup:**
```bash
# Stop service
sudo systemctl stop orion-sphere-lrp

# Restore from backup
sudo cp -r /opt/backups/orion-sphere-lrp/backup-YYYYMMDD-HHMMSS/* /opt/orion-sphere-lrp/

# Fix permissions
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp

# Start service
sudo systemctl start orion-sphere-lrp
```

#### Database Backups
```bash
# SQLite backup
sudo cp /opt/orion-sphere-lrp/app.db /opt/backups/orion-sphere-lrp/app.db.backup-$(date +%Y%m%d)

# PostgreSQL backup
pg_dump your_database > /opt/backups/orion-sphere-lrp/db-backup-$(date +%Y%m%d).sql

# MySQL backup
mysqldump your_database > /opt/backups/orion-sphere-lrp/db-backup-$(date +%Y%m%d).sql
```

## Deployment Script Reference

### Available Commands
```bash
./deploy.sh deploy    # Fresh installation
./deploy.sh update    # Update existing installation
./deploy.sh status    # Show service status
./deploy.sh logs      # Show service logs
./deploy.sh backup    # Create backup
./deploy.sh help      # Show help
```

### Script Features
- **Automatic dependency installation**
- **User and group creation**
- **Virtual environment setup**
- **Systemd service installation**
- **Automatic backups**
- **Database migration handling**
- **Permission management**
- **Error handling and logging**

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status orion-sphere-lrp

# View detailed logs
sudo journalctl -u orion-sphere-lrp -n 50

# Check file permissions
ls -la /opt/orion-sphere-lrp/

# Verify environment file
sudo -u orion-sphere cat /opt/orion-sphere-lrp/.env
```

#### Permission Issues
```bash
# Fix ownership
sudo chown -R orion-sphere:orion-sphere /opt/orion-sphere-lrp

# Fix permissions
sudo chmod 755 /opt/orion-sphere-lrp
sudo chmod 600 /opt/orion-sphere-lrp/.env
```

#### Database Issues
```bash
# Check database file
ls -la /opt/orion-sphere-lrp/app.db

# Run migrations manually
cd /opt/orion-sphere-lrp
sudo -u orion-sphere venv/bin/flask db upgrade

# Check database connection
sudo -u orion-sphere venv/bin/python -c "from app import create_app; app = create_app(); print('Database OK')"
```

#### Port Conflicts
```bash
# Check what's using port 5000
sudo netstat -tlnp | grep :5000

# Change port in .env file
sudo nano /opt/orion-sphere-lrp/.env
# Set DEFAULT_PORT=8080

# Restart service
sudo systemctl restart orion-sphere-lrp
```

### Performance Optimization

#### Database Optimization
- **SQLite:** For small to medium deployments
- **PostgreSQL:** For larger deployments with concurrent users
- **MySQL:** Alternative to PostgreSQL

#### Memory Optimization
```bash
# Monitor memory usage
free -h
ps aux | grep orion-sphere

# Adjust Python memory settings in service file
sudo nano /etc/systemd/system/orion-sphere-lrp.service
# Add: Environment=PYTHONUNBUFFERED=1
```

#### Log Rotation
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/orion-sphere-lrp

# Add configuration:
/var/log/orion-sphere-lrp/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 orion-sphere orion-sphere
}
```

## Security Considerations

### Firewall Configuration
```bash
# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow application port (if not using reverse proxy)
sudo ufw allow 5000

# Enable firewall
sudo ufw enable
```

### SSL/TLS Configuration
- Always use HTTPS in production
- Configure proper SSL certificates
- Use strong cipher suites
- Enable HSTS headers

### File Permissions
- Application files: 644 (files), 755 (directories)
- Environment file: 600 (owner only)
- Database file: 600 (owner only)

### Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update application
cd /opt/orion-sphere-lrp
git pull origin master
sudo ./deploy.sh update
```

## Monitoring and Maintenance

### Health Checks
```bash
# Create health check script
sudo nano /opt/orion-sphere-lrp/health_check.sh
```

```bash
#!/bin/bash
# Health check script
curl -f http://localhost:5000/health || exit 1
```

### Automated Monitoring
```bash
# Set up cron job for health checks
sudo crontab -e
# Add: */5 * * * * /opt/orion-sphere-lrp/health_check.sh
```

### Performance Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor system resources
htop
iotop
nethogs
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the application logs
3. Check the system logs
4. Create an issue in the GitHub repository

## Contributing

To improve the deployment process:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note:** This deployment guide assumes a standard Linux environment. Adjustments may be needed for specific distributions or configurations.
