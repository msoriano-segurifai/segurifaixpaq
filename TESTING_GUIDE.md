# SegurifAI x PAQ - Testing Guide

## Test User Configuration

**Phone Number:** `30082653`

### Pricing Structure:
- **Frontend Display:** Shows real MAWDY pricing (Q149, Q299, Q499)
- **Backend Charging:** User 30082653 is charged **Q5.00** for ANY plan
- **Implementation:** Located in `apps/services/views.py` lines 204-222

## Health Emergency Testing Scenarios

**How AI Evaluation Works:**
1. **Claude AI reviews ALL health questionnaires** submitted by users
2. **Auto-Approves** routine/low-risk cases with high confidence (>=75%)
3. **Requires Human Review** when:
   - Critical symptoms detected (chest pain, unconscious, severe bleeding)
   - High urgency level (CRITICAL or HIGH)
   - Low AI confidence (<75%)
   - AI explicitly flags for review
   - Any AI processing error
4. **Safety First Approach:** When uncertain, always escalates to MAWDY medical agent

### =� CRITICAL - Immediate Human Review (Urgency: CRITICAL)

These scenarios trigger immediate MAWDY agent notification:

#### Scenario 1: Cardiac Emergency
```
Emergency Type: PROBLEMA_CARDIACO
Critical Symptoms:
   Dolor de pecho
   Dificultad para respirar
Main Symptoms: Dolor, Mareo
Patient Age: 55
Gender: MASCULINO
Consciousness: CONSCIOUS
Pre-existing: Hipertensi�n, diabetes

Expected Result: =� CRITICAL - PENDING_REVIEW
Message: "=� EMERGENCIA CR�TICA. Un agente MAWDY est� siendo notificado inmediatamente."
```

#### Scenario 2: Unconscious Patient
```
Emergency Type: ACCIDENTE
Critical Symptoms:
   Sangrado severo
Main Symptoms: P�rdida de conciencia
Patient Age: 30
Gender: FEMENINO
Consciousness: UNCONSCIOUS
Pre-existing: Ninguna

Expected Result: =� CRITICAL - PENDING_REVIEW
```

#### Scenario 3: Severe Breathing Difficulty
```
Emergency Type: DIFICULTAD_RESPIRATORIA
Critical Symptoms:
   Dificultad para respirar
Main Symptoms: Debilidad, Confusi�n
Patient Age: 65
Gender: MASCULINO
Consciousness: DROWSY
Pre-existing: Asma

Expected Result: =� CRITICAL - PENDING_REVIEW
```

---

### � HIGH - Urgent Review Required (Urgency: HIGH)

#### Scenario 4: Severe Pain
```
Emergency Type: DOLOR_CRONICO
Critical Symptoms: (none)
Main Symptoms: Dolor, Fiebre, V�mito
Patient Age: 45
Gender: FEMENINO
Consciousness: CONSCIOUS
Pre-existing: Ninguna

Expected Result: � HIGH - PENDING_REVIEW or APPROVED
Message: "Requiere revisi�n de agente MAWDY. Nivel de urgencia: HIGH"
```

#### Scenario 5: Injury with Moderate Symptoms
```
Emergency Type: LESION
Critical Symptoms: (none)
Main Symptoms: Dolor, Debilidad
Patient Age: 28
Gender: MASCULINO
Consciousness: CONSCIOUS
Pre-existing: Ninguna

Expected Result: � HIGH - APPROVED
```

---

### =� MEDIUM - Standard Review (Urgency: MEDIUM)

#### Scenario 6: Sudden Illness
```
Emergency Type: ENFERMEDAD_REPENTINA
Critical Symptoms: (none)
Main Symptoms: Fiebre, N�useas, Debilidad
Patient Age: 35
Gender: FEMENINO
Consciousness: CONSCIOUS
Pre-existing: Ninguna

Expected Result:  MEDIUM - APPROVED
Message: "Informaci�n validada. Nivel de urgencia: MEDIUM. Un t�cnico ser� asignado pronto."
```

#### Scenario 7: Mild Poisoning
```
Emergency Type: INTOXICACION
Critical Symptoms: (none)
Main Symptoms: N�useas, V�mito, Mareo
Patient Age: 22
Gender: MASCULINO
Consciousness: CONSCIOUS
Pre-existing: Ninguna

Expected Result:  MEDIUM - APPROVED
```

---

### 9 LOW - Routine (Urgency: LOW)

