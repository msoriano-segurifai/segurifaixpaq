# SegurifAI x PAQ - Quick Start Guide

## Getting Started in 5 Minutes

### 1. Activate Virtual Environment

```bash
cd "SegurifAI x PAQ"
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Configure Environment

```bash
# Copy environment file if not already done
cp .env.example .env

# Ensure SQLite is configured for development:
# DB_ENGINE=django.db.backends.sqlite3
# DB_NAME=db.sqlite3
```

### 3. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Setup Guatemala production data (MAPFRE + Service Plans)
python manage.py setup_production_data --confirm
```

### 4. Start the Server

```bash
python manage.py runserver
```

The server will start at [http://localhost:8000](http://localhost:8000)

---

## Access Points

| Service | URL |
|---------|-----|
| Admin Panel | http://localhost:8000/admin/ |
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |

---

## Default Credentials

After running `setup_production_data`:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@segurifai.com | Admin123! |

---

## Service Plans (GTQ - Quetzales)

| Service | Basic | Premium |
|---------|-------|---------|
| Asistencia Vial | Q150/mes | Q300/mes |
| Asistencia Medica | Q225/mes | Q450/mes |
| Seguro de Tarjeta | Q75/mes | Q150/mes |

**Provider:** MAPFRE Guatemala - 24/7 national coverage

---

## Quick API Test

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "first_name": "Juan",
    "last_name": "Perez",
    "phone_number": "+50212345678",
    "role": "USER",
    "city": "Ciudad de Guatemala",
    "country": "Guatemala"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPass123!"
  }'
```

Save the `access` token from the response.

### 3. Get Your Profile

```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. View Available Services

```bash
curl -X GET http://localhost:8000/api/services/plans/
```

---

## Create Assistance Request

### Roadside Assistance (Asistencia Vial)

```bash
curl -X POST http://localhost:8000/api/assistance/requests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "user_service": 1,
    "service_category": 1,
    "title": "Vehiculo averiado",
    "description": "Motor no enciende",
    "priority": "HIGH",
    "location_address": "6a Avenida 5-55",
    "location_city": "Ciudad de Guatemala",
    "location_state": "Guatemala",
    "vehicle_make": "Toyota",
    "vehicle_model": "Corolla",
    "vehicle_year": 2020,
    "vehicle_plate": "P-123ABC"
  }'
```

---

## PAQ Wallet Payment Flow

The platform uses PAQ-GO for payments:

1. **User subscribes** to a service plan
2. **System generates** PAYPAQ token via `emite_token()`
3. **User receives** SMS with 5-character payment code
4. **User enters** code + phone number in app
5. **System processes** payment via `PAQgo()`
6. **Subscription activated** immediately

For detailed PAQ integration, see [docs/PAQ_WALLET.md](docs/PAQ_WALLET.md)

---

## Frontend Integration

### CORS Configuration

Allowed origins (configurable in `.env`):
- `http://localhost:3000`
- `http://localhost:5173`
- `https://paqasistencias.com`

### Authentication Flow

```javascript
// Login
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/api/auth/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
};

// Fetch with auth
const fetchWithAuth = async (url) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`http://localhost:8000${url}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};

// Example usage
const profile = await fetchWithAuth('/api/users/me/');
const services = await fetchWithAuth('/api/services/plans/');
```

---

## Troubleshooting

### Database locked error
```bash
del db.sqlite3
python manage.py migrate
python manage.py setup_production_data --confirm
```

### Module not found
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### CORS errors
Update `CORS_ALLOWED_ORIGINS` in `.env` to include your frontend URL

### Token expired
Use refresh token: `POST /api/auth/token/refresh/`

### Environment variables not loading
On Windows, if you have system environment variables set, they may override `.env`. Run with explicit variables:
```bash
DB_ENGINE=django.db.backends.sqlite3 DB_NAME=db.sqlite3 python manage.py runserver
```

---

## Next Steps

1. **Read the full documentation**: [README.md](README.md)
2. **Explore API endpoints**: [API_REFERENCE.md](API_REFERENCE.md)
3. **PAQ Wallet integration**: [docs/PAQ_WALLET.md](docs/PAQ_WALLET.md)
4. **Test with Postman**: [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md)

---

## Need Help?

- Check [README.md](README.md) for detailed documentation
- View [API_REFERENCE.md](API_REFERENCE.md) for complete API reference
- Use interactive docs at http://localhost:8000/api/docs/

---

**Built for Guatemala with Django REST Framework + PAQ Wallet**
