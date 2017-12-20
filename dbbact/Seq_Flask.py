import json
from flask import Blueprint, request, g
from flask.ext.login import login_required, current_user
import dbsequences
import dbannotations
import dbontology
from utils import debug, getdoc
from autodoc import auto
# NOTE: local flask_cors module, not pip installed!
from flask_cors import crossdomain

Seq_Flask_Obj = Blueprint('Seq_Flask_Obj', __name__, template_folder='templates')
# CORS(Seq_Flask_Obj)


@Seq_Flask_Obj.route('/sequences/add', methods=['POST', 'GET'])
@auto.doc()
def add_sequences():
    """
    Title: Add new sequences (or return seqid for ones that exist)
    URL: /sequences/add
    Method: POST
    URL Params:
    Data Params: JSON
        {
            "sequences" : list of str
                the sequences to add (acgt)
            "taxonomies" : list of str (optional)
                the taxonomy per sequence (if not provided, na will be used)
            "ggids" : list of int (optional)
                list of GreenGenes id per sample (if not provided, 0 will be used)
            "primer" : str
                name of the primer region (i.e. 'V4'). if region does not exist, will fail
        }
    Success Response:
        Code : 201
        Content :
        {
            "seqIds" : list of int
                the new sequence id per sequence in the list
        }
    Details:
        Validation:
        Action:
        Add all sequences that don't already exist in SequencesTable
    """
    cfunc = add_sequences
    if request.method == 'GET':
        return(getdoc(cfunc))
    alldat = request.get_json()
    sequences = alldat.get('sequences')
    if sequences is None:
        return(getdoc(cfunc))
    taxonomies = alldat.get('taxonomies')
    ggids = alldat.get('ggids')
    primer = alldat.get('primer')
    if primer is None:
        return(getdoc(cfunc))

    err, seqids = dbsequences.AddSequences(g.con, g.cur, sequences=sequences, taxonomies=taxonomies, ggids=ggids, primer=primer)
    if err:
        return(err, 400)
    debug(2, 'added/found %d sequences' % len(seqids))
    return json.dumps({"seqIds": seqids})


@Seq_Flask_Obj.route('/sequences/getid', methods=['GET'])
@auto.doc()
def get_sequenceid():
    """
    Title: Get id for a given new sequences (or return -1 if does not exist)
    URL: /sequences/getid
    Method: GET
    URL Params:
    Data Params: JSON
        {
            "sequence" : str
                the sequence to get data about
            "no_shorter" : bool (optional)
                False (default) to get also shorter sequences from DB if matching.
                True to get only sequences at least as long as the query
            "no_longer" : bool (optional)
                False (default) to get also longer sequences from DB if matching on query length.
                True to get only sequences not longer than the query
        }
    Success Response:
        Code : 201
        Content :
        {
            "seqId" : list of int
                the sequence ids, or []] if doesn't exists
                Note: can be more than 1 id since we are looking for
        }
    Details:
        Validation:
        Action:
    """
    cfunc = get_sequenceid
    alldat = request.get_json()
    sequence = alldat.get('sequence')
    no_shorter = alldat.get('no_shorter', False)
    no_longer = alldat.get('no_longer', False)
    if sequence is None:
        return(getdoc(cfunc))

    err, seqid = dbsequences.GetSequenceId(g.con, g.cur, sequence=sequence, no_shorter=no_shorter, no_longer=no_longer)
    if err:
        return(err, 400)
    debug(2, 'found sequences')
    return json.dumps({"seqId": seqid})


