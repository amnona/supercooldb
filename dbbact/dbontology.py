import psycopg2
from .utils import debug, tolist
from . import dbidval
from . import dbannotations


def AddTerm(con, cur, term, parent='na', ontologyname='scdb', synonyms=[], commit=True):
    """
    Add a term to the ontology table. Also add parent and synonyms if supplied

    input:

    output:

    """
    try:
        # convert everything to lower case before interacting with the database
        term = term.lower()
        parent = parent.lower()
        ontologyname = ontologyname.lower()
        synonyms = [csyn.lower() for csyn in synonyms]

        # add/get the ontology term
        err, termid = dbidval.AddItem(con, cur, table='OntologyTable', description=term, commit=False)
        if err:
            return err, None
        # add/get the ontology parent term
        err, parentid = dbidval.AddItem(con, cur, table='OntologyTable', description=parent, commit=False)
        if err:
            return err, None
        # add/get the ontology name
        err, ontologynameid = dbidval.AddItem(con, cur, table='OntologyNamesTable', description=ontologyname, commit=False)
        if err:
            return err, None
        # add the tree info
        err, treeid = AddTreeTerm(con, cur, termid, parentid, ontologynameid, commit=False)
        if err:
            return err, None
        # add the synonyms
        if synonyms:
            for csyn in synonyms:
                err, cid = AddSynonym(con, cur, termid, csyn, commit=False)
        debug(2, 'added ontology term %s. id is %d' % (term, termid))
        if commit:
            con.commit()
        return '', termid

    except psycopg2.DatabaseError as e:
        debug(7, "error %s enountered in ontology.AddTerm" % e)
        return "error %s enountered in ontology.AddTerm" % e, -2


def AddTreeTerm(con, cur, termid, parentid, ontologynameid, commit=True):
    """
    Add a relation to the OntologyTreeTable

    input:
    con,cur
    termid : int
        the ontology term id (from OntologyTable)
    parentid : int
        the parent ontology term id (from OntologyTable)
    ontologynameid : int
        the id of the name of the ontology (from OntologyNamesTable)
    commit : bool (optional)
        True (default) to commit, False to not commit to database

    output:
    err : str
        Error message or empty string if ok
    sid : int
        the id of the added item
    """
    try:
        # test if already exists
        cur.execute('SELECT uniqueId FROM OntologyTreeStructureTable WHERE (ontologyId=%s AND ontologyParentId=%s AND ontologyNameId=%s) LIMIT 1', [termid, parentid, ontologynameid])
        if cur.rowcount > 0:
            sid = cur.fetchone()[0]
            debug(2, 'Tree entry exists (%d). returning it' % sid)
            return '', sid
        # does not exist - lets add it
        cur.execute('INSERT INTO OntologyTreeStructureTable (ontologyId,ontologyParentId,ontologyNameId) VALUES (%s,%s,%s) RETURNING uniqueId', [termid, parentid, ontologynameid])
        sid = cur.fetchone()[0]
        return '', sid
    except psycopg2.DatabaseError as e:
        debug(7, "error %s enountered in ontology.AddTreeTerm" % e)
        return "error %s enountered in ontology.AddTreeTerm" % e, -2


def AddSynonym(con, cur, termid, synonym, commit=True):
    """
    Add a synonym to OntologySynonymTable

    input:
    con,cur
    termid : int
        The idOntology value to add (from OntologyTable)
    synonym : str
        The synonymous term
    commit : bool (optional)
        True (default) to commit, False to skip commit

    output:
    err : str
        Error message or empty string if ok
    sid : int
        the id of the added synonym
    """
    try:
        synonym = synonym.lower()
        # TODO: maybe test idterm,synonym does not exist
        cur.execute('INSERT INTO OntologySynonymTable (idOntology,synonym) VALUES (%s,%s) RETURNING uniqueId', [termid, synonym])
        sid = cur.fetchone()[0]
        if commit:
            con.commit()
        return '', sid
    except psycopg2.DatabaseError as e:
        debug(7, "error %s enountered in ontology.AddSynonym" % e)
        return "error %s enountered in ontology.AddSynonym" % e, -2


