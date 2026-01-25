# Gym Management System - Installation Guide

Follow these steps to set up the Gym Management System on a new laptop.

## 1. Prerequisites
Ensure the target laptop has the following installed:
- **Python (3.10+)**: [Download Here](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation)
- **Flutter SDK**: [Download Here](https://docs.flutter.dev/get-started/install/windows)
- **Git**: [Download Here](https://git-scm.com/downloads)
- **VS Code** (Optional, recommended for editing).

---

## 2. Backend Setup (Django)

This backend handles the database and API.

1.  **Copy the `GYM` folder** to the new laptop (e.g., `C:\Projects\GYM`).
2.  Open a terminal (Command Prompt or PowerShell) and navigate to the folder:
    ```powershell
    cd C:\Projects\GYM
    ```
3.  **Create a Virtual Environment** (Recommended):
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
4.  **Install Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```
5.  **Initialize the Database**:
    By default, the system will use a local SQLite file (`db.sqlite3`). No complex database setup is required.
    ```powershell
    python manage.py migrate
    ```
6.  **Create an Admin Account**:
    ```powershell
    python manage.py createsuperuser
    ```
    Follow the prompts to set a username and password.
7.  **Run the Server**:
    ```powershell
    python manage.py runserver
    ```
    *Keep this terminal open! The server is running at `http://127.0.0.1:8000/`.*

---

## 3. Frontend Setup (Flutter)

This is the mobile/desktop app interface.

1.  **Copy the `Flutter GYM` folder** to the new laptop.
2.  Open a **new** terminal and navigate to the `app` folder:
    ```powershell
    cd "C:\Projects\Flutter GYM\app"
    ```
3.  **Install Dependencies**:
    ```powershell
    flutter pub get
    ```
4.  **Run the App**:
    For the easiest experience on Windows, run it as a Windows Desktop app:
    ```powershell
    flutter run -d windows
    ```

---

## 4. Connecting a Physical Phone (Optional)

If you want to run the app on a real Android/iOS phone instead of Windows:

1.  **Find your Laptop's IP Address**:
    Run `ipconfig` in the terminal and find the IPv4 Address (e.g., `192.168.1.15`).
2.  **Update the Code**:
    Open these two files in VS Code or Notepad:
    *   `lib/core/network/api_client.dart`
    *   `lib/core/services/auth_service.dart`
    
    Change `http://127.0.0.1:8000` to your IP address, e.g., `http://192.168.1.15:8000`.
3.  **Run the Backend on 0.0.0.0**:
    Restart the backend server with this command so it accepts external connections:
    ```powershell
    python manage.py runserver 0.0.0.0:8000
    ```
4.  **Run the Flutter App**:
    Connect your phone via USB and run:
    ```powershell
    flutter run
    ```
