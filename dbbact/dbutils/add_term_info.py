#!/usr/bin/env python

import sys
import os

sys.path.append(os.getcwd())

import argparse
import psycopg2
from collections import defaultdict
import psycopg2.extras

from dbbact.utils import SetDebugLevel, debug

__version__ = "0.9"


def get_annotaiton_parents():
    cur.execute('SELECT annotationdetail,ontology FROM AnnotationParentsTable WHERE idannotation=%s', [annotationid])
    if cur.rowcount == 0:
        errmsg = 'No Annotation Parents found for annotationid %d in AnnotationParentsTable' % annotationid
        debug(3, errmsg)
        return(errmsg, {})
    parents = {}
    res = cur.fetchall()
    for cres in res:
        cdetail = cres[0]
        conto = cres[1]
        if cdetail in parents:
            parents[cdetail].append(conto)
        else:
            parents[cdetail] = [conto]
    debug(1, 'found %d detail types' % len(parents))
    return '', parents


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
        if servertype == 'openu':
            debug(1, 'connecting database=%s, user=%s, port=%d' % (database, user, port))
            con = psycopg2.connect(database=database, user=user, password=password, port=port)
        else:
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


def tessa(source):
    '''get all pairs from a list
    '''
    result = []
    for p1 in range(len(source)):
            for p2 in range(p1 + 1, len(source)):
                    result.append([source[p1], source[p2]])
    return result


def add_term_info(servertype='develop', overwrite=False, add_pairs=True, add_single=True, add_parents=True, max_annotation_terms=15):
    '''Fill the term info details for each ontology term into the TermInfoTable.
    Terms are taken from all the annotations in the database
    Term details include:
    TotalExperiments: total number of experiments the term appears in
    TotalAnnotations: total number of annotations the term appears in

    Parameters
    ----------
    servertype : str (optional)
        database to connect to ('main' or 'develop' or 'local')

    overwrite : bool (optional)
        False (default) to not overwrite existing (non-zero) seqCounts, True to delete all

    add_pairs: bool (optional)
        Add information about term pairs from each annotation
    add_single: bool, optional
        Add information about each single term in the annotation
    max_annotation_terms: int, optional
        maximal number of terms in an annotation in order to process the pairs in it
    '''
    con, cur = connect_db(servertype=servertype)

    # remove the old counts
    cur.execute('DELETE FROM TermInfoTable')

    # get the lower detailtypes (i.e. 'low'). For these types we add - before
    lowertypes = set()
    cur.execute('SELECT id FROM AnnotationDetailsTypesTable WHERE description=%s', ['low'])
    lowertypes.add(cur.fetchone()[0])

    term_id_experiments = defaultdict(set)
    term_id_annotations = defaultdict(int)
    all_term_ids = set()
    cur.execute('SELECT id, idexp from AnnotationsTable')
    res = cur.fetchall()
    debug(6, 'Getting term info from %d annotations' % len(res))
    # iterate over all annotations
    for idx, cres in enumerate(res):
        annotation_terms = set()
        if idx % 100 == 0:
            debug(4, 'processed %d annotations' % idx)
        cannotation_id = cres[0]
        cexp_id = cres[1]
        cur.execute('SELECT idontology, idannotationdetail FROM AnnotationListTable WHERE idannotation=%s', [cannotation_id])
        res2 = cur.fetchall()
        for cres2 in res2:
            cterm = cres2[0]
            all_term_ids.add(cterm)
            # if it is lower, add it as negative (we'll use it when we convert to strings...)
            if cres2[1] in lowertypes:
                cterm = -cterm
            term_id_experiments[cterm].add(cexp_id)
            term_id_annotations[cterm] += 1
            annotation_terms.add(cterm)

        if add_pairs:
            if len(annotation_terms) <= max_annotation_terms:
                pairs = tessa(list(annotation_terms))
                for cpair in pairs:
                    cpair = tuple(sorted(cpair))
                    term_id_experiments[cpair].add(cexp_id)
                    term_id_annotations[cpair] += 1

    # get the term names for all the terms we encountered
    term_id_to_name = {}
    for cterm_id in all_term_ids:
        cur.execute('SELECT description FROM OntologyTable WHERE id=%s LIMIT 1', [cterm_id])
        res = cur.fetchone()
        term_id_to_name[cterm_id] = res[0]

    debug(6, 'found %d terms' % len(term_id_experiments))
    num_single = 0
    num_pairs = 0
    for cid in term_id_experiments.keys():
        if add_single:
            if isinstance(cid, int):
                if cid > 0:
                    cterm = term_id_to_name[cid]
                else:
                    cterm = '-' + term_id_to_name[-cid]
                term_experiments = len(term_id_experiments[cid])
                term_annotations = term_id_annotations[cid]
                cur.execute('INSERT INTO TermInfoTable (term, TotalExperiments, TotalAnnotations,TermType) VALUES (%s, %s, %s, %s)', [cterm, term_experiments, term_annotations, 'single'])
                num_single += 1
        if add_pairs:
            if isinstance(cid, tuple):
                cnames = []
                for ccid in cid:
                    if ccid > 0:
                        cnames.append(term_id_to_name[ccid])
                    else:
                        cnames.append('-' + term_id_to_name[-ccid])
                cnames = sorted(cnames)
                cterm = '+'.join(cnames)
                term_experiments = len(term_id_experiments[cid])
                term_annotations = term_id_annotations[cid]
                cur.execute('INSERT INTO TermInfoTable (term, TotalExperiments, TotalAnnotations,TermType) VALUES (%s, %s, %s, %s)', [cterm, term_experiments, term_annotations, 'pair'])
                num_pairs += 1

    debug(6, 'updated %d single, %d pairs' % (num_single, num_pairs))
    debug(6, 'commiting')
    con.commit()
    debug(6, 'done')


def main(argv):
    parser = argparse.ArgumentParser(description='Add term info. version ' + __version__)
    parser.add_argument('--db', help='name of database to connect to (main/develop/local/amnon)', default='develop')
    parser.add_argument('--overwrite', help='delete current numbers', action='store_true')
    parser.add_argument('--add-pairs', help='add term pairs', action='store_true')
    parser.add_argument('--add-single', help='add single terms', action='store_true')
    parser.add_argument('--add-parents', help='add parent terms', action='store_true')
    parser.add_argument('--log-level', help='log level (1 is most detailed, 10 is only critical', default=1, type=int)
    args = parser.parse_args(argv)
    SetDebugLevel(args.log_level)
    add_term_info(servertype=args.db, overwrite=args.overwrite, add_pairs=args.add_pairs, add_single=args.add_single, add_parents=args.add_parents)


if __name__ == "__main__":
    main(sys.argv[1:])
