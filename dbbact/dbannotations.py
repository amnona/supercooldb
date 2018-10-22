import datetime
import psycopg2
from collections import defaultdict

from . import dbsequences
from . import dbexperiments
from . import dbidval
from . import dbontology
from .dbontology import GetParents
from .utils import debug


def AddSequenceAnnotations(con, cur, sequences, primer, expid, annotationtype, annotationdetails, method='',
                           description='', agenttype='', private='n', userid=None, commit=True):
    """
    Add an annotation to the annotation table

    input:
    con,cur : database connection and cursor
    sequences : list of str
        the sequences for which to add the annotation
        if they do not appear in the SequencesTable, they will be added
    primer : str
        the primer region name for the sequences (i.e. 'V4') or None for na
    expid : int
        the expid for the experiment for which we add the annotations
        (can be obtained via experiments.GetExperimentId() )
    annotationtype : str
        the annotation type (i.e. "isa","differential")
    annotationdetails : list of tuples (detailtype,ontologyterm) of str
        detailtype is ("higher","lower","all")
        ontologyterm is string which should match the ontologytable terms
    method : str (optional)
        the method used to discover this annotation (i.e. "permutation test", etc.) or '' for not specified
    description : str (optional)
        the text description of this annotation (i.e. "higher in sick people who like carrots")
    agenttype : str (optional)
        the agent program used to generate this annotation (i.e. 'heatsequer')
    private : str (optional)
        'n' (default) for this annotation to be visible to all users, 'y' to make it private (only current user can see)
    userid : str or None (optional)
        username of the user creating this annotation or None (default) for anonymous user
    commit : bool (optional)
        True (default) to commit, False to wait with the commit

    output:
    err : str
        the error encountered or '' if ok
    res : int
        annotationid if ok, -1 if error encouneted
    """
    # add the sequences
    err, seqids = dbsequences.AddSequences(con, cur, sequences, primer=primer, commit=False)
    if err:
        return err, -1
    err, annotationid = AddAnnotation(con, cur, expid, annotationtype, annotationdetails, method, description, agenttype, private, userid, commit=False, numseqs=len(seqids))
    if err:
        return err, -1
    for cseqid in seqids:
        cur.execute('INSERT INTO SequencesAnnotationTable (seqId,annotationId) VALUES (%s,%s)', [cseqid, annotationid])
    debug(2, "Added %d sequence annotations" % len(seqids))
    if commit:
        con.commit()
    return '', annotationid


def UpdateAnnotation(con, cur, annotationid, annotationtype=None, annotationdetails=None, method=None,
                     description=None, agenttype=None, private=None, userid=None,
                     commit=True, numseqs=None):
    '''Update an existing annotation in the database

    Parameters
    ----------
    con,cur : database connection and cursor
    annotationid : int
        the annotation to update (validated if ok to update with userid)
    annotationtype : str or None (optional)
        the annotation type (i.e. "isa","differential")
        None (default) to not update
    method : str or None (optional)
        the method (i.e. "differential abundance" etc.)
        None (default) to not update
    description : str or None (optional)
        free text description of the annotation
        None (default) to not update
    annotationdetails : list of tuples (detailtype,ontologyterm) of str or None (optional)
        detailtype is ("higher","lower","all")
        ontologyterm is string which should match the ontologytable terms
        None (default) to not update
    user : str or None (optional)
        username of the user wanting to update this annotation or None (default) for anonymous user.
        NOTE: an non-annonymous annotation can only be updated by the user who created it
        an annonymous annotation can be updated by anyone.
    commit : bool (optional)
        True (default) to commit, False to wait with the commit
    numseqs : int or None (optional)
        The number of sequences in this annotation (used to update the seqCount in the ontologyTable)
        None (default) to not change the number of sequences

    output:
    err : str
        the error encountered or '' if ok
    cid : int
        the annotationid or <0 if failed
    '''
    debug(1, 'UpdateAnnotation for annotationID %d' % annotationid)

    # verify the user can update the annotation
    err, origuser = GetAnnotationUser(con, cur, annotationid)
    if err:
        return err
    if origuser != 0:
        if userid == 0:
            debug(6, 'cannot update non-anonymous annotation (userid=%d) with default userid=0' % origuser)
            return('Cannot update non-anonymous annotation with default user. Please log in first')
        if origuser != userid:
            debug(6, 'cannot update. annotation %d was created by user %d but delete request was from user %d' % (annotationid, origuser, userid))
            return 'Cannot update. Annotation was created by a different user', -1

    # update annotationtypeid
    if annotationtype is not None:
        annotationtypeid = dbidval.GetIdFromDescription(con, cur, 'AnnotationTypesTable', annotationtype)
        if annotationtypeid < 0:
            return 'annotation type %s unknown' % annotationtype, -1
        cur.execute('UPDATE AnnotationsTable SET idAnnotationType = %s WHERE id = %s', [annotationtypeid, annotationid])
        debug(1, 'updated annotation type to %d' % annotationtypeid)

    # update methodid
    if method is not None:
        methodid = dbidval.GetIdFromDescription(con, cur, 'MethodTypesTable', method, noneok=True)
        if methodid < 0:
            return 'method %s unknown' % method, -1
        cur.execute('UPDATE AnnotationsTable SET idMethod = %s WHERE id = %s', [methodid, annotationid])
        debug(1, 'updated method to %d' % methodid)

    # update agenttypeid
    if agenttype is not None:
        agenttypeid = dbidval.GetIdFromDescription(con, cur, 'AgentTypesTable', agenttype, noneok=True, addifnone=True, commit=False)
        if agenttypeid < 0:
            return 'agenttype %s unknown' % agenttype, -1
        cur.execute('UPDATE AnnotationsTable SET idAgentType = %s WHERE id = %s', [agenttypeid, annotationid])
        debug(1, 'updated agenttypeid to %d' % agenttypeid)

    # update private
    if private is not None:
        private = private.lower()
        cur.execute('UPDATE AnnotationsTable SET isPrivate = %s WHERE id = %s', [private, annotationid])
        debug(1, 'updated private to %s' % private)

    # update description
    if description is not None:
        cur.execute('UPDATE AnnotationsTable SET description = %s WHERE id = %s', [description, annotationid])
        debug(1, 'updated description to %s' % description)

    debug(2, "updated annotation id %d." % (annotationid))

    if numseqs is None:
        cur.execute('SELECT seqCount FROM AnnotationsTable WHERE id = %s LIMIT 1', [annotationid])
        if cur.rowcount == 0:
            debug(3, 'seqCount for annotationid %d not found' % annotationid)
            numseqs = 0
        else:
            res = cur.fetchone()
            numseqs = res[0]

    # update the annotation details if needed
    if annotationdetails is not None:
        debug(1, 'Updating %d annotation details' % len(annotationdetails))
        # to update the annotaiton details, we delete and then create the new ones
        cur.execute('DELETE FROM AnnotationListTable WHERE idannotation=%s', [annotationid])
        debug(1, 'deleted from annotationliststable')
        # add the annotation details (which ontology term is higer/lower/all etc.)
        err, numadded = AddAnnotationDetails(con, cur, annotationid, annotationdetails, commit=False)
        if err:
            debug(3, "failed to add annotation details. aborting")
            return err, -1
        debug(2, "%d annotationdetails added" % numadded)
        # and update the annotationParentsTable (ontology terms per annotation)
        # delete the old entry
        cur.execute('DELETE FROM AnnotationParentsTable WHERE idAnnotation=%s', [annotationid])
        debug(1, 'deleted from annotationParentsTable')
        # add the parents of each ontology term to the annotationparentstable
        err, numadded = AddAnnotationParents(con, cur, annotationid, annotationdetails, commit=False, numseqs=numseqs)
        if err:
            debug(3, "failed to add annotation parents. aborting")
            return err, -1
        debug(2, "%d annotation parents added" % numadded)

    if commit:
        con.commit()
    return '', annotationid