def GetTreeParentsById(con, cur, termid):
    """
    get the parent (name and id) by term id

    input:
    con,cur
    termid : int
        the term to get the parent for

    output:
    err : str
        Error message or empty string if ok
    parentids : list of int
        list of ids of all the immediate parents of the term
    """
    try:
        cur.execute('SELECT ontologyParentId FROM OntologyTreeStructureTable WHERE ontologyId=%s', [termid])
        if cur.rowcount == 0:
            debug(3, 'termid %d not found in ontologytree' % termid)
            return 'termid %d not found in ontologytree' % termid, []
        parentids = []
        for cres in cur:
            parentids.append(cres[0])
        debug(2, 'found %d parentids for termid %d' % (len(parentids), termid))
        return '', parentids
    except psycopg2.DatabaseError as e:
        debug(7, "error %s enountered in ontology.GetTreeParentById" % e)
        return "error %s enountered in ontology.GetTreeParentById" % e, '', []


def GetParents(con, cur, term):
    """
    Get all the parents of the term in the ontology tree

    input:
    con,cur
    term : str
        The term for which to look for parents

    output:
    err : str
        Error message or empty string if ok
    parents : list of str
        the parents of term
    """
    termid = dbidval.GetIdFromDescription(con, cur, 'OntologyTable', term)
    if termid < 0:
        err, termid = GetSynonymTermId(con, cur, term)
        if err:
            debug(3, 'ontology term not found for %s' % term)
            return 'ontolgy term %s not found' % term, []
        debug(2, 'converted synonym to termid')
    plist = [termid]
    parents = [term]
    while len(plist) > 0:
        cid = plist.pop(0)
        err, cparentids = GetTreeParentsById(con, cur, cid)
        if err:
            continue
        plist.extend(cparentids)
        for cid in cparentids:
            err, cparent = dbidval.GetDescriptionFromId(con, cur, 'OntologyTable', cid)
            if err:
                continue
            parents.append(cparent)
    debug(2, 'found %d parents' % len(parents))
    return '', parents


def GetSynonymTermId(con, cur, synonym):
    """
    Get the term id for which the synonym is

    input:
    con,cur
    synonym : str
        the synonym to search for

    output:
    err : str
        Error message or empty string if ok
    termid : int
        the id of the term for the synonym is defined
    """
    synonym = synonym.lower()
    try:
        cur.execute('SELECT idOntology FROM OntologySynonymTable WHERE synonym=%s', [synonym])
        if cur.rowcount == 0:
            debug(2, 'synonym %s not found' % synonym)
            return 'synonym %s not found' % synonym, -1
        termid = cur.fetchone()[0]
        debug(2, 'for synonym %s termid is %d' % (synonym, termid))
        return '', termid
    except psycopg2.DatabaseError as e:
        debug(7, "error %s enountered in GetSynonymTermId" % e)
        return "error %s enountered in GetSynonymTermId" % e, -2


def GetSynonymTerm(con, cur, synonym):
    """
    Get the term for which the synonym is

    input:
    con,cur
    synonym : str
        the synonym to search for

    output:
    err : str
        Error message or empty string if ok
    term : str
        the term for the synonym is defined
    """
    err, termid = GetSynonymTermId(con, cur, synonym)
    if err:
        debug(2, 'ontology term %s is not a synonym' % synonym)
        return err, str(termid)
    err, term = dbidval.GetDescriptionFromId(con, cur, 'ontologyTable', termid)
    if err:
        debug(3, 'ontology term not found for termid %d (synonym %s)' % (termid, synonym))
        return err, term
    return '', term


