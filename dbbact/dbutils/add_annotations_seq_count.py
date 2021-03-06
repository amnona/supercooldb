#!/usr/bin/env python

import sys
import os

sys.path.append(os.getcwd())

import argparse
import psycopg2
import psycopg2.extras

from dbbact import dbannotations

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


def fill_annotation_seqcount(servertype='develop', overwrite=False):
    '''
    Fill the database AnnotationsTable seqCount field

    Parameters
    ----------
    servertype : str (optional)
        database to connect to ('main' or 'develop' or 'local')

    overwrite : bool (optional)
        False (default) to not overwrite existing (non-zero) seqCounts, True to delete all
    '''
    con, cur = connect_db(servertype=servertype)
    skipped = 0
    added = 0
    cur.execute('SELECT id,seqCount from AnnotationsTable')
    annotations = cur.fetchall()
    for cres in annotations:
        cid = cres[0]
        cseqcount = cres[1]
        if not overwrite:
            if cseqcount == 0:
                skipped += 1
                continue
        err, annotationdetails = dbannotations.GetSequencesFromAnnotationID(con, cur, cid, userid=0)
        if err:
            print('error: %s' % err)
            continue
        numseqs = len(annotationdetails)
        if numseqs != len(set(annotationdetails)):
            debug(3, 'WARNING: duplicate seqids for annotation %d' % cid)
        cur.execute('UPDATE AnnotationsTable SET seqCount = %s WHERE id = %s', [numseqs, cid])
        added += 1
    con.commit()
    print('added %d, skipped %d' % (added, skipped))


def main(argv):
    parser = argparse.ArgumentParser(description='Fill seqCount field in AnnotationsTable. version ' + __version__)
    parser.add_argument('--db', help='name of database to connect to (main/develop/local)', default='develop')
    parser.add_argument('--overwrite', help='delete current numbers', action='store_true')
    args = parser.parse_args(argv)
    fill_annotation_seqcount(servertype=args.db, overwrite=args.overwrite)

if __name__ == "__main__":
    main(sys.argv[1:])
