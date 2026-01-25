# How to Host Your Django Project on the Web (Free)

This guide uses **Render.com**, which is one of the easiest and best free platforms for hosting Django apps.

## 1. Prepare Your Code
I have already updated your code to be "Production Ready":
- Added `gunicorn` (Web Server) and `whitenoise` (Static Files) to `requirements.txt`.
- Configured `settings.py` to serve static files correctly.
- Created a `build.sh` script to automate setup.

**Important:** You must push these changes to GitHub before proceeding.
1. Create a repository on [GitHub](https://github.com/new).
2. Run these commands in your `GYM` folder:
   ```bash
   git init
   git add .
   git commit -m "Prepare for deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

---

## 2. Create an Account on Render
1. Go to [dashboard.render.com](https://dashboard.render.com/).
2. Sign up with your **GitHub** account.

---

## 3. Create the Database (PostgreSQL)
1. Click **New +** and select **PostgreSQL**.
2. **Name:** `gym-db` (or any name).
3. **Region:** Choose the one closest to you (e.g., Frankfurt).
4. **Instance Type:** Select **Free**.
5. Click **Create Database**.
6. **Wait** a moment, then copy the **Internal Database URL** (begins with `postgres://...`). You will need this soon.

---

## 4. Deploy the App (Web Service)
1. Go back to the Dashboard.
2. Click **New +** and select **Web Service**.
3. Connect your **GitHub Project**.
4. Configure the settings:
   - **Name:** `gym-backend`
   - **Region:** Same as your database.
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn gym_management.wsgi:application`
   - **Instance Type:** Free.
5. **Environment Variables** (Click "Advanced" or "Environment"):
   Add the following keys and values:
   
   | Key | Value |
   | :--- | :--- |
   | `PYTHON_VERSION` | `3.10.0` |
   | `DATABASE_URL` | *(Paste the Internal Database URL from Step 3)* |
   | `SECRET_KEY` | `some-random-complex-string-for-security` |
   | `DEBUG` | `False` |

6. Click **Create Web Service**.

---

## 5. Done!
Render will now download your code, install dependencies, and start the server. 
Once it says **Live**, you will get a URL like `https://gym-backend.onrender.com`.

**Next Step for Flutter App:**
Update your Flutter app's `api_client.dart` and `auth_service.dart` to use this new `https://gym-backend.onrender.com` URL instead of `http://127.0.0.1:8000`.
