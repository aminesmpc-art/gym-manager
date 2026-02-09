# 🧠 PROJECT MEMORY

> **Read this file at the start of every conversation to remember everything.**

---

## 📱 Project Overview

**Project**: Gym Management SaaS System
**Started**: January 2026
**Owner**: aminesmpc-art

### Apps:
| App | Path | Purpose |
|-----|------|---------|
| **Gym App** | `C:\Users\HP PROBOOK\Desktop\Flutter GYM\app` | For gym owners/staff |
| **Super Admin** | `C:\Users\HP PROBOOK\Desktop\super_admin` | Manage all gyms |
| **Backend API** | `C:\Users\HP PROBOOK\Desktop\GYM` | Django API on Railway |

### Deployment:
- **Backend URL**: `https://web-production-6b8db.up.railway.app`
- **Database**: PostgreSQL on Railway
- **Multi-tenant**: django-tenants (each gym = separate schema)
- **Railway Project**: `intelligent-vitality`

---

## 🔑 Credentials

| Role | Gym Code | Username | Password |
|------|----------|----------|----------|
| Super Admin | `public` | `admin` | `admin123` |
| Demo Gym | `demo_gym` | `admin` | `admin123` |
| LAACHIRI | `laachiri` | `laachiri_admin` | *use reset password* |

---

## 💰 Pricing (Cash-based, Morocco)

| Plan | Price | Duration |
|------|-------|----------|
| **Trial** | Free | 14 days |
| **Pro** | 200 DH | Monthly |
| **Lifetime** | 2000 DH | Forever |

All plans have **unlimited members**.

---

## ✅ Implementation Status

| Phase | Status | Features |
|-------|--------|----------|
| Phase 1 | ✅ DONE | Auth, Members CRUD, Attendance |
| Phase 2 | ✅ DONE | Subscriptions, Payments, Dashboard |
| Phase 3 | ✅ DONE | Reports, Revenue Charts, Demographics |
| Phase 4 | ✅ DONE | Super Admin, Multi-tenancy, Gym Management |
| Phase 5 | ✅ DONE | CSV Export, Renewal Dialog, Skeleton Loaders |
| Password Management | ✅ DONE | Reset/Set admin passwords |
| Bug Fixes | ✅ DONE | 8 bugs fixed (see DEBUG.md) |
| Phase 6: Production | ✅ DONE | Security hardening |

### 📍 WHERE WE ARE NOW (2026-02-09):

**All features complete + production-ready!**

- ✅ All core features (Members, Attendance, Subscriptions, Dashboard, Reports)
- ✅ Super Admin (Create/Approve/Suspend gyms, change plans)
- ✅ 8 bugs fixed (see DEBUG.md for details)

**Phase 6 Security (applied 2026-02-09):**
- ✅ CORS locked down (only allowed origins in production)
- ✅ SECRET_KEY enforced via env var (no insecure default)
- ✅ DEBUG=False in production by default
- ✅ Login rate limiting (5 attempts/min per IP)
- ✅ Security headers (XSS, HSTS, SSL redirect)
- ✅ Superuser hardened (requires DJANGO_SUPERUSER_PASSWORD env var)
- ✅ Structured error logging configured

---

## ⚠️ Important Technical Notes

### Payment Logic:
- `member.amount_paid` = stored field, the reliable source for debt calculation
- `remaining_debt` = `membership_plan.price - amount_paid` (property)
- `perform_create` now records **actual payment amount** (not plan price) — fixed in Bug #5
- Old Payment records may have wrong amounts (full plan price instead of actual payment)

### Revenue Card:
- Shows **this month's** collected revenue (not daily or all-time)
- Progress bar compares against **best month ever**

### Revenue Chart:
- **Green (Paid)** = actual cash received
- **Pink (Pending)** = outstanding debts from members who paid in that period

---

## 🔧 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login/` | POST | Login (needs gym_slug) |
| `/api/auth/refresh/` | POST | Refresh JWT token |
| `/api/tenants/` | GET/POST | List/Create gyms |
| `/api/tenants/{id}/` | PATCH | Update gym (change plan) |
| `/api/tenants/{id}/approve/` | POST | Approve pending gym |
| `/api/tenants/{id}/reset-password/` | POST | Reset admin password |
| `/api/tenants/{id}/set-password/` | POST | Set custom password |
| `/api/users/change_password/` | POST | Change user's own password |
| `/api/members/` | GET/POST | List/Create members |
| `/api/attendance/` | GET/POST | Check-in/out members |
| `/api/reports/dashboard/` | GET | Dashboard metrics |
| `/api/reports/revenue-chart/` | GET | Revenue chart data |

---

## 📁 Super Admin Features

- ✅ Create Gym (auto-generates schema)
- ✅ Approve Gym (shows credentials)
- ✅ Suspend/Reactivate Gym
- ✅ Change Plan (Trial/Pro/Lifetime)
- ✅ Reset Admin Password (🔑 key icon)
- ✅ Set Custom Admin Password

---

## 💡 Commands

```bash
# Run Gym App
cd "C:\Users\HP PROBOOK\Desktop\Flutter GYM\app" && flutter run -d chrome

# Run Super Admin
cd C:\Users\HP PROBOOK\Desktop\super_admin && flutter run -d windows

# Run Super Admin (Web)
cd C:\Users\HP PROBOOK\Desktop\super_admin && flutter run -d chrome

# Recalculate member payments (if amount_paid gets corrupted)
# Run on Railway shell:
python manage.py recalculate_payments
```

---

## 🔒 Railway Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `SECRET_KEY` | *(auto-generated)* | Django secret key |
| `DATABASE_URL` | *(Railway auto)* | PostgreSQL connection |
| `DJANGO_SUPERUSER_PASSWORD` | `admin123` | Superuser auto-creation |
| `DJANGO_SUPERUSER_USERNAME` | `admin` | Default: admin |

---

## 🐛 Bug Tracking

All bugs and solutions documented in **`DEBUG.md`**.

| Bug # | Issue | Root Cause | Status |
|-------|-------|------------|--------|
| #1 | Create Gym 500 Error | Missing public tenant setup | ✅ SOLVED |
| #2 | Attendance Date NULL | Missing default date | ✅ SOLVED |
| #3 | Super Admin Dashboard 500 | Schema routing issue | ✅ SOLVED |
| #4 | Create Gym Dialog Overflow | UI layout issue | ✅ SOLVED |
| #5 | Payment Doubling on Create | amount_paid reset before Payment.save() | ✅ SOLVED |
| #6 | Revenue Card Scope | Changed from daily to monthly | ✅ SOLVED |
| #7 | Chart Paid/Pending Wrong | Was using debt status instead of actual payments | ✅ SOLVED |
| #8 | Debt Mismatch | remaining_debt uses amount_paid (not corrupt Payment records) | ✅ SOLVED |

> Check DEBUG.md when encountering errors!

---

*Last Updated: 2026-02-09 01:14*