def AddAnnotation(con, cur, expid, annotationtype, annotationdetails, method='',
                  description='', agenttype='', private='n', userid=None,
                  commit=True, numseqs=0):
    """
    Add an annotation to the annotation table

    input:
    con,cur : database connection and cursor
    expid : int
        the expid for the experiment for which we add the annotations
        (can be obtained via experiments.GetExperimentId() )
    annotationtype : str
        the annotation type (i.e. "isa","differential")
    annotationdetails : list of tuples (detailtype,ontologyterm) of str
        detailtype is ("higher","lower","all")
        ontologyterm is string which should match the ontologytable terms
    user : str or None (optional)
        username of the user creating this annotation or None (default) for anonymous user
    commit : bool (optional)
        True (default) to commit, False to wait with the commit
    numseqs : int (optional)
        The number of sequences in this annotation (used to update the seqCount in the ontologyTable)

    output:
    err : str
        the error encountered or '' if ok
    cid : int
        the new curation identifier or <0 if failed
    """
    # test if experiment exists
    if not dbexperiments.TestExpIdExists(con, cur, expid, userid):
        debug(4, 'expid %d does not exists' % expid)
        return 'expid %d does not exist' % expid, -1
    # handle userid
    if userid is None:
        userid = 0
        # TODO: add user exists check
    # get annotationtypeid
    annotationtypeid = dbidval.GetIdFromDescription(con, cur, 'AnnotationTypesTable', annotationtype)
    if annotationtypeid < 0:
        return 'annotation type %s unknown' % annotationtype, -1
    # get annotationtypeid
    methodid = dbidval.GetIdFromDescription(con, cur, 'MethodTypesTable', method, noneok=True)
    if methodid < 0:
        err, methodid = dbidval.AddItem(con, cur, 'MethodTypesTable', method)
        if err:
            # return 'method %s unknown' % method, -1
            debug(3, "failed to add method. aborting")
            return err, -1

    # get annotationtypeid
    agenttypeid = dbidval.GetIdFromDescription(con, cur, 'AgentTypesTable', agenttype, noneok=True, addifnone=True, commit=False)
    if agenttypeid < 0:
        return 'agenttype %s unknown' % agenttype, -1
    # get the current date
    cdate = datetime.date.today().isoformat()

    if private is None:
        private = 'n'
    # lowercase the private
    private = private.lower()

    cur.execute('INSERT INTO AnnotationsTable (idExp,idUser,idAnnotationType,idMethod,description,idAgentType,isPrivate,addedDate,seqCount) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id',
                [expid, userid, annotationtypeid, methodid, description, agenttypeid, private, cdate, numseqs])
    cid = cur.fetchone()[0]
    debug(2, "added annotation id is %d. adding %d annotationdetails" % (cid, len(annotationdetails)))

    # add the annotation details (which ontology term is higer/lower/all etc.)
    err, numadded = AddAnnotationDetails(con, cur, cid, annotationdetails, commit=False)
    if err:
        debug(3, "failed to add annotation details. aborting")
        return err, -1
    debug(2, "%d annotationdetails added" % numadded)

    # add the parents of each ontology term to the annotationparentstable
    err, numadded = AddAnnotationParents(con, cur, cid, annotationdetails, commit=False, numseqs=numseqs)
    if err:
        debug(3, "failed to add annotation parents. aborting")
        return err, -1
    debug(2, "%d annotation parents added" % numadded)

    if commit:
        con.commit()
    return '', cid


