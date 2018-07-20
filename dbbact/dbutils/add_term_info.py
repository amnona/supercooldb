#!/usr/bin/env python

import sys
import os

sys.path.append(os.getcwd())

import argparse
import psycopg2
import psycopg2.extras

from dbbact import dbannotations
from dbbact.utils import SetDebugLevel, debug

__version__ = "0.9"


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
        elif servertype == 'openu':
            debug(1, 'servertype is openu')
            database = 'scdb'
            user = 'postgres'
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


def add_term_info(servertype='develop', overwrite=False):
    '''Fill the term info details for each ontology term.
    These include:
        total_sequences: total number of unique sequences that have this term
        total_associations: total number of sequece-annotation associations that have this term
        total_annotations: number of annotations with this term
        total_neg_annotations: number of annotations where this term is in negative context (lower in)
        total_experiments: number of experiments containing this term
        total_neg_experiments: number of experiments containing this term only in a negative manner (lower in)

    Parameters
    ----------
    servertype : str (optional)
        database to connect to ('main' or 'develop' or 'local')

    overwrite : bool (optional)
        False (default) to not overwrite existing (non-zero) seqCounts, True to delete all
    '''
    con, cur = connect_db(servertype=servertype)
    cur.execute('SELECT id from OntologyTable')
    res = cur.fetchall()
    debug(6, 'adding term info for %d terms' % len(res))
    for idx, cres in enumerate(res):
        if idx % 100 == 0:
            debug(4, 'processed %d terms' % idx)
        term_exps = set()
        term_seqs = set()
        term_annotations = 0
        term_neg_annotations = 0
        term_neg_exps = set()
        cid = cres[0]
        cur.execute('SELECT idannotation, idannotationdetail from AnnotationListTable where idontology=%s', [cid])
        ann = cur.fetchall()
        term_associations = len(ann)
        for cann in ann:
            cannid = cann[0]
            canntype = cann[1]
            cur.execute('SELECT idexp from AnnotationsTable WHERE id=%s', [cannid])
            xx = cur.fetchone()
            if xx is None:
                debug(9, 'no details found for annotation %s' % cannid)
            else:
                expid = xx[0]
                term_exps.add(expid)
            term_annotations += 1
            # if low annotation, count is as so
            if canntype == 2:
                term_neg_annotations += 1
        cur.execute('UPDATE OntologyTable SET annotationcount=%s, exp_count=%s, annotation_neg_count=%s WHERE id=%s', [term_annotations, len(term_exps), term_neg_annotations, cid])
    debug(6, 'commiting')
    con.commit()
    debug(6, 'done')


def main(argv):
    parser = argparse.ArgumentParser(description='Add term info. version ' + __version__)
    parser.add_argument('--db', help='name of database to connect to (main/develop/local/amnon)', default='develop')
    parser.add_argument('--overwrite', help='delete current numbers', action='store_true')
    parser.add_argument('--log-level', help='log level (1 is most detailed, 10 is only critical', default=1, type=int)
    args = parser.parse_args(argv)
    SetDebugLevel(args.log_level)
    debug(1, 'test1')
    debug(10, 'test10')
    add_term_info(servertype=args.db, overwrite=args.overwrite)


if __name__ == "__main__":
    main(sys.argv[1:])
