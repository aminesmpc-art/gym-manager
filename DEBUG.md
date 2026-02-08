# 🐛 DEBUG LOG

> Document of all bugs encountered and how they were solved.

---

## Bug #1: Create Gym Returns 500 Server Error
**Date**: 2026-02-08
**Status**: ✅ SOLVED

### Symptoms
- Super Admin app → Create New Gym → Click "Create Gym"
- Returns: `Server Error (500)` then `"Invalid string used for the schema name."`

### Investigation
1. Frontend sends POST to `/api/tenants/` with data
2. `GymSerializer` had `schema_name` in `read_only_fields`
3. Frontend's `schema_name` value was ignored
4. Django-tenants requires valid `schema_name` but it was empty/None
5. This caused the "Invalid string" validation error

### Root Cause
**`schema_name` was `read_only` but never auto-generated in the serializer!**

Django-tenants validates schema names strictly:
- Must be lowercase alphanumeric + underscores only
- Cannot start with a number
- Cannot be empty

### Solution
Added `create()` method to `GymSerializer` in `tenants/serializers.py`:
```python
def create(self, validated_data):
    import re
    slug = validated_data.get('slug', '')
    # Convert slug to valid PostgreSQL schema name
    schema_name = slug.replace('-', '_')
    schema_name = re.sub(r'[^a-z0-9_]', '', schema_name.lower())
    if schema_name and schema_name[0].isdigit():
        schema_name = 'gym_' + schema_name
    validated_data['schema_name'] = schema_name
    return super().create(validated_data)
```

---

## Bug #2: Attendance Date Field NULL Error (SOLVED ✅)
**Date**: 2026-02-08
**Status**: ✅ SOLVED

### Symptoms
- Demo data reset failed
- Error: `null value in column "date" of relation "attendance"`

### Root Cause
- `create_demo_gym.py` used `timezone.now()` instead of `datetime.time()` for check-in times
- The `date` field was never set (it's required)

### Solution
```python
# Fixed in create_demo_gym.py
from datetime import time
attendance_date = today - timedelta(days=days_ago)
check_in = time(check_in_hour, check_in_minute)
Attendance.objects.get_or_create(
    member=member,
    date=attendance_date,  # Required field
    defaults={
        'check_in_time': check_in,
        'check_out_time': check_out,
    }
)
```

---

## Bug #3: Super Admin Dashboard 500 Error (SOLVED ✅)
**Date**: 2026-02-08
**Status**: ✅ SOLVED

### Symptoms
- Super Admin login → Dashboard → 500 error
- Normal gym logins work fine

### Root Cause
- Dashboard API tried to query gym-level data in `public` schema
- Super Admin has no gym schema, uses `public`

### Solution
- Added fallback in `DashboardView` for public schema:
```python
if connection.schema_name == 'public':
    return Response({
        'total_gyms': Gym.objects.count(),
        'active_gyms': Gym.objects.filter(status='approved').count(),
    })
```

---

## Bug #4: Create Gym Dialog Overflow (SOLVED ✅)
**Date**: 2026-02-08
**Status**: ✅ SOLVED

### Symptoms
- Create New Gym dialog overflowed by 23px at bottom
- Phone field was cut off

### Solution
- Wrapped dialog content in `SingleChildScrollView`
- Added `maxHeight: 600` constraint

---

## Bug #5: Payment Amount Doubles on New Member Creation 🔴

**Date**: 2026-02-08
**Status**: 🔄 FIXING

### Symptoms
- Add new member with plan price 200 DH
- Enter amount_paid: 200 DH
- After save, financial status shows: **400 / 200 DH** (double!)
  
![Screenshot shows 400/200 DH bug]

### Investigation Timeline

#### Step 1: Trace the Data Flow

**Frontend** (`add_member_screen.dart` line 91):
```dart
'amount_paid': _amountPaidController.text,  // Sends 200
```

**Backend Serializer** (`members/serializers.py`):
- `amount_paid` is NOT read-only
- Saves directly to `member.amount_paid = 200` ✓

**View** (`members/views.py` `perform_create` lines 220-242):
```python
# First: Save member with dates
member = serializer.save(
    user=user,
    subscription_start=subscription_start,  # Sets dates FIRST
    subscription_end=subscription_end,
    is_active=True
)

# Second: Create Payment  
Payment.objects.create(
    member=member,
    amount=membership_plan.price,  # 200
    period_start=subscription_start,
    period_end=subscription_end,
    ...
)
```

#### Step 2: The Smoking Gun 🔫

**Payment.save()** (`subscriptions/models.py` lines 93-106):
```python
# Check if new period or same period
is_new_period = (
    self.member.subscription_start != self.period_start or
    self.member.subscription_end != self.period_end
)

if is_new_period:
    # RESET to payment amount
    self.member.amount_paid = Decimal(str(self.amount))
else:
    # ACCUMULATE (debt payment)
    if is_new:
        self.member.amount_paid = self.member.amount_paid + self.amount
```

#### Step 3: Root Cause Analysis

**The Bug Flow:**

1. `serializer.save()` runs → `member.amount_paid = 200` + sets dates
2. `Payment.objects.create()` runs
3. Payment.save() checks: `is_new_period?`
   - `member.subscription_start == period_start` ✓ (same dates!)
   - `member.subscription_end == period_end` ✓ (same dates!)
4. **`is_new_period = False`** → enters ACCUMULATE branch
5. `amount_paid = 200 + 200 = 400` ❌

### Root Cause

**Race condition between serializer and Payment model:**
- Serializer saves amount_paid BEFORE Payment is created
- Payment.save() logic expects to be FIRST writer
- But member already has amount_paid set, so it ADDS instead of SETS

### Solutions

**Solution A (CLEANEST):** Don't accept `amount_paid` from frontend on CREATE
```python
# In serializers.py - make amount_paid read-only on create
def create(self, validated_data):
    validated_data.pop('amount_paid', None)  # Let Payment handle it
    return super().create(validated_data)
```

**Solution B:** Reset amount_paid to 0 before creating Payment
```python
# In perform_create before Payment.objects.create():
member.amount_paid = 0
member.save(update_fields=['amount_paid'])
```

**Solution C:** Add `is_initial_payment` flag to Payment model

### Chosen Fix

Solution A - Remove `amount_paid` from serializer create. The Payment model
should be the single source of truth for payment calculations.

---

*Last Updated: 2026-02-08*

