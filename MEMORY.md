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
| Phase 6: Production | ❌ Pending | Security, docs |

### 📍 WHERE WE ARE NOW:
- ✅ **Create Gym** working
- ✅ **Password Management** - Reset Password, Set Custom Password
- ✅ **Credentials shown on approve**
- ⏭️ Next: Phase 6 (Security & Docs)

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

> Check DEBUG.md when encountering errors!

---

*Last Updated: 2026-02-08 21:38*