def AddAnnotationDetails(con, cur, annotationid, annotationdetails, commit=True):
    """
    Add annotationdetails to the AnnotationListTable

    input:
    con,cur
    annotationid : int
        the idAnnotation field
    annotationdetails : list of tuples (detailtype,ontologyterm) of str
        detailtype is ("higher","lower","all")
        ontologyterm is string which should match the ontologytable terms
    commit : bool (optional)
        True (default) to commit, False to not commit to database

    output:
    err : str
        error encountered or '' if ok
    numadded : int
        Number of annotations added to the AnnotationListTable or -1 if error
    """
    try:
        numadded = 0
        for (cdetailtype, contologyterm) in annotationdetails:
            cdetailtypeid = dbidval.GetIdFromDescription(con, cur, "AnnotationDetailsTypesTable", cdetailtype)
            if cdetailtypeid < 0:
                debug(3, "detailtype %s not found" % cdetailtype)
                return "detailtype %s not found" % cdetailtype, -1
            contologytermid = dbidval.GetIdFromDescription(con, cur, "OntologyTable", contologyterm)
            if contologytermid < 0:
                debug(3, "ontology term %s not found" % contologyterm)
                err, contologytermid = dbontology.AddTerm(con, cur, contologyterm, commit=False)
                if err:
                    debug(7, 'error enountered when adding ontology term %s' % contologyterm)
                    return 'ontology term %s not found or added' % contologyterm, -1
                debug(3, 'ontology term %s added' % contologyterm)
            cur.execute('INSERT INTO AnnotationListTable (idAnnotation,idAnnotationDetail,idOntology) VALUES (%s,%s,%s)', [annotationid, cdetailtypeid, contologytermid])
            numadded += 1
        debug(1, "Added %d annotationlist items" % numadded)
        if commit:
            con.commit()
        return '', numadded
    except psycopg2.DatabaseError as e:
        debug(7, "error %s enountered in AddAnnotationDetails" % e)
        return e, -2


def AddAnnotationParents(con, cur, annotationid, annotationdetails, commit=True, numseqs=0):
    """
    Add all the parent terms of each annotation detail ontology to the annotationparentstable

    input:
    con,cur
    annotationid : int
        the idAnnotation field
    annotationdetails : list of tuples (detailtype,ontologyterm) of str
        detailtype is ("higher","lower","all")
        ontologyterm is string which should match the ontologytable terms
    commit : bool (optional)
        True (default) to commit, False to not commit to database

    output:
    err : str
        error encountered or '' if ok
    numadded : int
        Number of annotations added to the AnnotationListTable or -1 if error
    """
    try:
        numadded = 0
        parentsdict = {}
        for (cdetailtype, contologyterm) in annotationdetails:
            err, parents = GetParents(con, cur, contologyterm)
            if err:
                debug(6, 'error getting parents for term %s: %s' % (contologyterm, err))
                continue
            debug(2, 'term %s parents %s' % (contologyterm, parents))
            if cdetailtype not in parentsdict:
                parentsdict[cdetailtype] = parents
            else:
                parentsdict[cdetailtype].extend(parents)

        for cdetailtype, parents in parentsdict.items():
            parents = list(set(parents))
            for cpar in parents:
                cpar = cpar.lower()
                cdetailtype = cdetailtype.lower()
                debug(2, 'adding parent %s' % cpar)
                cur.execute('INSERT INTO AnnotationParentsTable (idAnnotation,annotationDetail,ontology) VALUES (%s,%s,%s)', [annotationid, cdetailtype, cpar])
                numadded += 1
                # add the number of sequences and one more annotation to all the terms in this annotation
                cur.execute('UPDATE OntologyTable SET seqCount = seqCount+%s, annotationCount=annotationCount+1 WHERE description = %s', [numseqs, cpar])
        debug(1, "Added %d annotationparents items" % numadded)
        if commit:
            con.commit()
        return '', numadded
    except psycopg2.DatabaseError as e:
        debug(7, "error %s enountered in AddAnnotationParents" % e)
        return e, -2


def GetAnnotationParents(con, cur, annotationid):
    '''
    Get the ontology parents list for the annotation

    input:
    con,cur
    annotationid : int
        the annotationid for which to show the list of ontology terms

    output:
    err: str
        error encountered or '' if ok
    parents : dict of {str:list of str} {detail type (i.e. 'higher in'): list of ontology terms}
    '''
    debug(1, 'GetAnnotationParents for id %d' % annotationid)
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


def GetAnnotationDetails(con, cur, annotationid):
    """
    Get the annotation details list for annotationid

    input:
    con,cur
    annotationid : int
        the annotationid for which to show the list of ontology terms

    output:
    err: str
        error encountered or '' if ok
    details : list of (str,str) (detail type (i.e. 'higher in'), ontology term (i.e. 'homo sapiens'))
    """
    details = []
    debug(1, 'get annotationdetails from id %d' % annotationid)
    cur.execute('SELECT * FROM AnnotationListTable WHERE idAnnotation=%s', [annotationid])
    allres = cur.fetchall()
    for res in allres:
        iddetailtype = res['idannotationdetail']
        idontology = res['idontology']
        err, detailtype = dbidval.GetDescriptionFromId(con, cur, 'AnnotationDetailsTypesTable', iddetailtype)
        if err:
            return err, []
        err, ontology = dbidval.GetDescriptionFromId(con, cur, 'OntologyTable', idontology)
        debug(1, 'ontologyid %d term %s' % (idontology, ontology))
        if err:
            return err, []
        details.append([detailtype, ontology])
    debug(1, 'found %d annotation details' % len(details))
    return '', details


