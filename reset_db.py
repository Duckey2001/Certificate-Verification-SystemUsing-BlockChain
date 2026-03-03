import psycopg2
from psycopg2 import sql

try:
    # Connect to default postgres database
    conn = psycopg2.connect(
        dbname="postgres",
        user="diploma_admin",
        password="diploma1234",
        host="localhost"
    )
    conn.autocommit = True
    
    cur = conn.cursor()
    
    print("Dropping old database...")
    cur.execute("DROP DATABASE IF EXISTS diploma_verification;")
    
    print("Creating fresh database...")
    cur.execute("CREATE DATABASE diploma_verification OWNER diploma_admin;")
    
    print("Granting privileges...")
    cur.execute("GRANT ALL PRIVILEGES ON DATABASE diploma_verification TO diploma_admin;")
    
    cur.close()
    conn.close()
    
    print("✓ Database reset complete!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
