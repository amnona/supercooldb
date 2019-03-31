#!/usr/bin/env python

# Add the total counts of annotations and experiments for each sequence in dbbact

'''Add the total counts of annotations and experiments for each sequence in dbbact
'''

import sys
from collections import defaultdict

import argparse
import psycopg2
import psycopg2.extras

__version__ = "0.1"


def debug(level, msg):
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
			'amnon' - the local mac installed veriosn of dbbact
	schema : str (optional)
		name of the schema containing the annotation database

	output:
	con : the database connection
	cur : the database cursor
	"""
	debug(1, 'connecting to database')
	try:
		database = 'scdb'
		user = 'postgres'
		password = 'admin123'
		port = 5432
		host = 'localhost'
		if servertype == 'main':
			debug(1, 'servertype is main')
			database = 'scdb'
			user = 'scdb'
			password = 'magNiv'
			port = 29546
		elif servertype == 'develop':
			debug(1, 'servertype is develop')
			database = 'scdb_develop'
			user = 'scdb'
			password = 'magNiv'
			port = 29546
		elif servertype == 'local':
			debug(1, 'servertype is local')
			database = 'postgres'
			user = 'postgres'
			password = 'admin123'
			port = 5432
		elif servertype == 'amnon':
			debug(1, 'servertype is amnon')
			database = 'dbbact'
			user = 'amnon'
			password = 'magNiv'
			port = 5432
		else:
			debug(6, 'unknown server type %s' % servertype)
			print('unknown server type %s' % servertype)
		debug(1, 'connecting host=%s, database=%s, user=%s, port=%d' % (host, database, user, port))
		con = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
		cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SET search_path to %s' % schema)
		debug(1, 'connected to database')
		return (con, cur)
	except psycopg2.DatabaseError as e:
		print('Cannot connect to database. Error %s' % e)
		raise SystemError('Cannot connect to database. Error %s' % e)
		return None


def add_seq_counts(servertype='local', add_to_db=True):
	con, cur = connect_db(servertype=servertype)
	cur2 = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

	seq_exps = defaultdict(set)
	seq_annotations = defaultdict(set)

	print('processing sequences')
	cur.execute('SELECT seqid,annotationid FROM SequencesAnnotationTable')
	for cres in cur:
		cseq_id = cres['seqid']
		canno_id = cres['annotationid']
		if cseq_id == 18918:
			print('found it')
		cur2.execute('SELECT idexp FROM AnnotationsTable WHERE id=%s LIMIT 1', [canno_id])
		cres2 = cur2.fetchone()
		if cur2.rowcount != 0:
			cexp_id = cres2[0]
			seq_exps[cseq_id].add(cexp_id)
			if canno_id in seq_annotations[cseq_id]:
				print('sequence %s already associated with annotation %s' % (cseq_id, canno_id))
			seq_annotations[cseq_id].add(canno_id)
		else:
			print('sequence %s annotationid %s does not exist in annotationstable' % (cseq_id, canno_id))

	print('found data for %d sequences' % len(seq_exps))
	if not add_to_db:
		print('not adding to db')
		return
	print('adding total_annotations, total_experiments to SequencesTable')
	for cseq_id in seq_annotations.keys():
		cur.execute('UPDATE SequencesTable SET total_annotations=%s, total_experiments=%s WHERE id=%s', [len(seq_annotations[cseq_id]), len(seq_exps[cseq_id]), cseq_id])
	con.commit()
	print('done')


def main(argv):
	parser = argparse.ArgumentParser(description='Add annotation/experiment counts to all dbbact sequences. version ' + __version__)
	parser.add_argument('--db', help='name of database to connect to (main/develop/local/amnon)', default='main')
	args = parser.parse_args(argv)
	add_seq_counts(servertype=args.db)


if __name__ == "__main__":
	main(sys.argv[1:])
