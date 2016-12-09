import psycopg2
import psycopg2.extras
from utils import debug
import os


def connect_db(schema='AnnotationSchemaTest'):
	"""
	connect to the postgres database and return the connection and cursor
	input:

	output:
	con : the database connection
	cur : the database cursor
	"""
	debug(1,'connecting to database')
	try:
		#database='scdb'
		#user='scdb'
		#password='magNiv'
		#port=29546
		database = 'scdb'
		user = 'postgres'
		password = 'admin123'
		port=5432
		host='localhost'
		if 'SCDB_SERVER_TYPE' in os.environ:
			servertype=os.environ['SCDB_SERVER_TYPE'].lower()
			debug(1,'SCDB_SERVER_TYPE is %s' % servertype)
			if servertype=='develop':
				debug(1,'servertype is main')
				database='scdb'
				user='scdb'
				password='magNiv'
				port=29546
			if servertype=='develop':
				debug(1,'servertype is develop')
				database='scdb_develop'
				user='scdb'
				password='magNiv'
				port=29546
			elif servertype=='local':
				debug(1,'servertype is local')
				database='postgres'
				user='postgres'
				password='admin123'
				port=5432
			else:
				debug(6,'unknown server type %s' % servertype)
				print('unknown server type %s' % servertype)
		else:
			debug(6,'server type not set (SCDB_SERVER_TYPE)')
			print('SCDB_SERVER_TYPE not set')
		debug(1,'connecting host=%s, database=%s, user=%s, port=%d' % (host,database,user,port))
		con = psycopg2.connect(host=host,database=database, user=user, password=password, port=port)
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SET search_path to %s' % schema)
		debug(1,'connected to database')
		return (con,cur)
	except psycopg2.DatabaseError as e:
		print ('Cannot connect to database. Error %s' % e)
		raise SystemError('Cannot connect to database. Error %s' % e)
		return None
