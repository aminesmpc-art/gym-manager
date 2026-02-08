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
| Phase 1: Foundation | ✅ DONE | Demographics fix, JWT login |
| Phase 2: Super Admin API | ✅ DONE | Tenant CRUD, gym stats |
| Phase 3: Gym Onboarding | ✅ DONE | Self-registration, admin creation |
| Phase 4: Billing | ✅ DONE | Change Plan, cash-based workflow |
| Phase 5: Customer Experience | ✅ DONE | Already exists in Gym App |
| Phase 6: Production | ❌ Pending | Security, docs |

### 📍 WHERE WE ARE NOW:
- ✅ **Create Gym** working (LAACHIRI created successfully!)
- ✅ **DEBUG.md** tracks all bugs & solutions
- ⏭️ Next: Approve gym → Test gym login → Phase 6

---

## 🔧 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login/` | POST | Login (needs gym_slug) |
| `/api/tenants/admin/reset-demo/?secret=gym_reset_2026` | POST | Reset demo to 120 members |
| `/api/tenants/` | GET/POST | List/Create gyms |
| `/api/tenants/{id}/` | PATCH | Update gym (change plan) |
| `/api/users/change_password/` | POST | Change user password |

---

## 📁 Key Features in Gym App (Settings)

### Account Settings:
- ✅ Change Password
- ✅ Session Management
- ✅ Permissions View

### Data Export:
- ✅ Export Members CSV
- ✅ Export Attendance CSV
- ✅ Export Staff CSV

---

## 💡 Commands

```bash
# Run Gym App
cd "C:\Users\HP PROBOOK\Desktop\Flutter GYM\app" && flutter run -d chrome

# Run Super Admin
cd C:\Users\HP PROBOOK\Desktop\super_admin && flutter run -d chrome

# Reset Demo Data
POST /api/tenants/admin/reset-demo/?secret=gym_reset_2026
```

---

## 🐛 Bug Tracking

All bugs and their solutions are documented in **`DEBUG.md`**.

> **Always check DEBUG.md** when encountering errors - the solution might already be there!

---

*Last Updated: 2026-02-08 18:54*
