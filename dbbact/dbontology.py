import psycopg2
from utils import debug
import dbidval
import dbannotations


def AddTerm(con,cur,term,parent='na',ontologyname='scdb',synonyms=[],commit=True):
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
        err,termid=dbidval.AddItem(con,cur,table='OntologyTable',description=term,commit=False)
        if err:
            return err,None
        # add/get the ontology parent term
        err,parentid=dbidval.AddItem(con,cur,table='OntologyTable',description=parent,commit=False)
        if err:
            return err,None
        # add/get the ontology name
        err,ontologynameid=dbidval.AddItem(con,cur,table='OntologyNamesTable',description=ontologyname,commit=False)
        if err:
            return err,None
        # add the tree info
        err,treeid=AddTreeTerm(con,cur,termid,parentid,ontologynameid,commit=False)
        if err:
            return err,None
        # add the synonyms
        if synonyms:
            for csyn in synonyms:
                err,cid=AddSynonym(con,cur,termid,csyn,commit=False)
        debug(2,'added ontology term %s. id is %d' % (term,termid))
        if commit:
            con.commit()
        return '',termid

    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in ontology.AddTerm" % e)
        return "error %s enountered in ontology.AddTerm" % e,-2




def AddTreeTerm(con,cur,termid,parentid,ontologynameid,commit=True):
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
        cur.execute('SELECT uniqueId FROM OntologyTreeStructureTable WHERE (ontologyId=%s AND ontologyParentId=%s AND ontologyNameId=%s) LIMIT 1',[termid,parentid,ontologynameid])
        if cur.rowcount>0:
            sid=cur.fetchone()[0]
            debug(2,'Tree entry exists (%d). returning it' % sid)
            return '',sid
        # does not exist - lets add it
        cur.execute('INSERT INTO OntologyTreeStructureTable (ontologyId,ontologyParentId,ontologyNameId) VALUES (%s,%s,%s) RETURNING uniqueId',[termid,parentid,ontologynameid])
        sid=cur.fetchone()[0]
        return '',sid
    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in ontology.AddTreeTerm" % e)
        return "error %s enountered in ontology.AddTreeTerm" % e,-2



def AddSynonym(con,cur,termid,synonym,commit=True):
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
        synonym=synonym.lower()
        # TODO: maybe test idterm,synonym does not exist
        cur.execute('INSERT INTO OntologySynonymTable (idOntology,synonym) VALUES (%s,%s) RETURNING uniqueId',[termid,synonym])
        sid=cur.fetchone()[0]
        if commit:
            con.commit()
        return '',sid
    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in ontology.AddSynonym" % e)
        return "error %s enountered in ontology.AddSynonym" % e,-2


def GetTreeParentsById(con,cur,termid):
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
        cur.execute('SELECT ontologyParentId FROM OntologyTreeStructureTable WHERE ontologyId=%s',[termid])
        if cur.rowcount==0:
            debug(3,'termid %d not found in ontologytree' % termid)
            return 'termid %d not found in ontologytree' % termid,[]
        parentids=[]
        for cres in cur:
            parentids.append(cres[0])
        debug(2,'found %d parentids for termid %d' % (len(parentids),termid))
        return '',parentids
    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in ontology.GetTreeParentById" % e)
        return "error %s enountered in ontology.GetTreeParentById" % e,'',[]


def GetParents(con,cur,term):
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
    termid=dbidval.GetIdFromDescription(con,cur,'OntologyTable',term)
    if termid<0:
        err,termid=GetSynonymTermId(con,cur,term)
        if err:
            debug(3,'ontology term not found for %s' % term)
            return 'ontolgy term %s not found' % term,[]
        debug(2,'converted synonym to termid')
    plist=[termid]
    parents=[term]
    while len(plist)>0:
        cid=plist.pop(0)
        err,cparentids=GetTreeParentsById(con,cur,cid)
        if err:
            continue
        plist.extend(cparentids)
        for cid in cparentids:
            err,cparent=dbidval.GetDescriptionFromId(con,cur,'OntologyTable',cid)
            if err:
                continue
            parents.append(cparent)
    debug(2,'found %d parents' % len(parents))
    return '',parents


def GetSynonymTermId(con,cur,synonym):
    """
    Get the term id for whic the synonym is

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
    synonym=synonym.lower()
    try:
        cur.execute('SELECT idOntology FROM OntologySynonymTable WHERE synonym=%s',[synonym])
        if cur.rowcount==0:
            debug(2,'synonym %s not found' % synonym)
            return 'synonym %s not found' % synonym,-1
        termid=cur.fetchone()[0]
        debug(2,'for synonym %s termid is %d' % (synonym,termid))
        return '',termid
    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in GetSynonymTermId" % e)
        return "error %s enountered in GetSynonymTermId" % e,-2


def GetTermAnnotations(con, cur, term):
    '''
    Get details for all annotations which contain the ontology term "term" as a parent of (or exact) annotation detail

    input:
    con, cur
    term : str
        the ontology term to search

    output:
    annotations : list of dict
        list of annotation details per annotation which contains the term
    '''
    term = term.lower()
    cur.execute('SELECT idannotation FROM AnnotationParentsTable WHERE ontology=%s', [term])
    if cur.rowcount == 0:
        debug(3, 'no annotations for term %s' % term)
        return '', []
    res = cur.fetchall()
    annotations = []
    for cres in res:
        err, cdetails = dbannotations.GetAnnotationsFromID(con, cur, cres[0])
        if err:
            debug(6, err)
            continue
        annotations.append(cdetails)
    debug(3, 'found %d annotations' % len(annotations))
    return '', annotations
