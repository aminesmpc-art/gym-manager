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
**Status**: ✅ SOLVED

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

*Last Updated: 2026-02-09*

---

## Bug #6: Revenue Card Data Scope Wrong
**Date**: 2026-02-09
**Status**: ✅ SOLVED

### Symptoms
- Revenue Card showed **all-time** collected revenue for active members
- Should show **THIS MONTH's** collected revenue
- Progress bar had no meaningful comparison

### Data Flow (Before → After)

```
BEFORE (broken):                     AFTER (fixed):
┌───────────────────┐               ┌───────────────────┐
│  Revenue Card     │               │  Revenue Card     │
│  1070 DH          │  ──────►      │  1070 DH          │
│  (all-time sum!)  │               │  (THIS MONTH)     │
│  Progress: ???    │               │  Bar: month/best   │
└───────────────────┘               └───────────────────┘
```

### Root Cause
`collected_revenue` in `reports/views.py` was summing ALL Payment records for active members instead of filtering by current month.

### Fix Applied
```python
# Changed from:
collected_revenue = sum(Payment for ALL active members)  # all-time
# Changed to:
collected_revenue = float(income_month)  # THIS MONTH's payments only
```

Progress bar compares: `this month / best month ever`

### Status
- ✅ Backend: `collected_revenue = float(income_month)`
- ✅ Frontend: progress bar uses `highestMonthlyIncome`
- ✅ Deployed to Railway

---

## Bug #7: Chart Paid/Pending Classification is WRONG 🔴
**Date**: 2026-02-09
**Status**: ✅ SOLVED

### Symptoms
- Chart tooltip shows: **Paid: 750 DH, Pending: 320 DH**
- But actual member debts total only **130 DH** (HODAYFA 80 + NIZAR 50)
- Where does 320 DH "Pending" come from?

### Investigation

#### Step 1: Trace the Chart Logic
**File**: `reports/views.py`, `RevenueChartView`, lines 481-488:

```python
for p in payments:
    amt = float(p.amount)
    # Check if member CURRENTLY has debt
    if p.member and p.member.remaining_debt > 0:
        unpaid_val += amt    # ALL of this member's payment → Pending!
    else:
        paid_val += amt      # ALL of this member's payment → Paid!
```

#### Step 2: The Smoking Gun 🔫

The logic asks: "Does this member have ANY remaining debt?"
- If YES → **entire payment amount** goes to "Pending"
- If NO → **entire payment amount** goes to "Paid"

**This is WRONG.** Here's why:

```
HODAYFA: Plan = 200 DH, Paid 120 DH, Owes 80 DH
├── Payment #1: 120 DH
└── remaining_debt > 0 → Chart marks 120 DH as "Pending" ❌

Reality: 120 DH was ACTUALLY RECEIVED → should be "Paid"
         Only 80 DH is truly "Pending" (not yet received)
```

#### Step 3: Math Proof

```
Members and payments:
┌─────────────┬──────────┬──────────┬────────┬──────────────────┐
│ Member      │ Plan     │ Paid     │ Debt   │ Chart says...    │
├─────────────┼──────────┼──────────┼────────┼──────────────────┤
│ HODAYFA     │ 200 DH   │ 120 DH   │ 80 DH  │ 120 = Pending ❌ │
│ NIZAR       │ 200 DH   │ 150 DH   │ 50 DH  │ 150 = Pending ❌ │
│ KARIMA      │ 200 DH   │ 200 DH   │ 0 DH   │ 200 = Paid ✅    │
│ Others      │ various  │ 550 DH   │ 0 DH   │ 550 = Paid ✅    │
├─────────────┼──────────┼──────────┼────────┼──────────────────┤
│ TOTAL       │          │ 1020 DH  │ 130 DH │ Paid: 750        │
│             │          │          │        │ Pending: 270     │
└─────────────┴──────────┴──────────┴────────┴──────────────────┘

Chart says:   Paid=750, Pending=320 (off because stale amount_paid)
Should say:   Paid=1020, Pending=130 (actual money received vs owed)
```

### Root Cause

**The chart conflates "received money" with "member debt status".**

A payment that was already received and is sitting in the cash register should ALWAYS be "Paid". "Pending" should only show money that has NOT been received yet (i.e., outstanding debt).

### Proposed Fix

Change the chart to show:
- **Paid (green bar)** = Sum of actual Payment records (money received)
- **Pending (pink bar)** = Sum of remaining debts (money NOT yet received)

```python
# APPLIED FIX (all 3 period handlers: week/month/year):
paid_val = sum(float(p.amount) for p in payments if p.amount)
seen_members = {}
for p in payments:
    if p.member and p.member_id not in seen_members:
        seen_members[p.member_id] = float(p.member.remaining_debt)
unpaid_val = sum(seen_members.values())
total_val = paid_val + unpaid_val
```

### Status
- ✅ Fixed in all 3 period handlers (week, month, year)
- ✅ Deployed to Railway

---

## Bug #8: Debt Numbers Differ Between Card and Member Badges 🔴
**Date**: 2026-02-09
**Status**: ✅ SOLVED

### Symptoms
- Revenue Card debt: **80 DH**
- Member badge debts: **80 DH (HODAYFA) + 50 DH (NIZAR) = 130 DH**
- Numbers should match!

### Investigation

#### Data Sources Comparison

```
Source 1: Revenue Card (reports/views.py)
├── total_expected = SUM(plan prices for active members)
├── total_paid_all = SUM(Payment.amount for active members)
└── total_debt = total_expected - total_paid_all
    Result: 80 DH

Source 2: Member Badge (member.remaining_debt property)  
├── Each member: plan.price - amount_paid (stored field)
├── HODAYFA: 200 - 120 = 80 DH
├── NIZAR:   200 - 150 = 50 DH
└── Total: 130 DH

WHY DIFFERENT?
├── Payment records say total_paid = X
├── Member amount_paid fields say total = Y
└── X ≠ Y because amount_paid was CORRUPTED by Bug #5!
```

### Root Cause

**`member.amount_paid` (stored database field) is out of sync with actual Payment records.**

This happened because of **Bug #5** (payment doubling) - when it was active, some members got wrong `amount_paid` values. Even though Bug #5 is fixed for NEW payments, the OLD corrupted data still exists.

### Proposed Fix

**Single Source of Truth Principle:**

Option A: Make `remaining_debt` compute from Payment records (most reliable):
```python
@property
def remaining_debt(self):
    from subscriptions.models import Payment
    from django.db.models import Sum
    actual_paid = Payment.objects.filter(
        member=self,
        period_start=self.subscription_start,
        period_end=self.subscription_end,
    ).aggregate(total=Sum('amount'))['total'] or 0
    return max(0, self.membership_plan.price - actual_paid)
```

Option B: Fix corrupted data + keep current property:
```bash
python manage.py recalculate_payments  # Already created!
```

**Chosen: Keep `remaining_debt` using `amount_paid` field.**

Why NOT Payment records: `perform_create` previously recorded full plan price (200 DH) instead of actual payment (150 DH), so old Payment records are corrupted. The `amount_paid` field is correct for existing members.

Going forward: `perform_create` now records the actual user-entered payment amount, so both `amount_paid` AND Payment records will be correct for new members.

### Status
- ✅ `remaining_debt` uses `amount_paid` (correct for existing data)
- ✅ `perform_create` fixed to record actual payment amount (correct for new data)
- ✅ Verified: NIZAR shows 150/200 DH with 50 DH debt
- ✅ Deployed to Railway

---

*Last Updated: 2026-02-09*
