# Cahier des Charges Complet — Système de Gestion TKF

## 1. Présentation Générale

### 1.1. Nom du projet
**TKF** — Transport et Courrier Interurbain Mali

### 1.2. Objectif du projet
Concevoir et développer une solution numérique permettant de gérer efficacement les opérations de transport interurbain de la société TKF, reliant plusieurs villes du Mali. L'application doit couvrir la gestion des véhicules, la vente de tickets, le suivi des recettes, la gestion du personnel, ainsi que la gestion des courriers.

### 1.3. Objectifs spécifiques
- ✅ Centraliser toutes les opérations (réservations, trajets, paiements, courriers)
- ✅ Optimiser la planification des voyages et la répartition des véhicules
- ✅ Offrir un tableau de bord décisionnel pour la direction
- ✅ Assurer la traçabilité complète des opérations et des courriers
- ✅ Augmenter les revenus par meilleure gestion des capacités
- ✅ Réduire les coûts opérationnels (carburant, entretien)
- ✅ Améliorer l'expérience client (réservation en ligne, suivi temps réel)

---

## 2. Périmètre Fonctionnel

### 2.1. Gestion des Villes et Itinéraires
#### Fonctionnalités
- Ajout / modification / suppression des villes
- Création d'itinéraires (ex : Bamako → Ségou → Mopti)
- Tarification selon distance ou catégorie de véhicule
- Estimation automatique du temps de trajet
- Gestion des haltes/points intermédiaires
- Mémorisation des points GPS

#### Données à capturer
- Nom de la ville
- Coordonnées GPS
- Nombre d'habitants
- Infrastructure (gare routière, etc.)

---

### 2.2. Gestion des Véhicules
#### Fonctionnalités
- Enregistrement des véhicules (matricule, modèle, capacité, état, assurance, visite technique)
- Affectation des véhicules aux itinéraires
- Suivi d'entretien et de consommation carburant
- Historique des trajets effectués
- Génération d'alertes pour révisions
- Gestion des sinistres/dommages

#### Données à capturer
- Immatriculation
- Marque/Modèle
- Année d'acquisition
- Capacité passagers
- État (Actif, En maintenance, Retiré)
- Consommation carburant moyenne
- Dates d'assurance et visite technique

---

### 2.3. Gestion du Personnel
#### Types d'employés
- **Chauffeurs** : Conduite véhicules
- **Receveurs** : Vente tickets, accueil passagers
- **Guichetiers** : Vente tickets, gestion caisses
- **Contrôleurs** : Validation tickets
- **Agents Courrier** : Gestion parcels/colis
- **Administrateurs** : Configuration système

#### Fonctionnalités
- Enregistrement du personnel
- Attribution des rôles et permissions
- Suivi des salaires (base + primes)
- Historique des trajets effectués
- Gestion des congés
- Évaluation de performance

#### Données à capturer
- Nom / Prénom
- Email / Téléphone
- Fonction/Rôle
- Date d'embauche
- Salaire mensuel
- Document d'identité

---

### 2.4. Gestion des Trajets
#### Fonctionnalités
- Création de trajets planifiés (horaires réguliers)
- Affectation véhicule + personnel
- Modification dynamique (retards, annulations)
- Suivi en temps réel (GPS)
- Historique complet
- Arrêt à points intermédiaires

#### Statuts de trajet
- Planifié
- En cours
- Terminé
- Annulé
- Reporté

#### Données à capturer
- Itinéraire
- Véhicule assigné
- Chauffeur assigné
- Horaire départ/arrivée
- État du trajet
- Nombre de passagers

---

### 2.5. Vente et Gestion des Tickets
#### Fonctionnalités
- Réservation de tickets (online + guichets)
- Génération de codes QR/codes barres
- Paiement (espèces, mobile money, carte)
- Annulation/remboursement
- Gestion des tarifs (adulte, enfant, étudiant)
- Places disponibles en temps réel
- Système de file d'attente

