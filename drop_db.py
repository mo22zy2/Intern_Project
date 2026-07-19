import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Rest_project.settings'
django.setup()
from django.db import connection
conn = connection.cursor()
conn.connection.set_isolation_level(0)
conn.execute("""
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'test_rest_db'
  AND pid <> pg_backend_pid()
""")
conn.execute('DROP DATABASE IF EXISTS test_rest_db')
conn.connection.set_isolation_level(1)
print('Done')
