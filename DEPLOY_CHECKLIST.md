# 🚀 Production Deploy Checklist - Kupi Slona

## 📋 ПЕРЕД ДЕПЛОЕМ - Infrastructure Setup

### Server Requirements
- [ ] **Server:** VPS/Cloud with minimum 2GB RAM, 2 CPU cores
- [ ] **OS:** Ubuntu 22.04 LTS or Debian 11+
- [ ] **DNS:** A-record pointing domain → server IP
- [ ] **Firewall:** Ports 80 and 443 open
- [ ] **Docker:** Docker Engine 24+ installed
- [ ] **Docker Compose:** v2.0+ installed

---

## 🔐 SECURITY CHECKLIST (CRITICAL!)

### Before First Deployment
- [ ] ✅ `.env.*` files are in `.gitignore` (check with `git status --ignored`)
- [ ] ✅ No credentials in git history (`git log --all --full-history --source -- .env.*`)
- [ ] ✅ Generate strong SECRET_KEY (minimum 50 characters)
- [ ] ✅ Generate strong DB_PASSWORD (minimum 32 characters)
- [ ] ✅ Generate strong REDIS_PASSWORD (minimum 24 characters)
- [ ] ✅ DEBUG=False in production `.env` file
- [ ] ✅ ALLOWED_HOSTS set to your domain only
- [ ] ✅ OAuth credentials obtained from providers
- [ ] ⚠️ **NEVER commit `.env.slon.prvms.ru` or similar files to git!**

---

## 🚀 DEPLOYMENT PROCESS

### Step 1: Clone Repository on Server

```bash
cd ~
git clone https://github.com/your-username/kupi_slona.git kupi_slona
cd kupi_slona
```

### Step 2: Setup Environment File

```bash
# Create .env file from template
cp .env.example .env.slon.prvms.ru

# Edit the file
nano .env.slon.prvms.ru
```

**Required variables:**
```bash
# ==== SSL/Domain ====
DOMAIN=your-domain.com
SSL_EMAIL=your-email@example.com

# ==== Django Core ====
SECRET_KEY=<generate-with-command-below>
DEBUG=False
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com

# ==== Database ====
DB_NAME=elephant_shop
DB_USER=postgres
DB_PASSWORD=<generate-strong-password>

# ==== Redis (NEW - REQUIRED!) ====
REDIS_PASSWORD=<generate-strong-password>

# ==== OAuth ====
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
```

**Generate secure credentials:**
```bash
# SECRET_KEY (50+ characters)
openssl rand -base64 60

# DB_PASSWORD (32+ characters)
openssl rand -base64 32

# REDIS_PASSWORD (24+ characters)
openssl rand -base64 24
```

### Step 3: Initialize SSL Certificates

```bash
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh
```

⏳ This takes 30-60 seconds. It will:
- Create temporary nginx config
- Obtain Let's Encrypt certificate
- Configure nginx with SSL

### Step 4: Deploy Application

```bash
chmod +x auto-deploy.sh
./auto-deploy.sh
```

⏳ This takes 5-10 minutes. It will:
- Build Docker images
- Start all services (db, redis, web, celery, nginx, certbot)
- Run database migrations
- Collect static files
- Show deployment status

---

## ✅ POST-DEPLOYMENT VERIFICATION

### 1. Check Container Health

```bash
docker-compose -f docker-compose.prod.yml ps
```

**Expected output:**
```
NAME                  COMMAND                  STATUS           PORTS
kupi_slona-db-1       "docker-entrypoint.s…"   Up (healthy)     5432/tcp
kupi_slona-redis-1    "redis-server --requ…"   Up (healthy)     6379/tcp
kupi_slona-web-1      "/app/entrypoint.sh …"   Up (healthy)     8000/tcp
kupi_slona-celery-1   "/app/entrypoint.sh …"   Up (healthy)
kupi_slona-nginx-1    "nginx -g 'daemon of…"   Up               0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
kupi_slona-certbot-1  "/bin/sh -c 'trap ex…"   Up
```

### 2. Health Check Endpoint

```bash
curl http://localhost:8000/health/
```

**Expected response:**
```json
{"status":"healthy","database":"ok","cache":"ok"}
```

### 3. HTTPS Access

```bash
# Check HTTPS redirect
curl -I http://your-domain.com

# Check HTTPS works
curl -I https://your-domain.com
```

### 4. SSL Certificate

