import os
import sys
import time
import socket
import psycopg2
from urllib.parse import urlparse

def wait_for_postgres():
    """Wait for PostgreSQL to be available."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("[Boot] DATABASE_URL not set!")
        return
        
    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    
    print(f"[Boot] Waiting for database at {hostname}:{port}...")
    
    start_time = time.time()
    while True:
        try:
            conn = psycopg2.connect(
                dbname=database,
                user=username,
                password=password,
                host=hostname,
                port=port,
                connect_timeout=3
            )
            conn.close()
            print("[Boot] Database is ready!")
            break
        except psycopg2.OperationalError as e:
            if time.time() - start_time > 60:
                print(f"[Boot] Timeout waiting for database: {e}")
                # We continue anyway to let Gunicorn try, as it might handle it
                break
            print(f"[Boot] Database not ready yet... waiting (Error: {str(e).strip()})")
            time.sleep(2)
        except Exception as e:
            print(f"[Boot] Error checking database: {e}")
            break

def main():
    # 1. Wait for DB (critical for Railway cold starts)
    wait_for_postgres()
    
    # 2. Run Gunicorn
    print("[Boot] Starting Gunicorn...")
    
    # Use explicit flags for maximum reliability
    # workers=1 (save memory)
    # threads=4 (concurrency)
    # timeout=120 (prevent 502s)
    # log-level=debug (see everything)
    os.execvp("gunicorn", [
        "gunicorn", 
        "gym_management.wsgi:application",
        "--bind", "0.0.0.0:" + os.environ.get("PORT", "8000"),
        "--workers", "1",
        "--threads", "4",
        "--worker-class", "gthread",
        "--timeout", "120",
        "--log-level", "debug",
        "--access-logfile", "-",
        "--error-logfile", "-"
    ])

if __name__ == "__main__":
    main()
