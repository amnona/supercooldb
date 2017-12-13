#!/usr/bin/env python

# add greengenes closed reference ids to database sequences

import sys

import argparse
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


def get_sequences_fasta(filename, servertype='main', overwrite=False):
	'''
	Get all database sequences into a fasta file

	Parameters
	----------
	filename : str
		name of the fasta file to save to
	servertype : str (optional)
		database to connect to ('main' or 'develop' or 'local')
	overwrite : bool
		False (default) to get only sequences without ggid in database
		True to get all sequences
	'''
	con, cur = connect_db(servertype=servertype)
	cur.execute('SELECT id,sequence,ggid FROM SequencesTable')
	fl=open(filename,'w')
	for cres in cur:
		saveit = True
		if not overwrite:
			if cres[2] > 0:
				saveit = False
		if saveit:
			fl.write('>%s\n%s\n' % (cres[0], cres[1]))
	fl.close()


def add_sequence_ggids(rdpfilename, overwrite=False, servertype='main'):
	'''
	Add taxonomies from an RDP output file to the database

	Parameters:
	rdpfilename : str
		name of the RDP output file (run on fasta from get_sequences_fasta)
	servertype : str (optional)
		database to connect to ('main' or 'develop' or 'local')
	'''
	con, cur = connect_db(servertype=servertype)
	fl=open(rdpfilename,'r')
	for cline in fl:
		cc=cline.split('\t')
		cggid = cc[0]
		csim = cc[1]
		cid = cc[2]

		cur.execute('SELECT ggid from SequencesTable WHERE id=%s',[cid])
		if cur.rowcount==0:
			print('id %s not found in database!' % cid)
			continue
		dbggid = cur.fetchone()[0]
		writeit = True
		if not overwrite:
			if int(dbggid)>0:
				print('skipping %d' % int(dbggid))
				writeit = False
		print('cid %s, cggid %s' % (cid, cggid))
		if writeit:
			print('write')
			cur.execute('UPDATE SequencesTable SET ggid=%s WHERE id=%s',[cggid,cid])
	con.commit()


def main(argv):
	parser=argparse.ArgumentParser(description='Add greengenesids to database sequences. version '+__version__)
	parser.add_argument('-f','--filename',help='name of output fasta or input greengenesids file')
	parser.add_argument('--db',help='name of database to connect to (main/develop/local)', default='main')
	parser.add_argument('-a','--action',help='action to perform: "save" to save to fasta or "ggid" to load closed-reference results', default='save')
	parser.add_argument('--overwrite',help='overwrite sequences with taxonomy present', action='store_true')
	args=parser.parse_args(argv)
	if args.action=='save':
		get_sequences_fasta(filename=args.filename, servertype=args.db, overwrite=args.overwrite)
	elif args.action=='ggid':
		add_sequence_ggids(rdpfilename=args.filename, overwrite=args.overwrite, servertype=args.db)
	else:
		print('action %s unknown' % args.action)

if __name__ == "__main__":
	main(sys.argv[1:])