def GetAnnotationsFromID(con, cur, annotationid, userid=0):
    """
    get annotation details from an annotation id.

    input:
    con,cur
    annotationid : int
        the annotationid to get
    userid : int (optional)
        used to check if to return a private annotation


    output:
    err : str
        the error encountered or '' if ok
    data : dict
        the annotation data. includes:
        'annotationid' : int
        'description' : str
        'method' : str
        'agent' : str
        'annotationtype' : str
        'expid' : int
        'userid' : int (the user who added this annotation)
        'username' : string
        'date' : str
        'num_sequences' : int
            number of sequences associated with this annotations
        'details' : list of (str,str) of type (i.e. 'higher in') and value (i.e. 'homo sapiens')
    """
    debug(1, 'get annotation from id %d' % annotationid)
    cur.execute('SELECT AnnotationsTable.*,userstable.username FROM AnnotationsTable,userstable WHERE AnnotationsTable.iduser = userstable.id and AnnotationsTable.id=%s', [annotationid])
    if cur.rowcount == 0:
        debug(3, 'annotationid %d not found' % annotationid)
        return 'Annotationid %d not found' % annotationid, None
    res = cur.fetchone()
    debug(1, res)
    if res['isprivate'] == 'y':
        if res['iduser'] != userid:
            debug(3, 'cannot view annotation %d (created by user %d), request from used %d' % (annotationid, res['iduser'], userid))
            return 'Annotationid %d is private. Cannot view' % annotationid, None

    data = {}
    data['id'] = annotationid
    data['description'] = res['description']
    data['private'] = res['isprivate']
    err, method = dbidval.GetDescriptionFromId(con, cur, 'MethodTypesTable', res['idmethod'])
    if err:
        return err, None
    data['method'] = method
    err, agent = dbidval.GetDescriptionFromId(con, cur, 'AgentTypesTable', res['idagenttype'])
    if err:
        return err, None
    data['agent'] = agent
    err, annotationtype = dbidval.GetDescriptionFromId(con, cur, 'AnnotationTypesTable', res['idannotationtype'])
    if err:
        return err, None
    data['annotationtype'] = annotationtype
    data['expid'] = res['idexp']
    data['userid'] = res['iduser']
    data['username'] = res['username']
    data['date'] = res['addeddate'].isoformat()
    data['annotationid'] = annotationid
    data['num_sequences'] = res['seqcount']

    if res['isprivate'] == 'y':
        if userid != data['userid']:
            debug(6, 'Trying to view private annotation id %d from different user (orig user %d, current user %d)' % (annotationid, data['userid'], userid))
            return 'Annotation not found', None

    err, details = GetAnnotationDetails(con, cur, annotationid)
    if err:
        return err, None
    data['details'] = details

    return '', data


def IsAnnotationVisible(con, cur, annotationid, userid=0):
    """
    Test if the user userid can see annotation annotationid

    input:
    con,cur
    annotationid: int
        the id of the annotation to test
    userid : int (optional)
        the user asking to view the annotation (or 0 for anonymous)

    output:
    err: str
        the error encountered or '' if ok
    isvisible: bool
        True if user is allowed to see the annotation, False if not
    """
    debug(1, 'IsAnnotationVisible, annotationid %d, userid %d' % (annotationid, userid))
    cur.execute('SELECT (isPrivate,idUser) FROM AnnotationsTable WHERE id=%s LIMIT 1', [annotationid])
    if cur.rowcount == 0:
        debug(3, 'annotationid %d not found' % annotationid)
        return 'Annotationid %d not found', False
    res = cur.fetchone()
    if res[0] == 'y':
        if userid != res[1]:
            debug(6, 'Trying to view private annotation id %d from different user (orig user %d, current user %d)' % (annotationid, res[1], userid))
            return '', False
    return '', True


def GetUserAnnotations(con, cur, foruserid, userid=0):
    '''
    Get all annotations created by user userid

    input:
    con,cur :
    foruserid : int
        the userid to get the annotations generated by
    userid : int
        the current (querying) userid

    output:
    err : str
        The error encountered or '' if ok
    details: list of dict
        a list of all the info about each annotation (see GetAnnotationsFromID())
    '''
    details = []
    debug(1, 'GetUserAnnotations userid %d' % userid)
    cur.execute('SELECT id FROM AnnotationsTable WHERE iduser=%s', [foruserid])
    if cur.rowcount == 0:
        debug(3, 'no annotations for userid %d' % foruserid)
        return '', []
    res = cur.fetchall()
    for cres in res:
        err, cdetails = GetAnnotationsFromID(con, cur, cres[0], userid=userid)
        if err:
            debug(6, err)
            return err, None
        details.append(cdetails)
    debug(3, 'found %d annotations' % len(details))
    return '', details


def GetSequenceAnnotations(con, cur, sequence, region=None, userid=0):
    """
    Get all annotations for a sequence. Returns a list of annotations (empty list if sequence is not found)

    Parameters
    ----------
    con,cur :
    sequence : str ('ACGT')
        the sequence to search for in the database
    region : int (optional)
        None to not compare region, or the regionid the sequence is from
    userid : int (optional)
        the id of the user requesting the annotations. Private annotations with non-matching user will not be returned

    Returns
    -------
    err : str
        The error encountered or '' if ok
    details: list of dict
        a list of all the info about each annotation (see GetAnnotationsFromID())
    """
    details = []
    debug(1, 'GetSequenceAnnotations sequence %s' % sequence)
    err, sid = dbsequences.GetSequenceId(con, cur, sequence, region)
    if len(sid) == 0:
        debug(2, 'Sequence %s not found for GetSequenceAnnotations.' % sequence)
        return '', []
    if err:
        debug(6, 'Sequence %s not found for GetSequenceAnnotations. error : %s' % (sequence, err))
        return err, None
    debug(1, 'sequenceid=%s' % sid)
    cur.execute('SELECT annotationId FROM SequencesAnnotationTable WHERE seqId IN %s', [tuple(sid)])
    if cur.rowcount == 0:
        debug(3, 'no annotations for sequenceid %s' % sid)
        return '', []
    res = cur.fetchall()
    for cres in res:
        err, cdetails = GetAnnotationsFromID(con, cur, cres[0])
        if err:
            debug(6, err)
            return err, None
        details.append(cdetails)
    debug(3, 'found %d annotations' % len(details))
    return '', details