#### Statuts de billet
- Réservé
- Payé
- Scanné/Validé
- Utilisé
- Annulé

#### Données à capturer
- Numéro billet unique
- Passager (nom, prénom, téléphone)
- Itinéraire
- Date de voyage
- Prix payé
- Mode de paiement

---

### 2.6. Suivi des Recettes
#### Fonctionnalités
- Enregistrement de tous les paiements (tickets, courriers, services)
- Rapports journaliers/mensuels/annuels
- Comparaison budgets vs réalisé
- Ventilation par route, par guichetier
- Gestion des dépenses (carburant, entretien, salaires)
- Bénéfices nets

#### Indicateurs clés (KPIs)
- Chiffre d'affaires total
- Revenu moyen par trajet
- Taux d'occupation moyen
- Coûts d'exploitation
- Marge nette

---

### 2.7. Gestion des Courriers/Colis
#### Fonctionnalités
- Enregistrement des colis (expéditeur, destinataire, contenu, poids)
- Tarification selon poids/distance
- Suivi en temps réel (code tracking)
- Assignation à trajets
- Livraison et signature
- Gestion des réclamations

#### Statuts de colis
- Reçu
- En transit
- À la gare
- Livré
- Retourné

#### Données à capturer
- Code tracking unique
- Expéditeur / Destinataire
- Contenu déclaré
- Poids / Dimensions
- Valeur assurée
- Date de dépôt/livraison

---

### 2.8. Tableau de Bord Décisionnel
#### Dashboards par rôle

**Pour Administrateur / Direction**
- KPIs globaux (CA, marge, etc.)
- Graphiques trajets/performances
- Alertes (véhicules, employés)
- Rapports complets
- Gestion utilisateurs

**Pour Manager Opérations**
- Trajets en cours
- Véhicules actifs/en maintenance
- Personnel assigné
- Alertes temps réel

**Pour Manager Finance**
- Recettes journalières
- Dépenses détaillées
- Bénéfices par route
- Comparaison avec budgets

**Pour Guichetier**
- Ventes du jour
- Places disponibles
- Caisses
- Passagers enregistrés

---

## 3. Spécifications Techniques

### 3.1. Stack Technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Frontend** | React + TypeScript | 18+ |
| **Backend** | Node.js + Express | 18 LTS |
| **Base de données** | PostgreSQL | 14+ |
| **Cache** | Redis | 7+ |
| **Authentification** | JWT + bcrypt | - |
| **API** | REST + JSON | - |
| **UI Components** | Material-UI (MUI) | 5+ |
| **State Management** | Redux Toolkit | - |
| **Mapping** | Leaflet + OpenStreetMap | - |
| **Containerisation** | Docker | - |
| **Orchestration** | Docker Compose | - |
| **CI/CD** | GitHub Actions | - |

### 3.2. Architecture

```
TRANSPORT (TKF)/
├── frontend/                 # Application React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── App.tsx
│   └── package.json
│
├── backend/                  # Server Express.js
│   ├── src/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── config/
│   └── package.json
│
├── infrastructure/           # Docker, K8s, CI/CD
│   ├── docker-compose.yml
│   ├── nginx/
│   └── k8s/
│
└── docs/                     # Documentation
    ├── API.md
    ├── DATABASE.md
    └── DEPLOYMENT.md
```

---

## 4. Cas d'Usage Principaux

### 4.1. Réservation de billet
1. Utilisateur accède au site web
2. Cherche itinéraire (ville départ/arrivée, date)
3. Voit les trajets disponibles et prix
4. Sélectionne trajet et nombre de places
5. Remplit infos passagers
6. Effectue paiement
7. Reçoit code QR par SMS/email
8. Code QR scannné à bord = validation

### 4.2. Suivi trajet en temps réel
1. Passager rentre numéro billet
2. Voit position véhicule en direct (Google Maps)
3. Reçoit notifications (départ, arrêts, arrivée)

### 4.3. Gestion recettes quotidienne
1. Guichetier lance rapport fin de journée
2. Système totalise ventes du jour
3. Réconciliation avec caisse physique
4. Export en PDF pour direction

