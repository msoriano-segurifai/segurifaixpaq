# SegurifAI x PAQ - START HERE

## Backend Ready for Guatemala

Your Django REST API backend is fully configured for Guatemala with MAPFRE as the provider and PAQ Wallet PAQ-GO integration.

---

## Quick Start

### 1. Activate Environment & Start Server

```bash
cd "SegurifAI x PAQ"
venv\Scripts\activate  # Windows
python manage.py runserver
```

Server runs at: **http://localhost:8000**

### 2. Access Points

| Service | URL |
|---------|-----|
| API Documentation (Swagger) | http://localhost:8000/api/docs/ |
| API Documentation (ReDoc) | http://localhost:8000/api/redoc/ |
| Admin Panel | http://localhost:8000/admin/ |

---

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@segurifai.com | Admin123! |

---

## Service Plans (GTQ)

| Service | Basic | Premium |
|---------|-------|---------|
| Asistencia Vial | Q150/mes | Q300/mes |
| Asistencia Medica | Q225/mes | Q450/mes |
| Seguro de Tarjeta | Q75/mes | Q150/mes |

**Provider:** MAPFRE Guatemala - 24/7 national coverage

---

## Quick API Test

### 1. Get Auth Token

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@segurifai.com","password":"Admin123!"}'
```

### 2. View Service Plans (Public)

```bash
curl http://localhost:8000/api/services/plans/
```

### 3. View Provider (MAPFRE)

```bash
curl http://localhost:8000/api/providers/
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Complete project documentation |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide |
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API reference |
| [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) | Postman testing guide |
| [docs/PAQ_WALLET.md](docs/PAQ_WALLET.md) | PAQ Wallet integration |

---

## Key Features

- **MAPFRE Guatemala** as sole provider
- **PAQ Wallet PAQ-GO** payment integration
- **GTQ** (Guatemalan Quetzales) currency
- **+502** phone number format
- JWT authentication
- Role-based access control

---

## Need to Reset Data?

```bash
python manage.py setup_production_data --confirm
```

This creates fresh Guatemala data with MAPFRE and all service plans.

---

**Built for Guatemala with Django REST Framework + PAQ Wallet**
