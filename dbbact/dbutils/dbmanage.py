#!/usr/bin/env python

import click
import psycopg2
import psycopg2.extras

__version__ = "0.1"


def debug(level,msg):
	print(msg)


def connect_db(servertype='main', schema='AnnotationSchemaTest'):
	"""
	connect to the postgres database and return the connection and cursor
	input:
	servertype : str (optional)
		the database to access. options are:
			'main' (default) - the main remote production database
			'develop' - the remote development database
			'local' - a local postgres instance of the database
	schema : str (optional)
		name of the schema containing the annotation database

	output:
	con : the database connection
	cur : the database cursor
	"""
	debug(1,'connecting to database')
	try:
		database = 'scdb'
		user = 'postgres'
		password = 'admin123'
		port=5432
		host='localhost'
		if servertype=='main':
			debug(1,'servertype is main')
			database='scdb'
			user='scdb'
			password='magNiv'
			port=29546
		elif servertype=='develop':
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
		elif servertype=='mac':
			debug(1,'servertype is mac')
			database='dbbact'
			user='postgres'
			password='admin123'
			port=5432
		elif servertype=='openu':
			debug(1, 'servertype is openu')
			database = 'scdb'
			user = 'postgres'
			password = 'magNiv'
			port = 5432
		else:
			debug(6,'unknown server type %s' % servertype)
			print('unknown server type %s' % servertype)
		debug(1,'connecting host=%s, database=%s, user=%s, port=%d' % (host,database,user,port))
		con = psycopg2.connect(host=host,database=database, user=user, password=password, port=port)
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SET search_path to %s' % schema)
		debug(1,'connected to database')
		return (con,cur)
	except psycopg2.DatabaseError as e:
		print('Cannot connect to database. Error %s' % e)
		raise SystemError('Cannot connect to database. Error %s' % e)
		return None


@click.group()
def dbmanage_cmds():
	# database manage commands
	pass


@dbmanage_cmds.command()
@click.option('--expid', '-e', required=True, type=int, help='ExpID to fix')
@click.option('--name', '-n', required=True, type=str, help='name of field to modify (i.e. "name","sra"...)')
@click.option('--val', '-v', required=True, type=str, help='new value to put')
@click.option('--database', '-d', required=False, type=str, default='main', show_default=True, help='database to connect to')
def update_exp(expid, name, val, database):
	con, cur = connect_db(servertype=database)
	cur.execute('SELECT * from ExperimentsTable WHERE expid=%s', [expid])
	if cur.rowcount == 0:
			debug(9,'ExpID %s not found in database. Aborting' % expid)
			exit(1)
	res = cur.fetchall()
	debug(2,'found experiment with %d details:' % len(res))
	for cres in res:
		print(cres)
	ok = input('do you want to change %s to %s?' % (name, val))
	if ok != 'y':
		debug(9,'cancelled')
		exit(1)
	cur.execute('DELETE FROM ExperimentsTable WHERE ExpID=%s AND type=%s',[expid, name])
	cur.execute('INSERT INTO ExperimentsTable (expID, type, value, date, userid, private) VALUES (%s,%s,%s,%s,%s,%s)',[expid, name, val, cres['date'], cres['userid'], cres['private']])
	debug(2,'updated')
	con.commit()

if __name__ == '__main__':
	dbmanage_cmds()