### 4.4. Envoi colis
1. Client va au guichet
2. Agent remplit formulaire colis
3. Code tracking généré
4. Colis assigné à trajet
5. Client peut suivre en ligne jusqu'à livraison

---

## 5. Exigences Non-Fonctionnelles

### 5.1. Performance
- Temps de réponse < 2 secondes (99e percentile)
- Supporte 1000+ utilisateurs simultanés
- Database queries < 200ms (optimisées)

### 5.2. Sécurité
- Authentification JWT + 2FA (optionnel)
- Chiffrement mots de passe (bcrypt)
- HTTPS/TLS obligatoire
- Input validation + sanitization
- SQL Injection prevention
- Rate limiting (brute force protection)
- Audit logs complets

### 5.3. Disponibilité
- Uptime cible : 99.5%
- Sauvegarde DB : quotidienne (3 copies)
- Disaster recovery plan
- Maintenance planifiée : horaires creuses

### 5.4. Scalabilité
- Architecture microservices-ready
- Horizontal scaling possible
- Redis pour sessions distribuées
- Database connection pooling

### 5.5. Maintenabilité
- Code bien documenté + comments
- Tests automatisés (unit + intégration)
- CI/CD pipeline robuste
- API documentation (Swagger)
- Monitoring + alertes

---

## 6. Phases de Développement

### Phase 1 : Fondations (4-6 semaines)
- ✅ Setup infrastructure (Docker, DB, CI/CD)
- ✅ Authentification & RBAC
- ✅ API endpoints villes/itinéraires
- ✅ Frontend login + dashboard basique

### Phase 2 : Core Features (6-8 semaines)
- ✅ Gestion véhicules complet
- ✅ Gestion personnel complet
- ✅ Création/suivi trajets
- ✅ Vente tickets basique
- ✅ UI principale

### Phase 3 : Monetization (4-6 semaines)
- ✅ Paiement intégré (Stripe/Wave Money)
- ✅ Récettes & rapports
- ✅ Dashboards complets
- ✅ SMS notifications

### Phase 4 : Courrier & GPS (4-6 semaines)
- ✅ Gestion colis complet
- ✅ Tracking temps réel (GPS)
- ✅ Mapping Leaflet
- ✅ Notifications avancées

### Phase 5 : Production & Optimisation (2-4 semaines)
- ✅ Performance tuning
- ✅ Security audit
- ✅ Testing exhaustif
- ✅ Documentation déploiement
- ✅ Training utilisateurs

---

## 7. Budget & Ressources

### Équipe
- 1 Lead Developer (Full Stack)
- 1 Frontend Developer
- 1 Backend Developer
- 1 DevOps/Infrastructure
- 1 QA Engineer
- 1 Product Manager

### Infrastructure (Mensuel)
- Cloud Server (AWS/Azure) : $200-400
- Database (PostgreSQL Cloud) : $50-100
- Redis Cloud : $20-50
- CDN/Monitoring : $50-100
- **Total** : $320-650/mois

---

## 8. Risques & Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|-----------|
| Retard développement | Moyen | Haut | Planning slack de 20% |
| Problèmes performance | Moyen | Haut | Tests de charge dès Phase 2 |
| Perte données | Faible | Critique | Backup 3x/jour, DR plan |
| Sécurité breach | Faible | Critique | Audit sécurité externe |
| Adoption utilisateurs | Moyen | Moyen | Training + support 24/7 |

---

## 9. Critères de Succès

✅ Système opérationnel pour 100+ trajets/jour  
✅ Taux d'utilisation > 80% des utilisateurs potentiels  
✅ 0 perte de données (99.99% uptime)  
✅ Satisfaction client > 4.5/5  
✅ ROI positif en 12 mois  

---

**Document** : Cahier des Charges Complet TKF  
**Date** : 24 Décembre 2024  
**Version** : 1.0  
**Approuvé par** : [À compléter]