@login_required
@Seq_Flask_Obj.route('/sequences/get_annotations', methods=['GET'])
@auto.doc()
def get_sequence_annotations():
    """
    Title: Query sequence:
    Description : Get all the annotations about a given sequence
    URL: /sequences/get_annotations
    Method: GET
    URL Params:
    Data Params: JSON
        {
            sequence : str
                the DNA sequence string to query the database (can be any length)
            region : int (optional)
                the region id (default=1 which is V4 515F 806R)
            get_term_info : bool (optional)
                True (default) to get information about all ontology predecessors of terms of all annotations of the sequence.
    Success Response:
        Code : 200
        Content :
        {
            "taxonomy" : str
            (taxonomy from SequencesTable)
            "annotations" : list of
                {
                    "annotationid" : int
                        the id of the annotation
                    "userid" : int
                        The user id
                        (id from UsersTable)
                    "user" : str
                        name of the user who added this annotation
                        (userName from UsersTable)
                    "addedDate" : str (DD-MM-YYYY HH:MM:SS)
                        date when the annotation was added
                        (addedDate from CurationsTable)
                    "expid" : int
                        the ID of the experiment from which this annotation originated
                        (uniqueId from ExperimentsTable)
                        (see Query Experiment)
                    "currType" : str
                        curration type (differential expression/contaminant/etc.)
                        (description from CurationTypesTable)
                    "method" : str
                        The method used to detect this behavior (i.e. observation/ranksum/clustering/etc")
                        (description from MethodTypesTable)
                    "agentType" : str
                        Name of the program which submitted this annotation (i.e. heatsequer)
                        (description from AgentTypesTable)
                    "description" : str
                        Free text describing this annotation (i.e. "lower in green tomatoes comapred to red ones")
                    "private" : bool
                        True if the curation is private, False if not
                    "CurationList" : list of
                        {
                            "detail" : str
                                the type of detail (i.e. ALL/HIGH/LOW)
                                (description from CurationDetailsTypeTable)
                            "term" : str
                                the ontology term for this detail (i.e. feces/ibd/homo sapiens)
                                (description from OntologyTable)
                        }
                }
            term_info : dict of {term: dict}
            Information about all ontology terms associated with any of the annotations (including predecessors)
                key: term (str)
                value: dict of pairs:
                    'total_annotations' : number of annotations having this term in the database (int)
                    'total_sequences' : number of sequences in annotations having this term in the database (int)
        }
    Details :
        Validation:
            If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
            If annotation is not private, return it (no need for authentication)
    """
    cfunc = get_sequence_annotations
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    sequence = alldat.get('sequence')
    if sequence is None:
        return('sequence parameter missing', 400)
    get_term_info = alldat.get('get_term_info', True)

    err, details = dbannotations.GetSequenceAnnotations(g.con, g.cur, sequence, userid=current_user.user_id)
    if err:
        debug(6, err)
        return ('Problem geting details. error=%s' % err, 400)
    if get_term_info:
        term_info = dbontology.get_annotations_term_counts(g.con, g.cur, details)
    else:
        term_info = {}
    return json.dumps({'annotations': details, 'term_info': term_info})


@login_required
@Seq_Flask_Obj.route('/sequences/get_list_annotations', methods=['GET'])
@auto.doc()
def get_sequence_list_annotations():
    """
    Title: Query sequence:
    Description : Get all the annotations about a list of sequences
    URL: /sequences/get_annotations
    Method: GET
    URL Params:
    Data Params: JSON
        {
            sequences : list of str ('ACGT')
                the list of sequence strings to query the database (can be any length)
            region : int (optional)
                the region id (default=1 which is V4 515F 806R)
    Success Response:
        Code : 200
        Content :
        {
            'seqannotations': list
            list of:
                {
                "taxonomy" : str
                (taxonomy from SequencesTable)
                "annotations" : list of
                    {
                        "annotationid" : int
                            the id of the annotation
                        "user" : str
                            name of the user who added this annotation
                            (userName from UsersTable)
                        "addedDate" : str (DD-MM-YYYY HH:MM:SS)
                            date when the annotation was added
                            (addedDate from CurationsTable)
                        "expid" : int
                            the ID of the experiment from which this annotation originated
                            (uniqueId from ExperimentsTable)
                            (see Query Experiment)
                        "currType" : str
                            curration type (differential expression/contaminant/etc.)
                            (description from CurationTypesTable)
                        "method" : str
                            The method used to detect this behavior (i.e. observation/ranksum/clustering/etc")
                            (description from MethodTypesTable)
                        "agentType" : str
                            Name of the program which submitted this annotation (i.e. heatsequer)
                            (description from AgentTypesTable)
                        "description" : str
                            Free text describing this annotation (i.e. "lower in green tomatoes comapred to red ones")
                        "private" : bool
                            True if the curation is private, False if not
                        "CurationList" : list of
                            {
                                "detail" : str
                                    the type of detail (i.e. ALL/HIGH/LOW)
                                    (description from CurationDetailsTypeTable)
                                "term" : str
                                    the ontology term for this detail (i.e. feces/ibd/homo sapiens)
                                    (description from OntologyTable)
                            }
                    }
                }
        }
    Details :
        Validation:
            If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
            If annotation is not private, return it (no need for authentication)
    """
    cfunc = get_sequence_list_annotations
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    sequences = alldat.get('sequences')
    if sequences is None:
        return('sequences parameter missing', 400)
    seqannotations = []
    for cseq in sequences:
        err, details = dbannotations.GetSequenceAnnotations(g.con, g.cur, cseq, userid=current_user.user_id)
        # if err:
        #   debug(6,err)
        #   return ('Problem geting details. error=%s' % err,400)
        seqannotations.append(details)

    return json.dumps({'seqannotations': seqannotations})