#### Scenario 8: Mild Chronic Pain
```
Emergency Type: DOLOR_CRONICO
Critical Symptoms: (none)
Main Symptoms: Dolor (leve)
Patient Age: 40
Gender: FEMENINO
Consciousness: CONSCIOUS
Pre-existing: Artritis

Expected Result:  LOW - APPROVED
```

---

## Vehicle Validation Testing Scenarios

###  APPROVED - Valid Vehicle

#### Scenario 1: Real Vehicle Data
```
Make: Toyota
Model: Corolla
Year: 2020
Plate: P-123ABC
Color: Blanco
VIN: (optional)

Expected Result:  APPROVED
Message: "Veh�culo validado exitosamente por IA"
```

#### Scenario 2: Common Guatemala Vehicle
```
Make: Nissan
Model: Sentra
Year: 2018
Plate: P456DEF
Color: Gris

Expected Result:  APPROVED
```

---

### � PENDING_REVIEW - Needs Human Review

#### Scenario 3: Unusual Combination
```
Make: Ferrari
Model: F40
Year: 2023
Plate: P-999ZZZ
Color: Rojo

Expected Result: � PENDING_REVIEW
Message: "Requiere revisi�n manual. Posibles problemas: modelo raro/incoherente"
```

#### Scenario 4: Old Vehicle
```
Make: Ford
Model: Mustang
Year: 1965
Plate: P123XYZ
Color: Azul

Expected Result: � PENDING_REVIEW
```

---

### L FAILED - Invalid Format

#### Scenario 5: Invalid Year
```
Make: Honda
Model: Civic
Year: 2030 (future year)
Plate: P-123ABC

Expected Result: L FAILED
Message: "Errores de formato: A�o inv�lido (debe estar entre 1900-2025)"
```

#### Scenario 6: Invalid Plate Format
```
Make: Toyota
Model: Camry
Year: 2020
Plate: 123 (too short)

Expected Result: L FAILED
Message: "Errores de formato: Formato de placa inv�lido"
```

---

## Testing Flow for User 30082653

### Step 1: Login
```
Phone: 30082653
(Request OTP via PAQ integration)
```

### Step 2: Subscribe to Plan
1. Go to "Planes" section
2. **See:** Normal MAWDY pricing displayed (Q149/Q299/Q499)
3. Select any plan
4. Click "Suscribirse con PAQ"
5. **Backend charges:** Q5.00 (verified in logs)
6. Complete OTP verification

### Step 3: Test Health Assistance

1. Navigate to "Solicitar Asistencia"
2. Select **Health/Medical** category
3. Fill location information
4. **Step 3: Health Questionnaire**
   - Fill according to test scenario (see above)
   - Click "Validar Informaci�n"
   - **See AI validation result**
5. Review validation message
6. Continue to confirmation
7. Submit request

### Step 4: Test Roadside Assistance

1. Navigate to "Solicitar Asistencia"
2. Select **Roadside/Vehicular** category
3. Fill location information
4. **Step 3: Vehicle Information**
   - Fill according to test scenario (see above)
   - Click "Validar Veh�culo"
   - **See AI validation result**
5. Continue to confirmation
6. Submit request

---

## API Testing with curl

### Test Health Validation
```bash
curl -X POST http://localhost:8000/api/assistance/validate-health/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "emergency_type": "PROBLEMA_CARDIACO",
    "symptoms": "Dolor, Mareo",
    "patient_age": "55",
    "patient_gender": "MASCULINO",
    "consciousness_level": "CONSCIOUS",
    "breathing_difficulty": false,
    "chest_pain": true,
    "bleeding": false,
    "pre_existing_conditions": "Hipertensi�n",
    "medications": "Losart�n",
    "people_affected": "1"
  }'
```

### Test Vehicle Validation
```bash
curl -X POST http://localhost:8000/api/assistance/validate-vehicle/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "make": "Toyota",
    "model": "Corolla",
    "year": "2020",
    "plate": "P-123ABC",
    "color": "Blanco",
    "vin": ""
  }'
```

---

## MAWDY Agent Review Interface

### Pending Health Validations
```bash
GET /api/assistance/health-validations/pending/
```

**Response:** List of pending health validations sorted by urgency (CRITICAL first)

### Approve Health Validation
```bash
POST /api/assistance/health-validations/{id}/approve/
{
  "notes": "Verified patient information",
  "urgency_level": "HIGH"
}
```

