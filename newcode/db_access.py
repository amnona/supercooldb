import psycopg2
import psycopg2.extras


def connect_db(schema='AnnotationSchemaTest'):
	"""
	connect to the postgres database and return the connection and cursor
	input:

	output:
	con : the database connection
	cur : the database cursor
	"""
	try:
		con = psycopg2.connect(database='postgres', user='postgres', password='admin123')
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SET search_path to %s' % schema)
		return (con,cur)
	except psycopg2.DatabaseError as e:
		print ('Cannot connect to database. Error %s' % e)
		return None