# # need to add conversion to nice string
# @login_required
# @Seq_Flask_Obj.route('/sequences/get_annotations_string', methods=['GET'])
# @auto.doc()
# def get_annotations_string():
#     cfunc = get_annotations_string
#     alldat = request.get_json()
#     if alldat is None:
#         return(getdoc(cfunc))
#     sequence = alldat.get('sequence')
#     if sequence is None:
#         return('sequence parameter missing', 400)
#     err, details = dbannotations.GetSequenceAnnotations(g.con, g.cur, sequence, userid=current_user.user_id)
#     if err:
#         debug(6, err)
#         return ('Problem geting details. error=%s' % err, 400)
#     return json.dumps({'annotations': details})


@login_required
@Seq_Flask_Obj.route('/sequences/get_fast_annotations', methods=['GET'])
@auto.doc()
def get_fast_annotations():
    """
    Title: Get Fast Annotations
    Description : Get annotations for a list of sequences in a compressed form
    URL: /sequences/get_fast_annotations
    Method: GET
    URL Params:
    Data Params: JSON
        {
            sequences : list of str ('ACGT')
                the list of sequence strings to query the database (can be any length)
            region : int (optional)
                the region id (default=1 which is V4 515F 806R)
            get_term_info: bool (optional)
                True (info) to return also information about each term, False not to return
    Success Response:
        Code : 200
        Content :
        {
            annotations: dict of (annotationid: details):
                    annotationid : the annotationid used in seqannotations
                    details:
                {
                    "annotationid" : int
                        the id of the annotation
                    "user" : str
                        name of the user who added this annotation
                        (userName from UsersTable)
                    "addedDate" : str (DD-MM-YYYY HH:MM:SS)
                        date when the annotation was added
                        (addedDate from CurationsTable)
                    "expid" : int
                        the ID of the experiment from which this annotation originated
                        (uniqueId from ExperimentsTable)
                        (see Query Experiment)
                    "currType" : str
                        curration type (differential expression/contaminant/etc.)
                        (description from CurationTypesTable)
                    "method" : str
                        The method used to detect this behavior (i.e. observation/ranksum/clustering/etc")
                        (description from MethodTypesTable)
                    "agentType" : str
                        Name of the program which submitted this annotation (i.e. heatsequer)
                        (description from AgentTypesTable)
                    "description" : str
                        Free text describing this annotation (i.e. "lower in green tomatoes comapred to red ones")
                    "private" : bool
                        True if the curation is private, False if not
                    "CurationList" : list of
                        {
                            "detail" : str
                                the type of detail (i.e. ALL/HIGH/LOW)
                                (description from CurationDetailsTypeTable)
                            "term" : str
                                the ontology term for this detail (i.e. feces/ibd/homo sapiens)
                                (description from OntologyTable)
                        }
                    "parents" : list of tuples (type, list of terms)
                        {
                            type : type of the annotation type ('high'/'low','all')
                            list of terms - list of ontology terms which are annotated or parents of annotated ontology term
                        }
                }
            seqannotations : list of (seqid, annotationids):
            {
                    seqpos : position of the sequence in the list
                    annotationids : list of int
                            the annotationsid associated with this sequence
            }
            term_info : dict of {term, dict}:
            Information about each term which appears in the annotation parents. Key is the ontolgy term. the value dict is:
            {
                    'total_annotations' : int
                        total number of annotations where this term appears (as a parent)
                    'total_sequences' : int
                        total number of sequences in annotations where this term appears (as a parent)
            }
        }
    Details :
        Return a dict of details for all the annotations associated with at least one of the sequences used as input, and a list of seqpos and the associated annotationids describing it
        (i.e. a sparse representation of the annotations vector for the input sequence list)
    Validation:
        If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
        If annotation is not private, return it (no need for authentication)
    """
    cfunc = get_fast_annotations
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    sequences = alldat.get('sequences')
    if sequences is None:
        return('sequences parameter missing', 400)
    region = alldat.get('region')
    get_term_info = alldat.get('get_term_info', True)
    err, annotations, seqannotations, term_info = dbannotations.GetFastAnnotations(g.con, g.cur, sequences, region=region, userid=current_user.user_id, get_term_info=get_term_info)
    if err:
        errmsg = 'error encountered while getting the fast annotations: %s' % err
        debug(6, errmsg)
        return(errmsg, 400)
    res = {'annotations': annotations, 'seqannotations': seqannotations, 'term_info': term_info}
    return json.dumps(res)