def GetAnnotationsFromExpId(con, cur, expid, userid=0):
    """
    Get annotations about an experiment

    input:
    con,cur
    expid : int
        the experimentid to get annotations for
    userid : int
        the user requesting the info (for private studies/annotations)

    output:
    err : str
        The error encountered or '' if ok
    annotations: list of dict
        a list of all the annotations associated with the experiment
    """
    debug(1, 'GetAnnotationsFromExpId expid=%d' % expid)
    # test if experiment exists and not private
    if not dbexperiments.TestExpIdExists(con, cur, expid, userid):
        debug(3, 'experiment %d does not exist' % expid)
        return '', []
    cur.execute('SELECT id from AnnotationsTable WHERE idExp=%s', [expid])
    res = cur.fetchall()
    debug(1, 'found %d annotations for expid %d' % (len(res), expid))
    annotations = []
    for cres in res:
        # test if annotation is private - don't show it
        err, canview = IsAnnotationVisible(con, cur, cres[0], userid)
        if err:
            return err, None
        if not canview:
            continue

        err, cannotation = GetAnnotationsFromID(con, cur, cres[0], userid)
        if err:
            debug(3, 'error encountered for annotationid %d : %s' % (cres[0], err))
            return err, None
        annotations.append(cannotation)
    return '', annotations


def GetSequencesFromAnnotationID(con, cur, annotationid, userid=0):
    """
    Get a list of sequence ids which are a part of the annotation annotationid

    input:
    con,cur:
    annottionid : int
        the annotationid to get the associated sequences for
    userid : int (optional)
        the user performing the query (or None if unknown). Used to hide private annotations not by the user

    output:
    err : str
        The error encountered or '' if ok
    seqids : list of int
        the sequence ids associated with the annotationid
    """
    debug(1, "GetSequencesFromAnnotationID for annotationid %d" % annotationid)
    err, canview = IsAnnotationVisible(con, cur, annotationid, userid)
    if err:
        debug(6, 'error encountered:%s' % err)
        return err, None
    if not canview:
        debug(6, 'user %d cannot view annotationid %d since it is private' % (userid, annotationid))
        return 'Annotation is private', None
    cur.execute('SELECT seqId from SequencesAnnotationTable WHERE annotationId=%s', [annotationid])
    seqids = []
    res = cur.fetchall()
    for cres in res:
        seqids.append(cres[0])
    debug(1, "Found %d sequences associated" % len(seqids))
    return '', seqids


def GetFullSequencesFromAnnotationID(con, cur, annotationid, userid=0):
    '''Get information about sequences which are a part of the annotation annotationid.
    Retrieves full details including the sequence and the taxonomy

    Parameters
    ----------
    con, cur:
    annottionid : int
        the annotationid to get the associated sequences for
    userid : int (optional)
        the user performing the query (or None if unknown). Used to hide private annotations not by the user

    Returns
    -------
    err : str
        The error encountered or '' if ok
    sequences : list of dict (one per sequence). contains:
        'seq' : str (ACGT)
            the sequence
        'taxonomy' : str
            the taxonomy of the sequence or '' if unknown
    '''
    debug(1, "GetSequencesFromAnnotationID for annotationid %d" % annotationid)
    err, seqids = GetSequencesFromAnnotationID(con, cur, annotationid, userid)
    if err:
        return err, []
    debug(1, 'Found %s sequences' % len(seqids))
    err, sequences = dbsequences.SeqFromID(con, cur, seqids)
    if err:
        return err, []
    return '', sequences


def GetAnnotationUser(con, cur, annotationid):
    """
    Get which user generated the annotation

    input:
    con,cur
    annotationid: int
        the id of the annotation to test

    output:
    err: str
        the error encountered or '' if ok
    userid: int
        the userid which generated the annotation
    """
    debug(1, 'GetAnnotationUser, annotationid %d' % annotationid)
    cur.execute('SELECT (idUser) FROM AnnotationsTable WHERE id=%s LIMIT 1', [annotationid])
    if cur.rowcount == 0:
        debug(3, 'annotationid %d not found' % annotationid)
        return 'Annotationid %d not found', False
    res = cur.fetchone()
    return '', res[0]


def DeleteAnnotation(con, cur, annotationid, userid=0, commit=True):
    """
    Delete an annotation from the database
    Also deletes all the sequence annotations and annotationdetails associated with it
    Note only the user who created an annotation can delete it

    input:
    con,cur
    annotationid : int
        the annotationid to delete
    userid : int
        the user requesting the delete
    commit : bool (optional)
        True (default) to commit, False to wait with the commit

    output:
    err : str
        The error encountered or '' if ok
    """
    debug(1, 'DeleteAnnotation for annotationid %d userid %d' % (annotationid, userid))
    err, origuser = GetAnnotationUser(con, cur, annotationid)
    if err:
        return err
    if origuser != 0:
        if userid == 0:
            debug(6, 'cannot delete non-anonymous annotation (userid=%d) with default userid=0' % origuser)
            return('Cannot delete non-anonymous annotation with default user. Please log in first')
        if origuser != userid:
            debug(6, 'cannot delete. annotation %d was created by user %d but delete request was from user %d' % (annotationid, origuser, userid))
            return 'Cannot delete. Annotation was created by a different user'

    # find how many sequences are in the annotations
    cur.execute('SELECT seqCount FROM AnnotationsTable WHERE id=%s', [annotationid])
    res = cur.fetchone()
    num_seqs = res[0]

    # update the ontology term sequence counts
    err, parents = GetAnnotationParents(con, cur, annotationid)
    if err:
        msg = 'Could not find ontology parents. Delete aborted'
        debug(3, msg)
        return msg
    for cterm in parents:
        cur.execute('UPDATE OntologyTable SET seqCount = seqCount-%s, annotationCount=annotationCount-1 WHERE description = %s', [num_seqs, cterm])
    debug(3, 'fixed ontologytable counts')

    cur.execute('DELETE FROM AnnotationsTable WHERE id=%s', [annotationid])
    debug(1, 'deleted from annotationstable')
    cur.execute('DELETE FROM AnnotationListTable WHERE idannotation=%s', [annotationid])
    debug(1, 'deleted from annotationliststable')
    cur.execute('DELETE FROM SequencesAnnotationTable WHERE annotationid=%s', [annotationid])
    debug(1, 'deleted from sequencesannotationtable')
    # delete the annotation parents entries
    cur.execute('DELETE FROM AnnotationParentsTable WHERE idAnnotation=%s', [annotationid])
    debug(1, 'deleted from annotationParentsTable')

    if commit:
        con.commit()
    return('')


