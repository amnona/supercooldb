#!/usr/bin/env python

import sys
import argparse
import psycopg2
import psycopg2.extras
from collections import defaultdict
from os import path
import os

__version__ = "0.9"


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
        print ('Cannot connect to database. Error %s' % e)
        raise SystemError('Cannot connect to database. Error %s' % e)
        return None


def get_num_annotations_per_sequence(con, cur, outdir):
    hist = defaultdict(int)
    cur.execute('SELECT * FROM SequencesTable')
    for cseq_data in cur:
        cur2 = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur2.execute('SELECT * FROM SequencesAnnotationTable WHERE seqId=%s', [cseq_data['Id']])
        num_annotations = cur2.rowcount
        hist[num_annotations] += 1
    with open(path.join(outdir, 'annotations_per_seq.txt'), 'w') as fl:
        fl.write('num_annotations\tnum_sequences\n')
        for k, v in hist.items():
            fl.write('%d\t%d\n' % (k, v))


def get_stats(outdir='dbstats', servertype='main'):
    '''Get statistics about the distribution of database annotations

    Parameters
    ----------
    statsdir : str (optional)
        Name of the output directory
    servertype : str (optional)
        database to connect to ('main' or 'develop' or 'local')
    '''
    con, cur = connect_db(servertype=servertype)
    if not path.exists(outdir):
        os.makedirs(outdir)
    print('getting annotations per sequence histogram')
    get_num_annotations_per_sequence(con, cur, outdir)
    print('done')


def main(argv):
    parser = argparse.ArgumentParser(description='Get database statistics. version '+__version__)
    parser.add_argument('--db', help='name of database to connect to (main/develop/local)', default='main')
    parser.add_argument('--statsdir', help='Name of output directory', default='dbstats')
    args = parser.parse_args(argv)
    get_stats(outdir=args.statsdir, servertype=args.db)

if __name__ == "__main__":
    main(sys.argv[1:])