@login_required
@Seq_Flask_Obj.route('/sequences/get_taxonomy_annotation_ids', methods=['GET'])
@auto.doc()
def get_taxonomy_annotation_ids():
    """
    Title: Get taxonomy annotation ids
    Description : Get annotation ids for taxonomy substring
    URL: /sequences/get_taxonomy_annotation_ids
    Method: GET
    URL Params:
    Data Params: JSON
        {
            taxonomy : str
                the taxonomy substring to look for
        }
    Success Response:
        Code : 200
        Content :
        {
            annotationids : list of (int, int) (annotationid, count)
                the annotation ids and number of sequences from the taxonomy appearing in that annotation *for all annotations that contain at least 1 sequence from the requested taxonomy)
        }
    Details :
        Returns a list of annotationids. can get the annotation details for them via another api call to sequences/get_fast_annotations or sequences/
    Validation:
        If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
        If annotation is not private, return it (no need for authentication)
    """
    cfunc = get_taxonomy_annotation_ids
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    taxonomy = alldat.get('taxonomy')
    if taxonomy is None:
        return('taxonomy parameter missing', 400)
    err, annotationids = dbsequences.GetTaxonomyAnnotationIDs(g.con, g.cur, taxonomy, userid=current_user.user_id)
    if err:
        errmsg = 'error encountered searching for taxonomy annotations for taxonomy %s: %s' % (taxonomy, err)
        debug(6, errmsg)
        return(errmsg, 400)
    return json.dumps({'annotationids': annotationids})


@login_required
@Seq_Flask_Obj.route('/sequences/get_taxonomy_annotations', methods=['GET'])
@auto.doc()
def get_taxonomy_annotations():
    """
    Title: Get taxonomy annotation ids
    Description : Get annotation ids for taxonomy substring
    URL: /sequences/get_taxonomy_annotation_ids
    Method: GET
    URL Params:
    Data Params: JSON
        {
            taxonomy : str
                the taxonomy substring to look for
        }
    Success Response:
        Code : 200
        Content :
        {
            list of (annotation, counts)
                the annotation details for all annotations that contain a sequence with the requested taxonomy (see /sequences/get_annotations) and the count of taxonomy sequences with the annotation
        }
    Validation:
        If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
        If annotation is not private, return it (no need for authentication)
    """
    cfunc = get_taxonomy_annotations
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    taxonomy = alldat.get('taxonomy')
    if taxonomy is None:
        return('taxonomy parameter missing', 400)
    err, annotations = dbsequences.GetTaxonomyAnnotations(g.con, g.cur, taxonomy, userid=current_user.user_id)
    if err:
        errmsg = 'error encountered searching for taxonomy annotations for taxonomy %s: %s' % (taxonomy, err)
        debug(6, errmsg)
        return(errmsg, 400)
    return json.dumps({'annotations': annotations})


@Seq_Flask_Obj.route('/sequences/get_info', methods=['GET'])
@auto.doc()
def get_sequence_info():
    """
    Title: Get sequences information
    Description : Get information (sequence, taxonomy) from sequence ids
    URL: /sequences/get_info
    Method: GET
    URL Params:
    Data Params: JSON
        {
            seqids : int or list of int
                the sequence ids to get information for
        }
    Success Response:
        Code : 200
        Content :
        {
            'sequences' : list of dict
                information about each sequence in the annotation
                {
                    'seq' : str (ACGT)
                        the sequence
                    'taxonomy' : str
                        the taxonomy of the sequence (or '' if not present)
                }
        }
    Validation:
    """
    cfunc = get_sequence_info
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    seqids = alldat.get('seqids')
    if seqids is None:
        return('seqids parameter missing', 400)
    err, sequences = dbsequences.SeqFromID(g.con, g.cur, seqids)
    if err:
        errmsg = 'error encountered searching for sequence information: %s' % err
        debug(6, errmsg)
        return(errmsg, 400)
    return json.dumps({'sequences': sequences})


@login_required
@Seq_Flask_Obj.route('/sequences/get_string_annotations', methods=['GET', 'POST', 'OPTIONS'])
@crossdomain(origin='*', headers=['Content-Type'])
@auto.doc()
def get_sequence_string_annotations():
    """
    Title: Get sequence string annotations
    Description : Get description (string) and html link for all annotations of a given sequence
    URL: /sequences/get_string_annotations
    Method: GET, POST
    URL Params:
    Data Params: JSON
        {
            sequence : str
                the DNA sequence string to query the database (can be any length)
            region : int (optional)
                the region id (default=1 which is V4 515F 806R)
    Success Response:
        Code : 200
        Content :
        {
            "annotations" : list of
                {
                    "annotationid" : int
                        the id of the annotation
                    "annotation_summary" : str
                        String summarizing the annotation (i.e. 'higher in feces compared to saliva in homo spiens')
                }
        }
    Details :
        Validation:
            If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
            If annotation is not private, return it (no need for authentication)
    """
    cfunc = get_sequence_string_annotations
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(cfunc))
    sequence = alldat.get('sequence')
    if sequence is None:
        return('sequence parameter missing', 400)

    err, details = dbannotations.GetSequenceStringAnnotations(g.con, g.cur, sequence, userid=current_user.user_id)
    if err:
        debug(6, err)
        return ('Problem geting details. error=%s' % err, 400)
    res = json.dumps({'annotations': details})
    # return Response(res, content_type='text/xml; charset=utf-8')
    return res