def DeleteSequenceFromAnnotation(con, cur, sequences, annotationid, userid=0, commit=True):
    '''
    remove sequences from an annotation
    Note only the user who created an annotation can remove sequences from it

    input:
    con,cur
    sequences : list of str
        the sequences to remove from the annotation
    annotationid : int
        the annotation from which to remove the sequences
    userid : int (optional)
        the userid (for validating he can modify this annotation)
    commit :bool (optional)
        True (default) to commmit the change, False to not commit (the caller should commit)

    output:
    err: str
        the error string or '' if no error encountered
    '''
    debug(1, 'DeleteSequenceFromAnnotation for %d sequences, annotationid %d, userid %d' % (len(sequences), annotationid, userid))
    origuser = GetAnnotationUser(con, cur, annotationid)
    if origuser != 0:
        if userid == 0:
            debug(6, 'cannot delete non-anonymous annotation with default userid=0')
            return('Cannot delete non-anonymous annotation with default user. Please log in first')
        if origuser != userid:
            debug(6, 'cannot delete. annotation %d was created by user %d but delete request was from user %d' % (annotationid, origuser, userid))
            return 'Cannot delete. Annotation was created by a different user'

    # remove duplicate sequences for the delete
    sequences = list(set(sequences))
    seqids = dbsequences.GetSequencesId(con, cur, sequences)
    for cseqid in seqids:
        cur.execute('DELETE FROM SequencesAnnotationTable WHERE annotationid=%s AND seqId=%s', (annotationid, cseqid))
    debug(3, 'deleted %d sequences from from sequencesannotationtable annotationid=%d' % (len(sequences), annotationid))

    # remove the count of these sequences for the annotation
    numseqs = len(sequences)
    cur.execute('UPDATE AnnotationsTable SET seqCount = seqCount-%s', [numseqs])
    debug(3, 'removed %d from the annotationstable seq count' % numseqs)

    # update the ontology term sequence counts
    err, parents = GetAnnotationParents(con, cur, annotationid)
    if err:
        msg = 'Could not find ontology parents. Delete aborted'
        debug(3, msg)
        return msg
    for cterm in parents:
        cur.execute('UPDATE OntologyTable SET seqCount = seqCount-%s WHERE description = %s', [numseqs, cterm])
    debug(3, 'fixed ontologytable counts')

    if commit:
        con.commit()
    return('')


def GetFastAnnotations(con, cur, sequences, region=None, userid=0, get_term_info=True, get_all_exp_annotations=True, get_taxonomy=True, get_parents=True):
    """
    Get annotations for a list of sequences in a compact form

    input:
    con,cur :
    sequences : list of str ('ACGT')
        the sequences to search for in the database
    region : int (optional)
        None to not compare region, or the regionid the sequence is from
    userid : int (optional)
        the id of the user requesting the annotations. Provate annotations with non-matching user will not be returned
    get_term_info : bool (optional)
        True (default) to get the information about each term, False to skip this step
    get_all_exp_annotations: bool (optional)
        True (default) to get all annotations for each experiment which the sequence appear in at least one annotation.
        False to get just the annotations where the sequence appears
    get_taxonomy: bool, True
        True to get the taxonomy for each sequence (returned in the 'taxonomy' field)
    get_parents: bool, True
        True to get the parent terms for each annotation term, False to just get the annotation terms

    output:
    err : str
        The error encountered or '' if ok
    annotations : dict of {annotationid : annotation details (see GetAnnotationsFromID() }
        a dict containing all annotations relevant to any of the sequences and the details about them
        * includes 'parents' - list of all ontology term parents for each annotation
    seqannotations : list of (seqpos, annotationids)
        list of tuples.
        seqpos : the position (in sequences) of the sequence with annotations
        annotationsids : list of int
            the ids of annotations about this sequence
    term_info : dict of {term, dict}
        Information about each term which appears in the annotation terms. Key is the ontolgy term. the value dict is:
            'total_annotations' : int
                total number of annotations where this term appears (as a parent)
            'total_sequences' : int
                total number of sequences in annotations where this term appears (as a parent)
    taxonomy : list of str
        the dbbact taxonomy string for each supplied sequence (order similar to query sequences)
    """
    debug(2, 'GetFastAnnotations for %d sequences' % len(sequences))
    annotations = {}
    seqannotations = []
    all_terms = set()
    term_info = {}

    # set of experients we already processed (so no need to re-look at the annotations from the experiment
    # in case get_all_exp_annotations=True)
    experiments_added = set()

    for cseqpos, cseq in enumerate(sequences):
        cseqannotationids = []
        # get the sequenceid
        err, sid = dbsequences.GetSequenceId(con, cur, cseq, region)
        # if not in database - no annotations
        if len(sid) == 0:
            continue
        # get annotations for the sequence
        cur.execute('SELECT annotationid FROM SequencesAnnotationTable WHERE seqid IN %s', [tuple(sid)])
        res = cur.fetchall()
        # go over all annotations
        for cres in res:
            current_annotation = cres[0]
            # add the sequence annotation link
            cseqannotationids.append(current_annotation)

            # if annotation is already in list - move to next
            if current_annotation in annotations:
                continue

            # we don't need the term info since we do it once for all terms
            err, cdetails = GetAnnotationsFromID(con, cur, current_annotation, userid=userid)
            # if we didn't get annotation details, probably they are private - just ignore
            if cdetails is None:
                continue

            annotations_to_process = [cdetails]
            if get_all_exp_annotations:
                debug(2, 'getting all exp annotations')
                if 'expid' in cdetails:
                    expid = cdetails['expid']
                    # if we already added this experiment - finished
                    if expid in experiments_added:
                        continue
                    err, annotations_to_process = GetAnnotationsFromExpId(con, cur, expid, userid=userid)
                    experiments_added.add(expid)

            for cdetails in annotations_to_process:
                cannotationid = cdetails['annotationid']
                # if annotation not in annotations list - add it
                if cannotationid not in annotations:
                    # if we didn't get annotation details, probably they are private - just ignore
                    if cdetails is None:
                        continue
                    # if we need to get the parents, add all the parent terms
                    if get_parents:
                        err, parents = GetAnnotationParents(con, cur, cannotationid)
                    else:
                        # otherwise, just keep the annotation terms
                        parents = defaultdict(list)
                        for cdetailtype, cterm in cdetails['details']:
                                parents[cdetailtype].append(cterm)
                    cdetails['parents'] = parents
                    # add to the set of all terms to get the info for
                    # note we add a "-" for terms that have a "low" annotation type
                    for ctype, cterms in parents.items():
                        for cterm in cterms:
                            if ctype == 'low':
                                cterm = '-' + cterm
                            all_terms.add(cterm)
                    # and add the annotation
                    annotations[cannotationid] = cdetails

        seqannotations.append((cseqpos, cseqannotationids))
    debug(2, 'got annotations. found %d unique terms' % len(all_terms))
    if get_term_info:
        term_info = dbontology.get_term_counts(con, cur, all_terms)
    else:
        term_info = {}
    debug(2, 'found %d annotations, %d annotated sequences. %d term_info' % (len(annotations), len(seqannotations), len(term_info)))
    taxonomy = []
    if get_taxonomy:
        for cseq in sequences:
            cerr, ctax = dbsequences.GetSequenceTaxonomy(con, cur, cseq)
            if cerr == '':
                taxonomy.append(ctax)
            else:
                taxonomy.append('na')
        debug(2, 'got taxonomies')
    return '', annotations, seqannotations, term_info, taxonomy


