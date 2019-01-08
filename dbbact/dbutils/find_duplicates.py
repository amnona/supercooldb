#!/usr/bin/env python

import sys
import os
from collections import defaultdict

sys.path.append(os.getcwd())

import argparse
import psycopg2
import psycopg2.extras


__version__ = "1.1"


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
        elif servertype == 'openu':
            debug(1, 'servertype is openu')
            database = 'scdb'
            user = 'postgres'
            password = 'magNiv'
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
        if servertype == 'openu':
            con = psycopg2.connect(database=database, user=user, password=password, port=port)
        else:
            con = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SET search_path to %s' % schema)
        debug(1, 'connected to database')
        return (con, cur)
    except psycopg2.DatabaseError as e:
        print('Cannot connect to database. Error %s' % e)
        raise SystemError('Cannot connect to database. Error %s' % e)
        return None


def find_duplicate_sequences_in_sequencestable(con, cur, fix=False):
    '''Find sequences appearing twice in sequencestable (maybe with different primers)
    '''
    print('looking for duplicate sequences in sequencestable')
    cur.execute('SELECT id, idprimer, sequence FROM SequencesTable')
    seqs = defaultdict(list)
    seqids = defaultdict(list)
    res = cur.fetchall()
    for cres in res:
        cseq = cres[2]
        seqs[cseq].append(cres[1])
        seqids[cseq].append(cres[0])
    print('found %d unique sequences. looking for duplicates' % len(seqs))
    num_fixed = 0
    num_duplicate = 0
    for cseq, cregions in seqs.items():
        if len(cregions) < 2:
            continue
        num_duplicate += 1
        if len(set(cregions)) != len(cregions):
            print('duplicate seq and region for sequence %s' % cseq)
            continue
        if fix:
            if 1 not in cregions:
                print('2 regions but not v4 for sequence %s' % cseq)
                continue
            v4pos = cregions.index(1)
            v4id = seqids[cseq][v4pos]
            num_fixed += 1
            for cidx, cid in enumerate(seqids[cseq]):
                if cregions[cidx] == 1:
                    continue
                # update the annotations to the v4id
                cur.execute('UPDATE SequencesAnnotationTable SET seqid=%s WHERE seqid=%s', [v4id, cid])
                # delete from the greengenes/silva table
                cur.execute('DELETE FROM WholeSeqIDsTable WHERE dbbactid=%s', [cid])
                # and delete the redundant sequence
                cur.execute('DELETE FROM SequencesTable WHERE id=%s', [cid])
        else:
            # print('sequence %s regions %s' % (cseq, cregions))
            pass
    con.commit()
    print('found %d duplicate seqs' % num_duplicate)
    print('fixed %d sequences' % num_fixed)


def find_duplicate_annotations(con, cur):
    '''Find annotations with same details in database
    '''
    print('looking for identical annotations')
    cur.execute('SELECT id, idExp, idAnnotationType, idMethod FROM AnnotationsTable')
    res = cur.fetchall()
    all_annotations = defaultdict(list)
    for cres in res:
        cid = cres[0]
        annotation_str = '%s;%s;%s' % (cres[1], cres[2], cres[3])
        all_annotations[annotation_str].append(cid)

    print('found %d unique annotations' % len(all_annotations))
    for cids in all_annotations.values():
        if len(cids) < 2:
            continue
        for id1 in cids:
            cur.execute('SELECT idAnnotationDetail, idOntology from AnnotationListTable WHERE idAnnotation=%s', [id1])
            details1 = set()
            res = cur.fetchall()
            for cres in res:
                details1.add('%s;%s' % (cres[0], cres[1]))
            for id2 in cids:
                if id1 == id2:
                    continue
                cur.execute('SELECT idAnnotationDetail, idOntology from AnnotationListTable WHERE idAnnotation=%s', [id2])
                details2 = set()
                res = cur.fetchall()
                for cres in res:
                    details2.add('%s;%s' % (cres[0], cres[1]))
                if details1 == details2:
                    print('Found identical annotations %s, %s' % (id1, id2))
    print('done')


def find_empty_annotations(con, cur):
    '''Find annotations with no sequences associated
    '''
    print('looking for empty annotations')
    cur.execute('SELECT id FROM AnnotationsTable')
    res = cur.fetchall()
    for cres in res:
        cur.execute('SELECT * from SequencesAnnotationTable WHERE annotationID=%s', [cres[0]])
        if cur.rowcount == 0:
            print('Annotation %s has no sequences' % cres)
    print('done')


def find_duplicate_seqs(con, cur):
    '''
    Find duplicate sequences in same annotation
    '''
    print('looking for duplicate sequences in same annotations')
    cur.execute('SELECT id FROM AnnotationsTable')
    res = cur.fetchall()
    for cres in res:
        cur.execute('SELECT seqID from SequencesAnnotationTable WHERE annotationID=%s', [cres[0]])
        if cur.rowcount == 0:
            print('Annotation %s has no sequences' % cres)
        seqs = cur.fetchall()
        all_seqs = set()
        for cseq in seqs:
            cseq = cseq[0]
            if cseq in all_seqs:
                print('sequence %d appears twice in annotation %d' % (cseq, cres[0]))
            all_seqs.add(cseq)
    print('done')


def find_duplicates(servertype='main', sda=False, sea=False, sdsa=False, ssss=False, fix_sss=False):
    '''
    Find duplcates in the dbBact database

    Looks for the following duplicates:
    1. annotations with similar details
    2. sequences present twice in same annotation
    3. empty annotations
    4. same sequence appearing twice in sequencestable (different primers?)
    '''
    con, cur = connect_db(servertype=servertype)

    if not sda:
        find_duplicate_annotations(con, cur)
    if not sea:
        find_empty_annotations(con, cur)
    if not sdsa:
        find_duplicate_seqs(con, cur)
    if not ssss:
        find_duplicate_sequences_in_sequencestable(con, cur, fix_sss)
    print('done')


def main(argv):
    parser = argparse.ArgumentParser(description='Find duplicates in dbBact. version ' + __version__)
    parser.add_argument('--db', help='name of database to connect to (main/develop/local)', default='openu')
    parser.add_argument('--sda', help='skip duplicate annotations', action='store_true')
    parser.add_argument('--sea', help='skip empty annotations', action='store_true')
    parser.add_argument('--sdsa', help='skip duplicate sequence in annotation', action='store_true')
    parser.add_argument('--ssss', help='skip same sequence twice in sequencestable', action='store_true')
    parser.add_argument('--fix-sss', help='fix same sequence in two regions to v4', action='store_true')
    args = parser.parse_args(argv)
    find_duplicates(servertype=args.db, sda=args.sda, sea=args.sea, sdsa=args.sdsa, ssss=args.ssss, fix_sss=args.fix_sss)


if __name__ == "__main__":
    main(sys.argv[1:])
