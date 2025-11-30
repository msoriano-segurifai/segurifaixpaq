"""
Initialize PostgreSQL database for SegurifAI
This script attempts to create the database using different methods
"""
import sys
import os
import subprocess
import getpass

def method1_python():
    """Try creating database using Python and psycopg2"""
    try:
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        print("=== Method 1: Using Python/psycopg2 ===")
        password = getpass.getpass("Enter PostgreSQL password for user 'postgres': ")

        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user='postgres',
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'segurifai_db'")
        if cursor.fetchone():
            print("Database 'segurifai_db' already exists!")
        else:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('segurifai_db')))
            print("Database 'segurifai_db' created successfully!")

        cursor.close()
        conn.close()

        # Update .env file with the correct password
        update_env_password(password)
        return True

    except Exception as e:
        print(f"Failed: {e}\n")
        return False


def method2_psql():
    """Try creating database using psql command"""
    try:
        print("=== Method 2: Using psql command ===")
        psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"

        if not os.path.exists(psql_path):
            print(f"psql not found at {psql_path}")
            return False

        password = getpass.getpass("Enter PostgreSQL password for user 'postgres': ")

        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password

        # Try to create database
        result = subprocess.run(
            [psql_path, '-U', 'postgres', '-c', 'CREATE DATABASE segurifai_db;'],
            env=env,
            capture_output=True,
            text=True
        )

        if 'already exists' in result.stderr:
            print("Database 'segurifai_db' already exists!")
            update_env_password(password)
            return True
        elif result.returncode == 0:
            print("Database 'segurifai_db' created successfully!")
            update_env_password(password)
            return True
        else:
            print(f"Failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"Failed: {e}\n")
        return False


def update_env_password(password):
    """Update .env file with the correct password"""
    try:
        env_path = '.env'
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()

            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('DB_PASSWORD='):
                        f.write(f'DB_PASSWORD={password}\n')
                    else:
                        f.write(line)
            print("Updated .env file with PostgreSQL password")
    except Exception as e:
        print(f"Warning: Could not update .env file: {e}")


def main():
    print("SegurifAI PostgreSQL Database Setup")
    print("=" * 50)
    print()

    # Try Method 1 (Python)
    if method1_python():
        print("\n✓ Database setup complete!")
        print("\nNext steps:")
        print("1. Run migrations: python manage.py migrate")
        print("2. Create superuser: python manage.py createsuperuser")
        print("3. Start server: python manage.py runserver")
        return

    # Try Method 2 (psql)
    if method2_psql():
        print("\n✓ Database setup complete!")
        print("\nNext steps:")
        print("1. Run migrations: python manage.py migrate")
        print("2. Create superuser: python manage.py createsuperuser")
        print("3. Start server: python manage.py runserver")
        return

    # If all methods fail
    print("\n✗ Could not create database automatically")
    print("\nManual setup required:")
    print("1. Open pgAdmin or psql")
    print("2. Connect as postgres user")
    print("3. Run: CREATE DATABASE segurifai_db;")
    print("4. Update DB_PASSWORD in .env file")
    print("5. Run: python manage.py migrate")


if __name__ == "__main__":
    main()
