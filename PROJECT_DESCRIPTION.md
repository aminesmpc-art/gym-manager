# Gym Management System - Project Overview

This project is a complete solution for managing a gym, consisting of a robust **Django Backend** and a modern **Flutter Frontend**.

---

## 1. Backend (API)
**Path:** `...\Desktop\GYM`
**Status:** Active Django REST Framework project.

### Tech Stack
- **Framework:** Django & Django REST Framework (DRF)
- **Database:** PostgreSQL (configured in `.env`)
- **Authentication:** JWT (JSON Web Tokens) with Role-Based Access Control (Admin, Staff, Member)

### Key Modules (Apps)
| App Name | Description |
| :--- | :--- |
| **`users`** | Manages custom user models and roles (`ADMIN`, `STAFF`, `MEMBER`). |
| **`members`** | Handles member profiles, personal details, and emergency contacts. |
| **`gym`** | Core configuration like `MembershipPlan` and `ActivityType`. |
| **`subscriptions`** | Manages payment records, plan validity, and renewals. |
| **`attendance`** | Tracks daily member check-ins and history. |
| **`reports`** | Generates aggregated business metrics and analytics. |

### Key Commands
- **Run Server:** `python manage.py runserver`
- **Create Admin:** `python manage.py createsuperuser`
- **Migrations:** `python manage.py migrate`

---

## 2. Frontend (Mobile/Web App)
**Path:** `...\Desktop\Flutter GYM\app`
**Status:** Flutter application with a feature-first architecture.

### Tech Stack
- **Framework:** Flutter (Dart)
- **State Management:** `provider` package
- **Networking:** `http` package
- **Design:** Modern, clean corporate aesthetic (Open Sans / Poppins fonts).

### App Structure (`lib/features/`)
The app is organized by feature for scalability:
- **`auth/`**: Login screens and authentication logic.
- **`dashboard/`**: Main landing, displaying gym statistics (active members, revenue, etc.).
- **`members/`**: Complete member management (List view, Add Member, Edit Member).
- **`checkin/`**: Attendance system for checking members in.
- **`settings/`**: Application configuration.

---

## 3. Development & Testing
- **Test Data:** You have a `seed_test_data.py` script (located in the Flutter folder) designed to populate the backend with 200+ test members for stress testing and UI verification.
- **Environment:** The backend relies on a virtual environment (`venv`) which should be activated before running.
