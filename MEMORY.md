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
- **Backend URL**: `https://gym-backend-production-1547.up.railway.app`
- **Database**: PostgreSQL on Railway
- **Multi-tenant**: django-tenants (each gym = separate schema)

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
| Phase 1-5 | ✅ DONE | All core features |
| Password Management | ✅ DONE | Reset/Set admin passwords |
| Bug Fixes | ✅ DONE | See DEBUG.md (8 bugs fixed) |
| Phase 6: Production | ✅ DONE | Security hardening |

### 📍 WHERE WE ARE NOW (2026-02-09):
- ✅ **All core features** working
- ✅ **8 bugs fixed** (see DEBUG.md)
- ✅ **CORS locked down** (only allowed origins in production)
- ✅ **SECRET_KEY enforced** (no insecure default)
- ✅ **DEBUG=False** in production
- ✅ **Login rate limiting** (5 attempts/min per IP)
- ✅ **Security headers** enabled in production
- ✅ **Superuser hardened** (requires env var)
- ✅ **Error logging** configured
- 🎉 **Production ready!**

---

## 🔧 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login/` | POST | Login (needs gym_slug) |
| `/api/tenants/` | GET/POST | List/Create gyms |
| `/api/tenants/{id}/` | PATCH | Update gym (change plan) |
| `/api/tenants/{id}/approve/` | POST | Approve pending gym |
| `/api/tenants/{id}/reset-password/` | POST | Reset admin password |
| `/api/tenants/{id}/set-password/` | POST | Set custom password |
| `/api/users/change_password/` | POST | Change user's own password |

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
```

---

## 🐛 Bug Tracking

All bugs and solutions documented in **`DEBUG.md`**.

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

> Check DEBUG.md when encountering errors!

---

*Last Updated: 2026-02-09 00:30*

