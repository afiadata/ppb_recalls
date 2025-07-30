import os
import psycopg2
from dotenv import load_dotenv

# Load DB credentials from .env
load_dotenv()

CONNECTION_STRING = f"""
    dbname='{os.getenv("DB_NAME")}'
    user='{os.getenv("DB_USER")}'
    password='{os.getenv("DB_PASSWORD")}'
    host='{os.getenv("DB_HOST")}'
    port='{os.getenv("DB_PORT")}'
"""

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(CONNECTION_STRING)
    cur = conn.cursor()
    print("✅ Connected to PostgreSQL successfully.")

    # Enable pgvector if not already enabled
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    print("✅ pgvector extension is enabled.")

    # Create test table with vector column
    cur.execute("""
        DROP TABLE IF EXISTS test_vectors;
        CREATE TABLE test_vectors (
            id SERIAL PRIMARY KEY,
            name TEXT,
            embedding vector(3)  -- sample 3-dim vector
        );
    """)
    print("✅ Test table created.")

    # Insert a sample row
    cur.execute("""
        INSERT INTO test_vectors (name, embedding)
        VALUES ('sample', '[0.1, 0.2, 0.3]');
    """)
    conn.commit()
    print("✅ Sample vector inserted.")

    # Fetch and print inserted row
    cur.execute("SELECT * FROM test_vectors;")
    rows = cur.fetchall()
    print("✅ Fetched rows:")
    for row in rows:
        print(row)

    cur.close()
    conn.close()

except Exception as e:
    print("Error occurred:", e) 
