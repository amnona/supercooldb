#!/usr/bin/env python

# add database based whole sequence ids to dbbact sequences

'''Add SILVA/Greengenes IDs to each dbBact sequence
The IDs are added to the WholeSeqIDs table which contains the following columns:
dbID: SILVA/GreenGenes
dbbactid: the dbbact id of the sequence
wholeseqid: the whole sequence database id

NOTE: each dbbact sequence can match more than one silva/GG id! so can have multiple entries for same dbbactid

Adding is based on complete match of dbbact sequence to database (as a subsequence)
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


def dbbact_seqs_to_fasta(output_file='dbbact_seqs.fa', servertype='main'):
	con, cur = connect_db(servertype=servertype)
	print('getting sequences from database')
	cur.execute('SELECT id,sequence,ggid FROM SequencesTable')
	seq_count = 0
	with open(output_file, 'w') as fl:
		for cres in cur:
			fl.write('>%s\n%s\n' % (cres[0], cres[1]))
			seq_count += 1
	print('got %d sequences' % seq_count)


def hash_sequences(filename, short_len=100):
	'''hash all the sequences in a fasta file

	Parameters
	----------
	filename: str
		the fasta file

	Returns
	-------
	seq_hash: dict of {seq: seqid}
	seq_lens : list of int
		all the sequence lengths in the fasta file (so we can hash all the lengths in the queries)
	short_hash: dict of {short_seq: seq_hash dict}
	'''
	num_too_short = 0
	seq_hash = {}
	seq_lens = set()
	short_hash = defaultdict(dict)
	for cseq, chead in iter_fasta_seqs(filename):
		clen = len(cseq)
		if clen < short_len:
			num_too_short += 1
			continue
		short_seq = cseq[:short_len]
		short_hash[short_seq][cseq] = chead
		if clen not in seq_lens:
			seq_lens.add(clen)
		seq_hash[cseq] = chead
	print('processed %d sequences.' % len(seq_hash))
	print('lens: %s' % seq_lens)
	print('num too short: %d' % num_too_short)
	return seq_hash, seq_lens, short_hash


def iter_fasta_seqs(filename):
	"""
	iterate a fasta file and return header,sequence
	input:
	filename - the fasta file name

	output:
	seq - the sequence
	header - the header
	"""

	fl = open(filename, "rU")
	cseq = ''
	chead = ''
	for cline in fl:
		if cline[0] == '>':
			if chead:
				yield(cseq.lower(), chead)
			cseq = ''
			chead = cline[1:].rstrip()
		else:
			cline = cline.strip().lower()
			cline = cline.replace('u', 't')
			cseq += cline.strip()
	if cseq:
		yield(cseq, chead)
	fl.close()


def add_whole_seq_ids(filename, servertype='local', short_len=150, seqdbid='1'):
	dbbact_seqs_to_fasta(output_file='dbbact_seqs.fa', servertype=servertype)
	seq_hash, seq_lens, short_hash = hash_sequences(filename='dbbact_seqs.fa', short_len=short_len)
	idx = 0
	num_matches = 0
	con, cur = connect_db(servertype=servertype)
	for cseq, chead in iter_fasta_seqs(filename):
		idx += 1
		if idx % 1000 == 0:
			print(idx)
		for cpos in range(len(cseq) - short_len):
				ccseq = cseq[cpos:cpos + short_len]
				if ccseq in short_hash:
					# print('found short with %d sequences' % len(short_hash[ccseq]))
					for k, v in short_hash[ccseq].items():
						if k in cseq:
							cid = chead.split(' ')[0]
							cur.execute('INSERT INTO wholeSeqIDsTable (dbid, dbbactid, wholeseqid) VALUES (%s, %s, %s)', [seqdbid, v, cid])
							num_matches += 1
							# print('found %s' % v)
	print('found %d dbbact sequences in database' % num_matches)
	con.commit()
	print('done')


def main(argv):
	parser = argparse.ArgumentParser(description='Add whole genome database ids to dbbact sequences. version ' + __version__)
	parser.add_argument('-f', '--filename', help='name of whole sequence database fasta file (i.e. greenegenes or silva)')
	parser.add_argument('--db', help='name of database to connect to (main/develop/local)', default='main')
	parser.add_argument('--seqdbid', help='the whole genome db id (1=silva 13.2, 2=greengenes 13.8', default='1')
	args = parser.parse_args(argv)
	add_whole_seq_ids(filename=args.filename, servertype=args.db, seqdbid=args.seqdbid)


if __name__ == "__main__":
	main(sys.argv[1:])