def GetAllAnnotations(con, cur, userid=0):
    '''Get list of all annotations in dbBact

    Parameters
    ----------
    con,cur
    userid : int (optional)
        the userid from who the request is or 0 (default) for anonymous

    Returns
    -------
    err : str
        empty of ok, otherwise the error encountered
    annotations : list of dict
        list of all annotations (see GetAnnotationsFromID)
    '''
    debug(1, 'GetAllAnnotations for user %d' % userid)

    annotations = []
    cur.execute('SELECT id from AnnotationsTable')
    res = cur.fetchall()
    debug(1, 'Found %d annotations in dbBact' % len(res))
    for cres in res:
        cannotationid = cres[0]
        err, cannotation = GetAnnotationsFromID(con, cur, cannotationid, userid=userid)
        if err:
            debug(2, 'error for annotationid %d: %s' % (cannotationid, err))
            continue
        annotations.append(cannotation)
    debug(1, 'Got details for %d annotations' % len(annotations))
    return '', annotations


def GetSequenceStringAnnotations(con, cur, sequence, region=None, userid=0):
    """
    Get summary strings for all annotations for a sequence. Returns a list of annotation summary strings (empty list if sequence is not found)

    Parameters
    ----------
    con,cur :
    sequence : str ('ACGT')
        the sequence to search for in the database
    region : int (optional)
        None to not compare region, or the regionid the sequence is from
    userid : int (optional)
        the id of the user requesting the annotations. Private annotations with non-matching user will not be returned

    Returns
    -------
    err : str
        The error encountered or '' if ok
    details: list of dict
        a list of summary string and information about each annotations. contains:
            'annotationid' : int
                the annotation id in the database (can be used to find the link to the annotation page)
            'annotation_string' : str
                string summarizing the annotation (i.e. 'higher in ibd compared to control in human, feces')
    """
    res = []
    debug(1, 'GetSequenceStringAnnotations for sequence %s' % sequence)
    err, annotations = GetSequenceAnnotations(con, cur, sequence, region=region, userid=userid)
    if err:
        return err, res
    debug(1, 'Got %s annotations' % len(annotations))
    for cannotation in annotations:
        cres = {}
        cres['annotationid'] = cannotation['annotationid']
        cres['annotation_string'] = _get_annotation_string(cannotation)
        res.append(cres)
    return '', res


def _get_annotation_string(cann):
    '''Get nice string summaries of annotation

    Parameters
    ----------
    cann : dict
        items of the output of get_seq_annotations()

    Returns
    -------
    desc : str
        a short summary of the annotation
    '''
    cdesc = ''
    if cann['description']:
        cdesc += cann['description'] + ' ('
    if cann['annotationtype'] == 'diffexp':
        chigh = []
        clow = []
        call = []
        for cdet in cann['details']:
            if cdet[0] == 'all':
                call.append(cdet[1])
                continue
            if cdet[0] == 'low':
                clow.append(cdet[1])
                continue
            if cdet[0] == 'high':
                chigh.append(cdet[1])
                continue
        cdesc += ' high in '
        for cval in chigh:
            cdesc += cval + ' '
        cdesc += ' compared to '
        for cval in clow:
            cdesc += cval + ' '
        cdesc += ' in '
        for cval in call:
            cdesc += cval + ' '
    elif cann['annotationtype'] == 'isa':
        cdesc += ' is a '
        for cdet in cann['details']:
            cdesc += 'cdet,'
    elif cann['annotationtype'] == 'contamination':
        cdesc += 'contamination'
    else:
        cdesc += cann['annotationtype'] + ' '
        for cdet in cann['details']:
            cdesc = cdesc + ' ' + cdet[1] + ','
    return cdesc


# def get_annotation_term_pairs(cann, max_terms=20):
#     '''Get the pairs of terms in the annotation and their type

#     Parameters
#     ----------
#     cann : dict
#         items of the output of get_seq_annotations()

#     Returns
#     -------
#     list of str of term1 + "+" + term2 (sorted alphabetically term1<term2)
#     if term is "lower in", it will be preceeded by "-"
#     '''
#     term_pairs = []
#     details = cann['details']
#     if len(details) <= max_terms:
#         for p1 in range(len(details)):
#             # print('now detail term idx %d' % p1)
#             for p2 in range(p1 + 1, len(details)):
#                 det1 = details[p1]
#                 det2 = details[p2]
#                 term1 = det1[1]
#                 term2 = det2[1]
#                 type1 = det1[0]
#                 type2 = det2[0]
#                 if type1 == 'low':
#                     term1 = '-' + term1
#                 if type2 == 'low':
#                     term2 = '-' + term2
#                 cnew_type = 'all'
#                 if type1 == type2:
#                     cnew_type == type1
#                 cnew_term = sorted([term1, term2])
#                 cnew_term = "+".join(cnew_term)
#                 # cnew_term = '%s+%s' % (term1, term2)
#                 term_pairs.append(cnew_term)
#         # print('new details: %d' % len(details))
#     return term_pairs


