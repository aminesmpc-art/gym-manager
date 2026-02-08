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

*Last Updated: 2026-02-08*
