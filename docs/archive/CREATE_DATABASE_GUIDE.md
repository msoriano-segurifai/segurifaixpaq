# Create PostgreSQL Database for SegurifAI x PAQ

## Quick Setup - 2 Minutes

PostgreSQL is running on your system, but I need the correct password to create the database.

### Option 1: Using pgAdmin (Easiest)

1. Open **pgAdmin 4** from your Start menu
2. Connect to **PostgreSQL 18**
3. Right-click on **Databases** → **Create** → **Database**
4. Enter database name: `segurifai`
5. Click **Save**

### Option 2: Using Command Line

Open **Command Prompt** or **PowerShell** and run:

```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```

When prompted for password, enter your PostgreSQL password, then run:

```sql
DROP DATABASE IF EXISTS segurifai;
CREATE DATABASE segurifai;
\q
```

### Option 3: Using SQL Shell

1. Open **SQL Shell (psql)** from Start menu
2. Press Enter for defaults (localhost, 5432, postgres, postgres)
3. Enter your password
4. Run these commands:

```sql
DROP DATABASE IF EXISTS segurifai;
CREATE DATABASE segurifai;
\q
```

## After Creating the Database

Once the database is created, run these commands:

```bash
cd "c:\Users\escog\OneDrive\Documents\segurifai x paq"
venv\Scripts\activate
python manage.py migrate
python populate_test_data.py
python manage.py runserver
```

## Configuration Already Done

✅ `.env` file updated to use PostgreSQL
✅ Database name set to: `segurifai`
✅ psycopg2-binary installed in venv
✅ Database settings configured

## Need Help?

If you don't remember your PostgreSQL password, you can:
1. Reset it using pgAdmin
2. Or update the password in `.env` file after you find it

The password should be entered in line 14 of the `.env` file:
```
DB_PASSWORD=YOUR_PASSWORD_HERE
```