def get_annotation_term_pairs(cann, max_terms=20, get_pairs=True, get_singles=True):
    '''Get the pairs of terms in the annotation and their type

    Parameters
    ----------
    cann : dict
        items of the output of get_seq_annotations()

    Returns
    -------
    list of str of term1 + "+" + term2 (sorted alphabetically term1<term2)
    if term is "lower in", it will be preceeded by "-"
    '''
    term_pairs = []
    details = cann['details']
    # add single terms
    if get_singles:
        for cdetail in details:
            cterm = cdetail[1]
            ctype = cdetail[0]
            if ctype == 'low':
                cterm = '-' + cterm
            term_pairs.append(cterm)

    # add term pairs
    if get_pairs:
        if len(details) <= max_terms:
            for p1 in range(len(details)):
                # print('now detail term idx %d' % p1)
                for p2 in range(p1 + 1, len(details)):
                    det1 = details[p1]
                    det2 = details[p2]
                    term1 = det1[1]
                    term2 = det2[1]
                    type1 = det1[0]
                    type2 = det2[0]
                    if type1 == 'low':
                        term1 = '-' + term1
                    if type2 == 'low':
                        term2 = '-' + term2
                    cnew_type = 'all'
                    if type1 == type2:
                        cnew_type == type1
                    cnew_term = sorted([term1, term2])
                    cnew_term = "+".join(cnew_term)
                    # cnew_term = '%s+%s' % (term1, term2)
                    term_pairs.append(cnew_term)
            # print('new details: %d' % len(details))
    return term_pairs


def get_fast_annotations_gg_silva(con, cur, seq_db_ids, db_name='silva', userid=0, get_term_info=True, get_all_exp_annotations=True):
    '''
    Get annotations for a list of sequences in a compact form based on the silva/greengenes ids

    input:
    con,cur :
    seq_db_ids: list of str
        the sequences database identifiers to search for (i.e. 'FJ978486.1.1387' for silva or '1111883' for greengenes)
   db_name : str (optional)
        the database for which the id originated. options are "silva" or "gg"
    userid : int (optional)
        the id of the user requesting the annotations. Provate annotations with non-matching user will not be returned
    get_term_info : bool (optional)
        True (default) to get the information about each term, False to skip this step
    get_all_exp_annotations: bool (optional)
        True (default) to get all annotations for each experiment which the sequence appear in at least one annotation.
        False to get just the annotations where the sequence appears

    output:
    err : str
        The error encountered or '' if ok
    annotations : dict of {annotationid : annotation details (see GetAnnotationsFromID() }
        a dict containing all annotations relevant to any of the sequences and the details about them
        * includes 'parents' - list of all ontology term parents for each annotation
    seq_db_id_seqs : list of list of str
        the seqyences (ACGT) associated with each seq_db_id. in order of the query seq_db_ids
        (so the first entry is a list of all dbbact sequences associated with the first silva/gg id)
    term_info : dict of {term, dict}
        Information about each term which appears in the annotation parents. Key is the ontolgy term. the value dict is:
            'total_annotations' : int
                total number of annotations where this term appears (as a parent)
            'total_sequences' : int
                total number of sequences in annotations where this term appears (as a parent)
    seq_db_id_annotations: list of (list of dict of {annotationid(int): count(int)})
        the ids and counts of the annotations matching each seq_db_id (i.e. silva/gg) ordered by the query order.
        the dbbact annotation ids (matching the annotations dict) are the key, and the number of dbbact sequences having this annotation is the value (note that each seq_db_id can appear in several dbbact sequences,
        and therefore may match several sequences with this annotation, so this will manifest in the count).
    '''
    debug(2, 'getting fast annotations gg_silva for %d ids' % len(seq_db_ids))
    # the dbbact sequences associated with each seq_db_id
    seq_db_id_seqs = []
    # the dbbact sequence ids for each silva/gg db_id
    seq_ids = {}
    # all the sequences we encountered (since can have same sequence matching multiple db_ids)
    all_seqs = set()
    # get the dbbact ids for each db_id
    for cid in seq_db_ids:
        err, ids, seqs = dbsequences.get_seqs_from_db_id(con, cur, db_name=db_name, db_seq_id=cid)
        if err:
            return err, {}, [], {}, []
        seq_ids[cid] = seqs
        all_seqs = all_seqs.union(set(seqs))
        seq_db_id_seqs.append(seqs)
    # get the annotations for all the sequences
    all_seqs = list(all_seqs)
    debug(2, 'got %d unique sequences for all db_ids' % len(all_seqs))
    err, annotations, seqannotations, term_info = GetFastAnnotations(con, cur, all_seqs, region=None, userid=userid, get_term_info=get_term_info, get_all_exp_annotations=get_all_exp_annotations)
    if err:
        return err, {}, [], {}, []

    # create the seq_db_id_annotations parameter
    # first we need to see for each sequenceid, in what annotations is participated
    seq_annotations_dict = {}
    for cseqpos, cseqannotationids in seqannotations:
        cseq = all_seqs[cseqpos]
        seq_annotations_dict[cseq] = cseqannotationids

    seq_db_id_annotations = []
    for cid in seq_db_ids:
        cseqs = seq_ids[cid]
        cseq_annotations = defaultdict(int)
        for ccseq in cseqs:
            for canno in seq_annotations_dict[ccseq]:
                cseq_annotations[canno] += 1
        seq_db_id_annotations.append(dict(cseq_annotations))

    return '', annotations, seq_db_id_seqs, term_info, seq_db_id_annotations
