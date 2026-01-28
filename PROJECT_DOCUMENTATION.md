# Gym Management System - Django Backend

A comprehensive REST API backend for managing gym operations including members, subscriptions, attendance, and staff payroll.

---

## Tech Stack

| Component | Technology |
|:---|:---|
| Framework | Django 5.0 + Django REST Framework |
| Database | PostgreSQL (Supabase) |
| Authentication | JWT (SimpleJWT) |
| Server | Gunicorn + WhiteNoise |

---

## Quick Start

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

Server runs at: **http://127.0.0.1:8000/**

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|:---|:---|:---|
| POST | `/api/auth/login/` | Get JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |

### Members
| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/members/` | List members |
| POST | `/api/members/` | Create member (auto-creates user + payment) |
| GET | `/api/members/{id}/` | Get member details |
| PUT | `/api/members/{id}/` | Update member |
| DELETE | `/api/members/{id}/` | Archive member |
| POST | `/api/members/{id}/renew_subscription/` | Renew subscription |
| POST | `/api/members/{id}/toggle_active/` | Suspend/activate |

### Subscriptions (Payments)
| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/subscriptions/` | List payments |
| POST | `/api/subscriptions/` | Record payment |

### Attendance
| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/attendance/` | List attendance |
| POST | `/api/attendance/` | Check in member |

### Staff & Payroll
| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/users/?role=STAFF` | List staff |
| POST | `/api/users/` | Create staff user |
| GET | `/api/staff-payments/` | List salary payments |
| POST | `/api/staff-payments/` | Record salary payment |

### Gym Configuration
| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/gym/activities/` | List activity types |
| GET | `/api/gym/plans/` | List membership plans |
| GET | `/api/gym/info/` | Get gym info |

### Reports
| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/reports/dashboard/` | Dashboard metrics |

---

## User Roles

| Role | Permissions |
|:---|:---|
| **ADMIN** | Full access to everything |
| **STAFF** | Manage members, payments, attendance (can be restricted by gender) |
| **MEMBER** | View own profile, payments, attendance |

---

## Data Models

### Member
- Personal info (name, phone, email, DOB, gender)
- Emergency contact
- Linked to ActivityType and MembershipPlan
- Auto-calculated membership status (ACTIVE/EXPIRED/PENDING)
- Archive support (soft delete)

### Payment
- Records subscription payments
- Auto-updates member subscription dates on save

### Attendance
- One check-in per member per day
- Requires active membership

### StaffPayment
- Monthly salary tracking
- Prevents duplicate payments for same period

---

## Management Commands

```bash
# Create admin user
python manage.py createsuperuser

# Seed 300 test members
python manage.py seed_members

# Change password
python manage.py changepassword <username>
```

---

## Project Structure

```
GYM/
├── gym_management/     # Main settings & URLs
│   ├── settings.py
│   ├── urls.py
│   └── permissions.py
├── users/              # User model & staff payments
├── gym/                # Activities & plans
├── members/            # Member management
├── subscriptions/      # Payment tracking
├── attendance/         # Daily check-ins
└── reports/            # Dashboard API
```

---

## Environment Variables

Create `.env` file:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:pass@host:5432/dbname
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Admin Panel

Access Django Admin at: **http://127.0.0.1:8000/admin/**

Features:
- Colored status badges for members
- Days remaining display
- Search and filter capabilities
- Staff role management
