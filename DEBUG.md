# 🐛 DEBUG LOG

> Document of all bugs encountered and how they were solved.

---

## Bug #1: Create Gym Returns 500 Server Error
**Date**: 2026-02-08
**Status**: 🔄 IN PROGRESS

### Symptoms
- Super Admin app → Create New Gym → Click "Create Gym"
- Returns: `Server Error (500)`
- No specific error message

### Investigation
1. Frontend sends POST to `/api/tenants/` with:
   - `name`, `slug`, `schema_name`, `owner_name`, `owner_email`, `owner_phone`
2. Backend `GymViewSet` uses `ModelViewSet.create()`
3. `django-tenants` should auto-create schema when Gym.save() is called
4. **500 error** = something crashes in the backend during gym creation

### Root Cause
- TODO: Check backend for actual error

### Solution
- TODO: Add traceback logging to GymViewSet.create()

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

*Last Updated: 2026-02-08*