```bash
# View certificate details
docker-compose -f docker-compose.prod.yml run --rm certbot certificates

# Test SSL grade (after deployment)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
# Expected: A or A+ grade
```

### 5. Create Superuser

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 6. Setup Automated Backups

```bash
# Test backup script
./scripts/backup-database.sh

# Add to crontab for daily backups at 2 AM
crontab -e

# Add this line:
0 2 * * * /root/kupi_slona/scripts/backup-database.sh >> /var/log/kupi_slona_backup.log 2>&1
```

---

## 🔄 GITHUB ACTIONS CI/CD

### Setup Secrets

In your GitHub repository → Settings → Secrets and variables → Actions, add:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SERVER_HOST` | Server IP or domain | `123.456.789.0` or `server.example.com` |
| `SERVER_USER` | SSH username | `root` or `ubuntu` |
| `SSH_PRIVATE_KEY` | SSH private key for authentication | Contents of `~/.ssh/id_ed25519` |

### Generate SSH Key (if needed)

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-kupi-slona"

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@your-server-ip

# Copy private key contents for GitHub Secret
cat ~/.ssh/id_ed25519
```

### Trigger Deployment

After setup, every push to `main` branch will:
1. ✅ Run tests
2. ✅ Create database backup
3. ✅ Deploy to production
4. ✅ Run migrations
5. ✅ Collect static files
6. ✅ Perform health check

---

## 🛠️ MAINTENANCE COMMANDS

### View Logs

```bash
# Web application logs
docker-compose -f docker-compose.prod.yml logs -f web

# Nginx access/error logs
docker-compose -f docker-compose.prod.yml logs -f nginx

# Celery worker logs
docker-compose -f docker-compose.prod.yml logs -f celery_worker

# All logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Restart Services

```bash
# Restart specific service
docker-compose -f docker-compose.prod.yml restart web

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Rebuild and restart (after code changes)
docker-compose -f docker-compose.prod.yml up -d --build web
```

### Database Management

```bash
# Create backup
./scripts/backup-database.sh

# List backups
ls -lh /backups/postgres/

# Restore from backup
./scripts/restore-database.sh /backups/postgres/kupi_slona_20240211_120000.sql.gz

# Access PostgreSQL directly
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d elephant_shop
```

### Monitoring

```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Check container resource usage
docker stats

# View recent backups
ls -lht /backups/postgres/ | head -10
```

---

## 🔧 TROUBLESHOOTING

### Issue: Services Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check if ports are in use
sudo netstat -tulpn | grep -E ':(80|443|8000|5432|6379)'

# Restart with clean slate
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Issue: Health Check Failing

```bash
# Check health status
docker-compose -f docker-compose.prod.yml ps

# Test health endpoint manually
curl http://localhost:8000/health/

# Check database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD ping
```

### Issue: SSL Certificate Not Obtained

```bash
# Check DOMAIN and SSL_EMAIL in .env
cat .env.slon.prvms.ru | grep -E "^DOMAIN=|^SSL_EMAIL="

# Re-run init script
./init-letsencrypt.sh

# Check certbot logs
docker-compose -f docker-compose.prod.yml logs certbot
```

### Issue: 502 Bad Gateway

```bash
# Check if web container is running
docker-compose -f docker-compose.prod.yml ps web

# Check web logs
docker-compose -f docker-compose.prod.yml logs web

# Restart web service
docker-compose -f docker-compose.prod.yml restart web
```

### Full Diagnostic

```bash
./diagnose.sh
```

---

## 📚 ADDITIONAL RESOURCES

- **Production Plan:** [production-readiness-plan.md](/.claude/plans/production-readiness-plan.md)
- **Deployment Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Environment Template:** [.env.example](.env.example)
- **Health Check:** `https://your-domain.com/health/`
- **Admin Panel:** `https://your-domain.com/admin/`

---

## 🎉 SUCCESS CRITERIA

After deployment, verify:

- [ ] All containers are running and healthy
- [ ] Health endpoint returns `{"status":"healthy"}`
- [ ] Website loads over HTTPS
- [ ] SSL grade is A or A+
- [ ] Can create/login user accounts
- [ ] OAuth login works (Google/Apple)
- [ ] Can create and download elephant images
- [ ] Celery tasks execute successfully
- [ ] Backup script runs successfully
- [ ] GitHub Actions deployment works

**🎊 Congratulations! Your Kupi Slona is production-ready!**
