#!/bin/bash

# Nextstep Production Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
PROJECT_DIR="/var/www/nextstep"
LOG_FILE="/var/log/nextstep-deploy.log"

echo "===================================="
echo "Nextstep Deployment Script"
echo "Environment: $ENVIRONMENT"
echo "Date: $(date)"
echo "===================================="

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Function to check if service is running
check_service() {
    if systemctl is-active --quiet $1; then
        log "✓ $1 is running"
        return 0
    else
        log "✗ $1 is not running"
        return 1
    fi
}

# Create necessary directories
log "Creating necessary directories..."
sudo mkdir -p $PROJECT_DIR/logs
sudo mkdir -p /var/log/nginx
sudo chown -R $USER:$USER $PROJECT_DIR

# Update system packages
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
log "Installing system dependencies..."
sudo apt install -y nginx python3-pip nodejs npm mongodb redis-server git curl

# Install PM2 globally
log "Installing PM2..."
sudo npm install -g pm2 yarn

# Clone or update repository
if [ -d "$PROJECT_DIR/.git" ]; then
    log "Updating repository..."
    cd $PROJECT_DIR
    git fetch origin
    git reset --hard origin/main
else
    log "Cloning repository..."
    sudo rm -rf $PROJECT_DIR
    git clone https://github.com/Simonwafula/Nextstepjobs.git $PROJECT_DIR
    cd $PROJECT_DIR
fi

# Setup backend
log "Setting up backend..."
cd $PROJECT_DIR/backend

# Install Python dependencies
pip3 install -r requirements.txt

# Setup environment file
if [ ! -f ".env" ]; then
    log "Creating backend environment file..."
    cp .env.example .env
    log "⚠️  Please edit backend/.env with your actual configuration"
fi

# Setup frontend
log "Setting up frontend..."
cd $PROJECT_DIR/frontend

# Install Node dependencies
yarn install

# Setup environment file
if [ ! -f ".env" ]; then
    log "Creating frontend environment file..."
    cp .env.example .env
    log "⚠️  Please edit frontend/.env with your actual configuration"
fi

# Build frontend for production
log "Building frontend..."
yarn build

# Setup Nginx
log "Configuring Nginx..."
sudo cp $PROJECT_DIR/nginx.conf /etc/nginx/sites-available/nextstep
sudo ln -sf /etc/nginx/sites-available/nextstep /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
if sudo nginx -t; then
    log "✓ Nginx configuration is valid"
else
    log "✗ Nginx configuration is invalid"
    exit 1
fi

# Setup SSL (Let's Encrypt) - Optional
setup_ssl() {
    log "Setting up SSL with Let's Encrypt..."
    sudo apt install -y certbot python3-certbot-nginx
    
    echo "To setup SSL, run:"
    echo "sudo certbot --nginx -d your-domain.com"
    echo "sudo crontab -e"
    echo "Add: 0 12 * * * /usr/bin/certbot renew --quiet"
}

# Start services
log "Starting services..."

# Start MongoDB
if ! check_service mongodb; then
    sudo systemctl start mongodb
    sudo systemctl enable mongodb
fi

# Start Redis
if ! check_service redis-server; then
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
fi

# Start Nginx
if ! check_service nginx; then
    sudo systemctl start nginx
    sudo systemctl enable nginx
else
    sudo systemctl reload nginx
fi

# Setup PM2
log "Setting up PM2..."
cd $PROJECT_DIR

# Stop existing PM2 processes
pm2 delete all 2>/dev/null || true

# Start application with PM2
pm2 start ecosystem.config.js --env $ENVIRONMENT

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
pm2 startup | grep -E '^sudo' | bash || true

# Setup log rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/nextstep > /dev/null <<EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        pm2 reloadLogs
    endscript
}
EOF

# Setup systemd service (alternative to PM2)
setup_systemd() {
    log "Setting up systemd service..."
    sudo tee /etc/systemd/system/nextstep.service > /dev/null <<EOF
[Unit]
Description=Nextstep API Server
After=network.target mongodb.service

[Service]
Type=exec
User=$USER
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=/usr/bin:/usr/local/bin
Environment=NODE_ENV=production
ExecStart=/usr/local/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable nextstep
    sudo systemctl start nextstep
}

# Setup monitoring
setup_monitoring() {
    log "Setting up basic monitoring..."
    
    # Create monitoring script
    tee $PROJECT_DIR/monitor.sh > /dev/null <<EOF
#!/bin/bash
# Basic health check script

APP_URL="http://localhost:8001/api/health"
LOG_FILE="/var/log/nextstep-monitor.log"

if curl -f \$APP_URL > /dev/null 2>&1; then
    echo "\$(date): ✓ Application is healthy" >> \$LOG_FILE
else
    echo "\$(date): ✗ Application is down - restarting..." >> \$LOG_FILE
    pm2 restart nextstep-api
fi
EOF

    chmod +x $PROJECT_DIR/monitor.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/monitor.sh") | crontab -
}

# Run monitoring setup
setup_monitoring

# Setup backup script
setup_backup() {
    log "Setting up backup script..."
    
    tee $PROJECT_DIR/backup.sh > /dev/null <<EOF
#!/bin/bash
# Database backup script

BACKUP_DIR="/var/backups/nextstep"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Backup MongoDB
mongodump --db nextstep --out \$BACKUP_DIR/mongodb_\$DATE

# Backup application files
tar -czf \$BACKUP_DIR/app_\$DATE.tar.gz $PROJECT_DIR --exclude='$PROJECT_DIR/node_modules' --exclude='$PROJECT_DIR/.git'

# Keep only last 7 days of backups
find \$BACKUP_DIR -type f -mtime +7 -delete

echo "\$(date): Backup completed: \$BACKUP_DIR"
EOF

    chmod +x $PROJECT_DIR/backup.sh
    
    # Add to crontab (daily backup at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/backup.sh") | crontab -
}

# Run backup setup
setup_backup

# Final checks
log "Performing final checks..."

# Check if MongoDB is accessible
if mongosh --eval "db.stats()" nextstep > /dev/null 2>&1; then
    log "✓ MongoDB is accessible"
else
    log "✗ MongoDB connection failed"
fi

# Check if application is responding
sleep 5
if curl -f http://localhost:8001/api/health > /dev/null 2>&1; then
    log "✓ Application is responding"
else
    log "✗ Application is not responding"
fi

# Display status
log "Deployment Summary:"
log "=================="
pm2 status

log ""
log "Services Status:"
log "==============="
check_service mongodb
check_service redis-server  
check_service nginx

log ""
log "🎉 Deployment completed!"
log ""
log "Next steps:"
log "1. Edit backend/.env with your actual configuration"
log "2. Edit frontend/.env with your domain"
log "3. Setup SSL certificate: sudo certbot --nginx -d your-domain.com"
log "4. Update Nginx configuration with your domain name"
log "5. Test the application: http://your-domain.com"
log ""
log "Logs location: $PROJECT_DIR/logs/"
log "Monitor logs: pm2 logs"
log "Application status: pm2 status"