#!/usr/bin/env python

import sys

import argparse
import psycopg2

__version__ = "1.1"


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
		print ('Cannot connect to database. Error %s' % e)
		raise SystemError('Cannot connect to database. Error %s' % e)
		return None


def get_sequences_fasta(filename, servertype='main'):
	'''
	Get all database sequences into a fasta file

	Parameters
	----------
	filename : str
		name of the fasta file to save to
	servertype : str (optional)
		database to connect to ('main' or 'develop' or 'local')
	'''
	con, cur = connect_db(servertype=servertype)
	cur.execute('SELECT id,sequence,taxonomy FROM SequencesTable')
	for cres in cur:
		pass
	print('id %s, sequence %s, taxonomy %s' % (cres[0],cres[1],cres[2]))


def main(argv):
	parser=argparse.ArgumentParser(description='Add taxonomies to database sequences. version '+__version__)
	parser.add_argument('-f','--fasta',help='name of fasta file')
	parser.add_argument('--db',help='name of database to connect to', default='main')
	args=parser.parse_args(argv)
	get_sequences_fasta(filename=args.fasta, servertype=args.db)

if __name__ == "__main__":
	main(sys.argv[1:])
