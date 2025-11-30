# Quick Database Setup - 30 Seconds

## Using pgAdmin (Recommended - No Password Needed)

1. **Open pgAdmin 4** from your Start Menu
2. In the left panel, expand **Servers** → **PostgreSQL 18**
3. Right-click on **Databases** → **Create** → **Database...**
4. Enter name: **segurifai**
5. Click **Save**

**Done!** Now run in terminal:

```bash
cd "c:\Users\escog\OneDrive\Documents\segurifai x paq"
venv\Scripts\activate
python manage.py migrate
python populate_test_data.py
python manage.py runserver
```

## Alternative: SQL Shell Method

1. Open **SQL Shell (psql)** from Start menu
2. Press Enter 4 times to accept defaults
3. Enter your postgres password
4. Type: `CREATE DATABASE segurifai;`
5. Type: `\q`

Then run the migration commands above.

---

**I'm ready to run migrations immediately** once you create the database!