### Reject Health Validation
```bash
POST /api/assistance/health-validations/{id}/reject/
{
  "reason": "Informaci�n insuficiente",
  "notes": "Solicitar m�s detalles al usuario"
}
```

---

## Expected Behaviors

###  Success Indicators

1. **Test User Pricing:**
   - Frontend shows: Q149, Q299, Q499
   - Backend log shows: "Test user pricing applied: Q5.00 for phone 30082653"
   - Database `UserService.amount_paid` = 5.00

2. **Health Validation:**
   - Critical symptoms � PENDING_REVIEW
   - Mild symptoms � APPROVED
   - All validations stored in database
   - AI confidence score provided

3. **Vehicle Validation:**
   - Valid vehicles � APPROVED
   - Unusual combinations � PENDING_REVIEW
   - Invalid formats � FAILED

### � Edge Cases to Test

1. **Multiple People Affected:**
   - Select "4+ personas"
   - Should increase urgency level

2. **Pre-existing Conditions + Critical Symptoms:**
   - Always triggers PENDING_REVIEW

3. **Empty Optional Fields:**
   - Should still validate successfully
   - Pre-existing conditions: empty
   - Medications: empty

4. **AI Failure Scenario:**
   - If Claude API fails
   - Should fallback to PENDING_REVIEW
   - User can still continue

---

## AI Evaluation Testing

### Test Auto-Approval Flow
1. Submit a MEDIUM urgency health request (Scenario 6)
2. **Expected:** Claude evaluates → High confidence → AUTO-APPROVED
3. **Verify:** Validation message shows "Información validada"
4. **Backend log:** Should show AI confidence score >= 0.75

### Test Human Review Flow
1. Submit a CRITICAL health request (Scenario 1)
2. **Expected:** Claude evaluates → Detects red flags → PENDING_REVIEW
3. **Verify:** Validation message shows "EMERGENCIA CRÍTICA"
4. **Backend log:** Should show "CRITICAL health emergency detected"

### Test AI Failure Fallback
1. Temporarily set invalid ANTHROPIC_API_KEY in .env
2. Submit any health request
3. **Expected:** AI fails → Automatic PENDING_REVIEW
4. **Verify:** Message shows "La IA no pudo procesar tu solicitud"
5. **Restore:** Set correct API key after testing

## Verification Checklist

- [ ] User 30082653 sees normal MAWDY prices on frontend
- [ ] User 30082653 is charged Q5.00 on backend
- [ ] Critical health scenarios trigger PENDING_REVIEW (AI detects)
- [ ] Normal health scenarios auto-approve (AI approves)
- [ ] AI failure triggers PENDING_REVIEW fallback
- [ ] Vehicle validation works for common vehicles
- [ ] Invalid vehicle formats are rejected
- [ ] MAWDY agents can see pending validations
- [ ] Validation status visible in request confirmation
- [ ] Full request flow works end-to-end

---

## Troubleshooting

### Issue: AI Validation Always Fails
**Solution:** Check `ANTHROPIC_API_KEY` in `.env` file

### Issue: Test User Charged Full Price
**Solution:** Verify phone number is exactly "30082653" (no spaces)

### Issue: Health Questionnaire Not Showing
**Solution:** Ensure category type is "HEALTH" or "MEDICAL"

### Issue: Vehicle Step Not Showing
**Solution:** Ensure category type is "ROADSIDE" or "VEHICULAR"

---

## Database Queries for Verification

### Check Test User Subscriptions
```sql
SELECT us.id, us.amount_paid, sp.name, u.phone_number
FROM services_userservice us
JOIN services_serviceplan sp ON us.service_plan_id = sp.id
JOIN users_user u ON us.user_id = u.id
WHERE u.phone_number LIKE '%30082653%';
```

### Check Health Validations
```sql
SELECT id, emergency_type, urgency_level, validation_status, ai_confidence_score, created_at
FROM assistance_healthvalidation
ORDER BY urgency_level DESC, created_at DESC
LIMIT 10;
```

### Check Vehicle Validations
```sql
SELECT id, make, model, year, plate, validation_status, ai_confidence_score, created_at
FROM assistance_vehiclevalidation
ORDER BY created_at DESC
LIMIT 10;
```

---

## Support

For issues or questions:
- Check Django logs: `python manage.py runserver` output
- Check browser console for frontend errors
- Verify API responses in Network tab
- Review database records for validation results
