# 🚀 Guide Build & Déploiement (Sans Docker)

## Phase 1: Setup Initial

### Backend
```bash
cd backend

# Environnement Python
python3.12 -m venv venv
source venv/bin/activate

# Dépendances
pip install -r requirements.txt
pip install gunicorn whitenoise psycopg2-binary

# Configuration
cp .env.example .env
# Éditer .env avec vos paramètres
```

### Frontend
```bash
cd ../frontend

# Dépendances
yarn install
# ou: npm install
```

---

## Phase 2: Build Production

### 1. Frontend Build
```bash
cd frontend

# Build optimisé
yarn build

# Vérifier le résultat
ls -lah dist/
# dist/ contient: index.html + assets/
```

### 2. Backend Préparation
```bash
cd ../backend

# Migrations BD
python manage.py migrate

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Supprimer le cache
python manage.py clear_cache 2>/dev/null || true
```

---

## Phase 3: Déploiement Production

### Option A: Serveur Linux (VPS)

**1. Préparer le serveur**
```bash
# Sur votre serveur
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3-pip python3-venv postgresql nginx
sudo apt install -y nodejs npm

# Créer utilisateur app
sudo useradd -m -s /bin/bash appuser
sudo -u appuser mkdir -p /home/appuser/tkf
```

**2. Déployer l'application**
```bash
# Sur votre PC local
cd /home/lidruf/TRANSPORT

# Compresser
tar -czf tkf-release.tar.gz \
  backend/ frontend/dist/ \
  --exclude=backend/venv \
  --exclude=backend/__pycache__ \
  --exclude=frontend/node_modules

# Envoyer au serveur
scp tkf-release.tar.gz appuser@your-server.com:/home/appuser/tkf/

# Sur le serveur
ssh appuser@your-server.com
cd /home/appuser/tkf
tar -xzf tkf-release.tar.gz

# Setup
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

**3. Configurer Gunicorn (systemd)**
```bash
# Sur le serveur, créer: /etc/systemd/system/tkf.service
sudo cat > /etc/systemd/system/tkf.service << 'EOF'
[Unit]
Description=TKF Backend Service
After=network.target postgresql.service

[Service]
Type=notify
User=appuser
WorkingDirectory=/home/appuser/tkf/backend
Environment="PATH=/home/appuser/tkf/backend/venv/bin"
ExecStart=/home/appuser/tkf/backend/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind unix:/run/tkf.sock \
    --timeout 60 \
    --access-logfile /var/log/tkf-access.log \
    --error-logfile /var/log/tkf-error.log \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Activer le service
sudo systemctl daemon-reload
sudo systemctl enable tkf
sudo systemctl start tkf
sudo systemctl status tkf
```

**4. Configurer Nginx**
```bash
# Sur le serveur, créer: /etc/nginx/sites-available/tkf
sudo cat > /etc/nginx/sites-available/tkf << 'EOF'
upstream tkf_backend {
    server unix:/run/tkf.sock fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://tkf_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/appuser/tkf/backend/staticfiles/;
        expires 30d;
    }

    location / {
        alias /home/appuser/tkf/frontend/dist/;
        try_files $uri /index.html;
    }
}
EOF

# Activer le site
sudo ln -s /etc/nginx/sites-available/tkf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. Certificat SSL (Let's Encrypt)**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### Option B: Déploiement Local (Test)

```bash
# Terminal 1: Backend
cd /home/lidruf/TRANSPORT/backend
source venv/bin/activate
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Terminal 2: Servir Frontend
cd /home/lidruf/TRANSPORT/frontend
python -m http.server 3000
```

---

## Phase 4: Vérification Post-Déploiement

```bash
# Vérifier les services
ps aux | grep gunicorn
curl http://localhost:8000/api/v1/health/

# Logs
tail -f /var/log/tkf-error.log
tail -f /var/log/tkf-access.log

# BD
psql -U postgres -d tkf_db -c "SELECT COUNT(*) FROM users_user;"
```

---

## Phase 5: Maintenance

### Mise à jour du code
```bash
cd /home/appuser/tkf/backend
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart tkf
```

### Backup BD
```bash
pg_dump -U postgres tkf_db > backup-$(date +%Y%m%d).sql
```

### Monitoring
```bash
# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier les connexions
netstat -an | grep :8000
```
