# SegurifAI - Quick Start Guide

## Setup in 3 Steps

### Step 1: Seed the Database
```bash
# Run the all-in-one seeding script
python seed_all_data.py

# Or run commands individually:
python manage.py seed_educational_modules
python manage.py seed_subscription_plans
python manage.py create_mawdy_technician
```

### Step 2: Start Backend Server
```bash
python manage.py runserver
```

### Step 3: Start Frontend
```bash
cd user-app
npm run dev
```

---

## What Was Implemented

### 1. Educational Modules (5 modules, 28 quiz questions)
- Seguridad al Volante
- Primeros Auxilios Basicos
- Ahorro Inteligente
- Prevencion de Robos y Fraudes
- Mantenimiento Vehicular Basico

**Test it:** Go to "Aprendizaje" section

### 2. Subscription Plans (9 plans across 3 categories)
- Roadside Assistance (3 plans: Q49-Q149/month)
- Health Assistance (2 plans: Q79-Q129/month)
- Card Insurance (2 plans: Q29-Q59/month)
- Combo Plans (1 plan: Q199/month)

**Test it:** Go to "Suscripciones" section

### 3. PAQ Wallet Auto-Link
- Removed manual linking option
- Shows PAQ account as automatically linked
- Displays verified status

**Test it:** Go to "Mi Billetera" section

### 4. Mawdy Field Technician
- Auto-created test provider
- Email: `mawdy@segurifai.com`
- Password: `mawdy2024`
- Available 24/7, covers Guatemala City

**Test it:** Create assistance request, see auto-assignment

### 5. Auto-Accept Assistance Requests
- New requests automatically assigned to Mawdy
- Status changes to "ASSIGNED" immediately
- ETA set to 20 minutes
- User receives notification

**Test it:**
1. Go to "Solicitar Asistencia"
2. Select any category
3. Fill location and details
4. Submit request
5. See immediate assignment to Mawdy

### 6. PAQ Payment with OTP
- Two-step payment flow
- SMS OTP verification
- Test phone: `30082653`

**Test it:**
1. Go to "Suscripciones"
2. Click "Pay with PAQ" on any plan
3. Enter phone number (30082653)
4. Click "Send Code"
5. Enter OTP received via SMS
6. Confirm payment
7. Subscription activated!

---

## Test Credentials

### Mawdy Provider
- **Email:** `mawdy@segurifai.com`
- **Password:** `mawdy2024`
- **Role:** Provider

### Test PAQ Phone
- **Number:** `30082653`
- Use for payment testing

---

## File Structure

### Backend Files Created/Modified
```
apps/
├── gamification/
│   └── management/
│       └── commands/
│           └── seed_educational_modules.py      [NEW]
├── services/
│   ├── management/
│   │   └── commands/
│   │       └── seed_subscription_plans.py       [NEW]
│   └── views.py                                 [MODIFIED - Added PAQ payment endpoints]
├── providers/
│   └── management/
│       └── commands/
│           └── create_mawdy_technician.py       [NEW]
└── assistance/
    ├── signals.py                               [NEW - Auto-assignment logic]
    └── apps.py                                  [MODIFIED - Register signals]
```

### Frontend Files Modified
```
user-app/
└── src/
    ├── pages/
    │   └── user/
    │       ├── Subscriptions.tsx                [MODIFIED - PAQ payment modal]
    │       └── PAQWallet.tsx                    [MODIFIED - Removed linking]
    └── services/
        └── api.ts                               [MODIFIED - Added PAQ payment APIs]
```

### Utility Files Created
```
├── seed_all_data.py                             [NEW - Run all seeds]
├── IMPLEMENTATION_SUMMARY.md                    [NEW - Full documentation]
└── QUICK_START.md                               [NEW - This file]
```

---

## Common Commands

### Database Seeds
```bash
# Seed educational modules
python manage.py seed_educational_modules

# Seed subscription plans
python manage.py seed_subscription_plans

# Create Mawdy technician
python manage.py create_mawdy_technician

# Run all seeds at once
python seed_all_data.py
```

### Django Management
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Django shell
python manage.py shell
```

### Frontend
```bash
# Install dependencies
cd user-app && npm install

# Run development server
npm run dev

# Build for production
npm run build
```

---

## Testing Checklist

- [ ] Educational modules load and display correctly
- [ ] Can start and complete modules
- [ ] Points and credits awarded after completion
- [ ] Subscription plans display with correct pricing
- [ ] Can toggle between monthly/yearly billing
- [ ] PAQ payment modal opens when clicking "Pay with PAQ"
- [ ] Can enter phone number and initiate payment
- [ ] OTP step shows after sending code
- [ ] Can confirm payment with OTP
- [ ] Subscription activates successfully
- [ ] PAQ wallet shows auto-linked status
- [ ] Can create assistance request
- [ ] Request automatically assigned to Mawdy
- [ ] Status shows as "ASSIGNED" immediately
- [ ] ETA displays correctly (20 minutes)

---

## Troubleshooting

### Problem: Educational modules not showing
**Solution:**
```bash
python manage.py seed_educational_modules
```

### Problem: Subscriptions not showing
**Solution:**
```bash
python manage.py seed_subscription_plans
```

### Problem: Assistance requests not auto-assigned
**Solution:**
```bash
# Verify Mawdy exists
python manage.py create_mawdy_technician

# Check signals are loaded
python manage.py shell
>>> from apps.assistance import signals
```

### Problem: PAQ payment fails
**Solution:**
1. Check PAQ credentials in `.env`
2. Verify phone number is 8 digits
3. Check backend logs for API errors
4. Use test phone: 30082653

---

## Next Steps

1. **Test all features** using the checklist above
2. **Configure PAQ credentials** in `.env` for production
3. **Create promo codes** via Django admin
4. **Add more providers** for real dispatch logic
5. **Deploy to production** environment

---

## Support

For issues or questions:
1. Check `IMPLEMENTATION_SUMMARY.md` for detailed documentation
2. Review backend logs: `tail -f logs/django.log`
3. Check browser console for frontend errors
4. Verify database has seeded data via Django shell

---

**Last Updated:** November 2024
**Version:** 1.0
