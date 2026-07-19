import psycopg2
conn = psycopg2.connect(
    dbname="postgres", user="postgres", password="mo22zy", host="127.0.0.1", port="5432"
)
conn.set_isolation_level(0)
cur = conn.cursor()
cur.execute("""
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'test_rest_db'
      AND pid <> pg_backend_pid()
""")
cur.execute("DROP DATABASE IF EXISTS test_rest_db")
cur.close()
conn.close()
print("Done")
