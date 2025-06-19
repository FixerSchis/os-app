# Linux Installation Guide for Orion Sphere LRP

This guide will help you install the Orion Sphere LRP Flask application on a Linux server with all necessary dependencies and configure it as a systemd service.

## Prerequisites

- Ubuntu 18.04+ or Debian 9+ (other distributions may work but are not tested)
- A user account with sudo privileges
- Internet connection for downloading packages

## Quick Installation

1. **Download or clone the application** to your Linux server
2. **Navigate to the application directory** (where `app.py` is located)
3. **Run the installation script**:

```bash
./install.sh
```

The script will automatically:
- Install all system dependencies (Python, nginx, etc.)
- Create a dedicated service user
- Set up a Python virtual environment
- Install Python dependencies
- Configure the application as a systemd service
- Set up nginx as a reverse proxy
- Initialize the database
- Start all services

## Handling Repository Issues (Debian/Ubuntu)

If you encounter repository timing issues like:
```
E: Release file for https://security.debian.org/debian-security/dists/bookworm-security/InRelease is not valid yet
```

This is a common issue on Debian systems. The installation script now includes retry logic, but if you continue to have problems:

### Option 1: Use the Repository Fix Script
```bash
chmod +x fix_repository_issues.sh
./fix_repository_issues.sh
```

This script will:
- Check your system time
- Clean apt cache
- Try multiple update methods
- Provide manual solutions if automatic fixes fail

### Option 2: Manual Solutions

1. **Wait for timing issues to resolve** (usually 1-3 hours)
2. **Temporarily disable problematic repositories**:
   ```bash
   sudo nano /etc/apt/sources.list.d/debian.list
   # Comment out lines with 'bookworm-security', 'bookworm-updates', etc.
   ```
3. **Use a different mirror**:
   ```bash
   sudo nano /etc/apt/sources.list
   # Replace 'ftp.debian.org' with 'deb.debian.org'
   ```
4. **Sync system time**:
   ```bash
   sudo apt install ntp
   sudo systemctl start ntp
   sudo systemctl enable ntp
   ```

### Option 3: Minimal Installation
If repository issues persist, try installing with minimal dependencies:
```bash
sudo apt update -o Acquire::http::Timeout=30
sudo apt install --no-install-recommends python3 python3-pip python3-venv
# Then run the installation script
./install.sh
```

## What the Installation Script Does

### System Dependencies
- Python 3 and pip
- Build tools and development libraries
- Image processing libraries (for WeasyPrint)
- nginx web server
- SQLite3

### Application Setup
- Creates a dedicated service user (`orion-sphere`)
- Sets up a Python virtual environment
- Installs all Python packages from `requirements.txt`
- Creates a local configuration file
- Initializes the SQLite database

### Service Configuration
- Creates a systemd service file (`/etc/systemd/system/orion-sphere-lrp.service`)
- Configures nginx as a reverse proxy
- Sets up proper file permissions and security
- Enables automatic startup on boot

### Error Handling
The updated installation script includes:
- Retry logic for package installation (up to 3 attempts)
- Graceful handling of repository timing issues
- Detailed error logging
- Alternative installation methods

## Post-Installation Configuration

After running the installation script, you should:

### 1. Update Email Configuration
Edit the local configuration file:
```bash
sudo nano /path/to/your/app/config/local.py
```

Update the email settings:
```python
MAIL_SERVER = 'your-smtp-server.com'
MAIL_PORT = 587
MAIL_USERNAME = 'your-email@example.com'
MAIL_PASSWORD = 'your-password'
MAIL_DEFAULT_SENDER = 'Orion Sphere LRP <your-email@example.com>'
```

### 2. Change the Secret Key
Generate a secure secret key and update it in the configuration:
```python
SECRET_KEY = 'your-secure-secret-key-here'
```

