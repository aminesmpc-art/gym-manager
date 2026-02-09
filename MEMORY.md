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

> ⚠️ **CRITICAL: There are multiple Railway projects. Only ONE is the real backend:**

| Railway Project | URL | Has DB? | Status |
|----------------|-----|---------|--------|
| **fearless-mindfulness** ✅ | `gym-backend-production-1547.up.railway.app` | ✅ Yes | **THE REAL BACKEND** |
| intelligent-vitality ❌ | `web-production-6b8db.up.railway.app` | ❌ No DB | IGNORE — wrong project |

**Always use:** `https://gym-backend-production-1547.up.railway.app`

**Railway CLI must be linked to:**
```bash
Project: fearless-mindfulness
Service: gym-backend
```

To verify: `railway status` → should show `fearless-mindfulness`
To re-link: `railway link` → select `fearless-mindfulness` → `gym-backend`

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
| Password Mgmt | ✅ DONE | Reset/Set admin passwords |
| Bug Fixes | ✅ DONE | 9 bugs fixed (see DEBUG.md) |
| Phase 6 | ✅ DONE | Security hardening |

### 📍 WHERE WE ARE NOW (2026-02-09):

**All features complete + production-ready!**

- ✅ All core features (Members, Attendance, Subscriptions, Dashboard, Reports)
- ✅ Super Admin (Create/Approve/Suspend gyms, change plans)
- ✅ 9 bugs fixed (see DEBUG.md for details)

**Phase 6 Security (applied 2026-02-09):**
- ✅ SECRET_KEY safe (with build-time fallback, requires env var in production)
- ✅ DEBUG=False in production by default
- ✅ Login rate limiting (5 attempts/min per IP)
- ✅ Security headers (XSS, HSTS, secure cookies)
- ✅ Superuser hardened (requires DJANGO_SUPERUSER_PASSWORD env var)
- ✅ Structured error logging configured
- ✅ CORS open for Flutter apps (JWT-based auth, not cookie-based)

---

## ⚠️ Important Technical Notes

### Railway Deployment:
- **Docker-based** deployment via `Dockerfile`
- `collectstatic` runs at BUILD time (no env vars available yet)
-`migrate` + `gunicorn` run at RUNTIME (env vars available)
- `SECRET_KEY` has a safe build-time fallback — real key is set via env var
- **Do NOT enable `SECURE_SSL_REDIRECT`** — Railway handles SSL at the proxy level

### Payment Logic:
- `member.amount_paid` = stored field, the reliable source for debt calculation
- `remaining_debt` = `membership_plan.price - amount_paid` (property)
- `perform_create` records **actual payment amount** (not plan price)
- Old Payment records may have wrong amounts (full plan price instead of actual)

### Revenue Card:
- Shows **this month's** collected revenue (not daily or all-time)
- Progress bar compares against **best month ever**

### Revenue Chart:
- **Green (Paid)** = actual cash received
- **Pink (Pending)** = outstanding debts

---

## 🔧 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login/` | POST | Login (needs gym_slug) — **rate limited** |
| `/api/auth/refresh/` | POST | Refresh JWT token |
| `/api/tenants/` | GET/POST | List/Create gyms |
| `/api/tenants/{id}/approve/` | POST | Approve pending gym |
| `/api/tenants/{id}/reset-password/` | POST | Reset admin password |
| `/api/tenants/{id}/set-password/` | POST | Set custom password |
| `/api/members/` | GET/POST | List/Create members |
| `/api/attendance/` | GET/POST | Check-in/out members |
| `/api/reports/dashboard/` | GET | Dashboard metrics |

---

## 📁 Super Admin Features

- ✅ Create Gym (auto-generates schema)
- ✅ Approve Gym (shows credentials)
- ✅ Suspend/Reactivate Gym
- ✅ Change Plan (Trial/Pro/Lifetime)
- ✅ Reset Admin Password
- ✅ Set Custom Admin Password

---

## 💡 Commands

```bash
# Run Gym App
cd "C:\Users\HP PROBOOK\Desktop\Flutter GYM\app" && flutter run -d chrome

# Run Super Admin
cd C:\Users\HP PROBOOK\Desktop\super_admin && flutter run -d chrome

# Verify Railway is linked correctly
railway status  # Must show: fearless-mindfulness / gym-backend

# Re-link Railway if wrong
railway link  # Select: fearless-mindfulness → gym-backend
```

---

## 🔒 Railway Environment Variables (fearless-mindfulness)

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret key (already set) |
| `DATABASE_URL` | PostgreSQL connection (auto from Railway DB) |
| `DJANGO_SUPERUSER_PASSWORD` | Superuser auto-creation |
| `ALLOWED_HOSTS` | Set to `*` |

---

## 🐛 Bug Tracking

All bugs documented in **`DEBUG.md`**.

| Bug # | Issue | Status |
|-------|-------|--------|
| #1 | Create Gym 500 Error | ✅ SOLVED |
| #2 | Attendance Date NULL | ✅ SOLVED |
| #3 | Super Admin Dashboard 500 | ✅ SOLVED |
| #4 | Create Gym Dialog Overflow | ✅ SOLVED |
| #5 | Payment Doubling on Create | ✅ SOLVED |
| #6 | Revenue Card Scope (monthly) | ✅ SOLVED |
| #7 | Chart Paid/Pending Wrong | ✅ SOLVED |
| #8 | Debt Mismatch Card vs Badges | ✅ SOLVED |
| #9 | Backend 500 after security changes | ✅ SOLVED |

---

*Last Updated: 2026-02-09 21:50*
