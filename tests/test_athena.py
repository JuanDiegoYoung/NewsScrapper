from pyathena import connect

conn = connect(
    s3_staging_dir='s3://jd-athena-results-20251112/',
    region_name='us-east-1',
    work_group='primary'
)

cursor = conn.cursor()
cursor.execute('SELECT * FROM information_schema.tables LIMIT 5;')
for row in cursor:
    print(row)