def GetTermAnnotations(con, cur, terms, use_synonyms=True):
    '''
    Get details for all annotations which contain the ontology term "term" as a parent of (or exact) annotation detail

    input:
    con, cur
    terms : str or list of str
        the ontology term to search. if list, retrieve only annotations containing all the terms in the list
    use_synonyms : bool (optional)
        True (default) to look in synonyms table if term is not found. False to look only for exact term

    output:
    annotations : list of dict
        list of annotation details per annotation which contains the term
    '''
    terms = tolist(terms)
    debug(1, 'GetTermAnnotations for ontology terms %s' % terms)
    annotation_ids = None
    for cterm in terms:
        cterm = cterm.lower()
        cur.execute('SELECT idannotation FROM AnnotationParentsTable WHERE ontology=%s', [cterm])
        if cur.rowcount == 0:
            if use_synonyms:
                err, cterm = GetSynonymTerm(con, cur, cterm)
                if err:
                    debug(3, 'no annotations or synonyms for term %s' % cterm)
                    return '', []
                debug(1, 'found original ontology term %s' % cterm)
                cur.execute('SELECT idannotation FROM AnnotationParentsTable WHERE ontology=%s', [cterm])
            else:
                    debug(3, 'no annotations for term %s' % cterm)
                    return '', []
        res = cur.fetchall()
        cannotation_ids = set()
        for cres in res:
            cannotation_ids.add(cres[0])
        if annotation_ids is None:
            annotation_ids = cannotation_ids
        annotation_ids = annotation_ids.intersection(cannotation_ids)

    annotations = []
    for cannotation_id in annotation_ids:
        err, cdetails = dbannotations.GetAnnotationsFromID(con, cur, cannotation_id)
        if err:
            debug(6, err)
            continue
        annotations.append(cdetails)
    debug(3, 'found %d annotations' % len(annotations))
    return '', annotations


def get_term_counts(con, cur, terms, term_types=('single'), ignore_lower=False):
    '''Get the number of annotations and experiments containing each term in terms.
    NOTE: terms can be also term pairs (term1+term2)

    Parameters
    ----------
    terms: list of str
        list of terms to look for. can be term pairs
    TODO: ignore_lower: bool, optional. TODO
        True to look for total counts combining "all"/"high" and "lower" counts

    Returns
    -------
    dict of {term(str): {'total_annotations': int, 'total_experiments': int}}
    '''
    debug(1, 'get_term_counts for %d terms' % len(terms))
    terms = list(set(terms))
    term_info = {}
    for cterm in terms:
        cur.execute('SELECT TotalExperiments, TotalAnnotations from TermInfoTable WHERE term=%s LIMIT 1', [cterm])
        # cur.execute('SELECT seqCount, annotationCount, exp_count from OntologyTable WHERE description=%s LIMIT 1', [cterm])
        if cur.rowcount == 0:
            debug(2, 'Term %s not found in ontology table' % cterm)
            continue
        res = cur.fetchone()
        term_info[cterm] = {}
        # term_info[cterm]['total_sequences'] = 0
        term_info[cterm]['total_experiments'] = res[0]
        term_info[cterm]['total_annotations'] = res[1]
    debug(1, 'found info for %d terms' % len(term_info))
    return term_info


def get_annotations_term_counts(con, cur, annotations):
    '''
    Get information about all ontology terms in annotations

    Parameters
    ----------
    con, cur
    annotations : list of annotations
        The list of annotations to get the terms for (see dbannotations.GetAnnotationsFromID() )

    Returns
    -------
    term_info : dict of {str: dict}:
        Key is the ontology term.
        Value is a dict of pairs:
            'total_annotations' : int
                The total number of annotations where this ontology term is a predecessor
            'total_squences' : int
                The total number of sequences in annotations where this ontology term is a predecessor
    '''
    debug(1, 'get_annotations_term_counts for %d annotations' % len(annotations))
    terms = []
    for cannotation in annotations:
        for ctype, cterm in cannotation['details']:
            if ctype == 'low':
                cterm = '-' + cterm
            terms.append(cterm)
    terms = list(set(terms))
    # return GetTermCounts(con, cur, terms)
    return get_term_counts(con, cur, terms)


