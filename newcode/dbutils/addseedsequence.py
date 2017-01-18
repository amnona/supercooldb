#!/usr/bin/env python

import sys

import argparse
import psycopg2
import psycopg2.extras

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


def add_seed_sequence(length=100, servertype='main'):
	'''
	Add the seed sequence field to each sequence in sequecestable

	Parameters
	----------
	length : int (optional)
		the length of the seed sequence
	servertype : str (optional)
		database to connect to ('main' or 'develop' or 'local')
	'''
	con, cur = connect_db(servertype=servertype)
	cur.execute('SELECT id,sequence FROM SequencesTable')
	numadded=0
	res=cur.fetchall()
	for cres in res:
		cid=cres[0]
		cseq=cres[1]
		if len(cseq)<length:
			continue
		cseedseq=cseq[:length]
		cur.execute('UPDATE SequencesTable SET seedsequence=%s WHERE id=%s',[cseedseq,cid])
		numadded+=1
	con.commit()
	print('added %d seed sequences of length %d' % (numadded, length))


def main(argv):
	parser=argparse.ArgumentParser(description='Add seed sequence to sequences table. version '+__version__)
	parser.add_argument('-l','--length',help='length of seed sequence',default=100, type=int)
	parser.add_argument('--db',help='name of database to connect to (main/develop/local)', default='main')
	args=parser.parse_args(argv)
	add_seed_sequence(length=args.length, servertype=args.db)

if __name__ == "__main__":
	main(sys.argv[1:])
