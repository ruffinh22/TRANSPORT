# Plateforme de Gestion Intégrée du Transport - Burkina Faso

## 🇧🇫 Système Officiel du Gouvernement

Portail officiel de gestion du transport routier du Burkina Faso, conforme aux normes ISO 27001, OHADA et WCAG 2.1 AA.

## 📋 Fonctionnalités

### Backend (Django 4.2.8)
- ✅ Gestion complète des trajets
- ✅ Système de billetterie
- ✅ Suivi des colis/parcels
- ✅ Gestion des paiements
- ✅ Authentification JWT
- ✅ 6 rôles système avec permissions
- ✅ API REST complète avec 30+ endpoints
- ✅ Admin panel complet

### Frontend (React 18 + TypeScript)
- ✅ Interface gouvernementale professionnelle
- ✅ 5 pages CRUD (Trajets, Billets, Colis, Paiements, Dashboard)
- ✅ Authentification sécurisée
- ✅ Navigation responsive avec sidebar
- ✅ Thème officiel Burkinabé (Rouge #CE1126 + Vert #007A5E)
- ✅ Header et Footer gouvernementaux
- ✅ Material-UI 7.3.6
- ✅ Redux Toolkit pour state management

## 🚀 Installation

### Backend
```bash
cd backend
conda activate envrl
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🔐 Accès

**URL Admin**: http://localhost:3000/login
- Email: admin@transport.local
- Mot de passe: admin123456

## 📁 Structure

```
TRANSPORT/
├── backend/          # Django 4.2.8 LTS
│   ├── apps/         # 10 applications
│   ├── config/       # Configuration
│   ├── manage.py
│   └── requirements.txt
├── frontend/         # React 18 + TypeScript
│   ├── src/
│   ├── public/
│   └── package.json
└── README.md
```

## 🏗️ Technologies

### Backend
- Django 4.2.8 LTS
- Python 3.12
- PostgreSQL / SQLite
- djangorestframework-simplejwt 5.3.0

### Frontend
- React 18
- TypeScript
- Vite 7.3.0
- Material-UI 7.3.6
- Redux Toolkit 2.11.2
- Axios

## 📄 Conformité

- ✅ ISO 27001 (Sécurité informatique)
- ✅ OHADA (Régulation commerciale burkinabée)
- ✅ WCAG 2.1 AA (Accessibilité)

## 👥 Équipe

Développé par: Lidruf TRANSPORT
Gouvernement du Burkina Faso - Ministère des Transports et de la Mobilité Urbaine

## 📞 Support

- Email: support@transport.bf
- Téléphone: +226 25 30 00 00
- Horaires: Lun-Ven 07:00-18:00 GMT

## 📜 Licence

© 2025 Gouvernement du Burkina Faso. Tous droits réservés.