### 3. Configure Domain (Optional)
If you have a domain name, update the nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/orion-sphere-lrp
```

Change `server_name _;` to `server_name yourdomain.com;`

### 4. Set up SSL/TLS (Recommended for Production)
Install Certbot and obtain SSL certificates:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Service Management

### Check Service Status
```bash
sudo systemctl status orion-sphere-lrp
```

### View Application Logs
```bash
sudo journalctl -u orion-sphere-lrp -f
```

### Restart the Application
```bash
sudo systemctl restart orion-sphere-lrp
```

### Stop the Application
```bash
sudo systemctl stop orion-sphere-lrp
```

### Enable/Disable Auto-start
```bash
sudo systemctl enable orion-sphere-lrp    # Enable auto-start
sudo systemctl disable orion-sphere-lrp   # Disable auto-start
```

## Nginx Management

### Check Nginx Status
```bash
sudo systemctl status nginx
```

### Test Nginx Configuration
```bash
sudo nginx -t
```

### Reload Nginx Configuration
```bash
sudo systemctl reload nginx
```

## File Locations

- **Application**: `/path/to/your/app/` (where you ran the script)
- **Service file**: `/etc/systemd/system/orion-sphere-lrp.service`
- **Nginx config**: `/etc/nginx/sites-available/orion-sphere-lrp`
- **Logs**: `/var/log/orion-sphere-lrp/`
- **Database**: `/path/to/your/app/db/oslrp.db`

## Troubleshooting

### Repository Issues
If you encounter repository timing issues:
1. Run the repository fix script: `./fix_repository_issues.sh`
2. Check the "Handling Repository Issues" section above
3. Try the minimal installation approach

### Service Won't Start
1. Check the service status:
   ```bash
   sudo systemctl status orion-sphere-lrp
   ```

2. View detailed logs:
   ```bash
   sudo journalctl -u orion-sphere-lrp -n 50
   ```

3. Check file permissions:
   ```bash
   sudo chown -R orion-sphere:orion-sphere /path/to/your/app
   ```

### Nginx Issues
1. Check nginx configuration:
   ```bash
   sudo nginx -t
   ```

2. View nginx error logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

### Database Issues
1. Check database file permissions:
   ```bash
   sudo chown orion-sphere:orion-sphere /path/to/your/app/db/oslrp.db
   ```

2. Reinitialize the database:
   ```bash
   cd /path/to/your/app
   source venv/bin/activate
   python3 -c "
   from app import create_app
   from models.extensions import db
   app = create_app()
   with app.app_context():
       db.create_all()
   "
   ```

### Python Package Installation Issues
If Python packages fail to install:
1. Check internet connectivity
2. Try installing packages individually:
   ```bash
   source venv/bin/activate
   pip install Flask==3.0.2
   pip install Flask-SQLAlchemy==3.1.1
   # ... continue with other packages
   ```
3. Check for system library dependencies:
   ```bash
   sudo apt install python3-dev build-essential
   ```

## Security Considerations

1. **Firewall**: Configure your firewall to only allow necessary ports (80, 443)
2. **SSL/TLS**: Always use HTTPS in production
3. **Secret Key**: Use a strong, random secret key
4. **File Permissions**: The installation script sets appropriate permissions
5. **Service User**: The application runs as a dedicated, unprivileged user

## Uninstallation

To completely remove the application:

```bash
# Stop and disable services
sudo systemctl stop orion-sphere-lrp
sudo systemctl disable orion-sphere-lrp

# Remove service file
sudo rm /etc/systemd/system/orion-sphere-lrp.service

# Remove nginx configuration
sudo rm /etc/nginx/sites-enabled/orion-sphere-lrp
sudo rm /etc/nginx/sites-available/orion-sphere-lrp

# Reload systemd and nginx
sudo systemctl daemon-reload
sudo systemctl reload nginx

# Remove service user (optional)
sudo userdel orion-sphere
sudo groupdel orion-sphere

# Remove log directories
sudo rm -rf /var/log/orion-sphere-lrp
sudo rm -rf /var/run/orion-sphere-lrp
sudo rm -rf /etc/orion-sphere-lrp
```

## Support

If you encounter issues during installation:

1. Check the troubleshooting section above
2. Review the service logs: `sudo journalctl -u orion-sphere-lrp -f`
3. Run the repository fix script: `./fix_repository_issues.sh`
4. Ensure all prerequisites are met
5. Verify file permissions are correct

The installation script is designed to be idempotent - you can run it multiple times safely. 