def get_ontology_terms_list(con, cur, min_term_id=None, ontologyid=None):
    '''
    Get list of all ontology terms

    Parameters
    ----------
    con, cur
    min_term_id: int or None, optional
        if int, get only terms with dbbactid > min_term_id (for fast syncing)
        if None, get all terms
    ontologies: list of str, optional
        if not None, get only terms from ontologies in ontologies list
        if None, get terms from all ontologies
        TODO: NOT SUPPORTED YET!

    Returns
    -------
    terms : dict of {term(str): id(int)}
        The list of ontology terms from table OntologyTable
    '''
    # get rid of duplicate terms
    debug(1, 'GetListOfOntologies')
    if ontologyid is None:
        cur.execute('SELECT id, description from ontologyTable')
    else:
        cur.execute('SELECT ontologytreestructuretable.ontologyid, ontologytable.description FROM ontologytreestructuretable INNER JOIN ontologytable ON ontologytable.id=ontologytreestructuretable.ontologyid WHERE OntologyNameID=%s', [ontologyid])

    if cur.rowcount == 0:
        debug(1, 'Ontologies list is empty')
        return

    if min_term_id is None:
        min_term_id = 0

    res = cur.fetchall()
    all_ontologies = {}
    for cres in res:
        if cres[0] > min_term_id:
            all_ontologies[cres[1]] = cres[0]
    return all_ontologies


def GetListOfSynonym(con, cur):
    '''
    Get list of synonym

    Parameters
    ----------
    con, cur

    Returns
    -------
    terms : list of str
        The full list of synonym
    '''
    # get rid of duplicate terms
    debug(1, 'GetListOfSynonym')
    all_synonym = []
    cur.execute('SELECT distinct synonym from ontologysynonymtable')
    if cur.rowcount == 0:
        debug(1, 'ontologysynonymtable list is empty')
        return

    res = cur.fetchall()
    all_synonym = []
    for cres in res:
        all_synonym.append(cres[0])
    return all_synonym


def GetIDs(con, cur, ontList):
    """
    Get ids of list of ontologies
    input:
    con,cur : database connection and cursor
    ontList: list of str
        the ontolgies

    output:
    errmsg : str
        "" if ok, error msg if error encountered
    seqids : list of int or None
        list of the new ids or None if error enountered
    """
    ontids = []
    try:
        sqlStr = "SELECT id from ontologyTable WHERE (description='%s')" % ontList[0]
        idx = 0
        while idx < len(ontList):
            sqlStr += " OR (description='%s')" % ontList[idx]
            idx = idx + 1

        cur.execute(sqlStr)
        if cur.rowcount == 0:
            debug(2, 'Failed to get list of terms')
        else:
            res = cur.fetchall()
            for cres in res:
                ontids.append(res[0])

        debug(3, "Number of ontology ids (out of %d)" % (len(ontids)))
        return "", ontids

    except psycopg2.DatabaseError as e:
        debug(7, 'database error %s' % e)
        return "database error %s" % e, None


def get_term_pairs_count(con, cur, term_pairs):
    '''Get the total count of experiments where each term pair appears

    Parameters
    ----------
    con,cur : database connection and cursor
    term_pairs: list of str
        the term pairs to count

    Returns
    -------
    term_count: dict of {term(str): count(float)}
    '''
    term_count = {}
    for cterm in term_pairs:
        cur.execute("SELECT AnnotationCount from TermPairsTable WHERE TermPair=%s", [cterm])
        if cur.rowcount == 0:
            debug(5, 'term pair %s not found' % cterm)
            term_count[cterm] = 0
            continue
        res = cur.fetchone()
        term_count[cterm] = res[0]
    debug(2, 'Found term pairs for %d terms' % len(term_count))
    return term_count
