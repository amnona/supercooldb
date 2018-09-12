import json
from flask import Blueprint, g, request
from flask_login import login_required
from . import dbontology
from .utils import getdoc, debug
from .autodoc import auto

Ontology_Flask_Obj = Blueprint('Ontology_Flask_Obj', __name__, template_folder='templates')


@Ontology_Flask_Obj.route('/ontology/add', methods=['GET', 'POST'])
@auto.doc()
def ontology_add_term():
    """
    Title: Add new ontology term
    URL: /ontology/add
    Description : Add a new term to the ontology term list and link to parent, synonyms
    Method: POST
    URL Params:
    Data Params: JSON
        {
            "term" : str
                the new term to add (description from OntologyTable)
            "parent" : str (optional)
                default="na"
                if supplied, the id of the parent of this term (description from OntologyTable)
            "ontologyname" : str (optional)
                default = "scdb"
                name of the ontology to which this term belongs (i.e. "doid")
                (description from OntologyNamesTable
            "synonyms" : (optional) list of
            {
                "term" : str
                    alternative names for the new ontology term
            }
        }
    Success Response:
        Code : 201
        Content :
        {
            "termid" : int
                the id of the new ontology term
        }
    Details:
        Validation:
        NA
        Action:
            if term does not exist in OnologyTable, add it (description in OntologyTable).
            Get the term id (id in OntologyTable)
            If parent is supplied, if it does not exist in OntologyTable, add it. Get the parentid (id from OntologyTable for the parent).
            Get the ontologynameid from the OntologyNamesTable. Add (ontologyId = termid, ontologyParentId = parentif, ontologyNameId = ontologynameid)
            for each sysnonym, if not in OntologyTable add it, get the synonymid, add to OntologySynymTable (idOntology = termid, idSynonym = synonymid)
    """
    cfunc = ontology_add_term
    if request.method == 'GET':
        return(getdoc(cfunc))
    alldat = request.get_json()
    term = alldat.get('term')
    if term is None:
        return('term missing', 400)
    parent = alldat.get('parent')
    if parent is None:
        parent = 'na'
    ontologyname = alldat.get('ontologyname')
    if ontologyname is None:
        ontologyname = 'scdb'
    synonyms = alldat.get('synonyms')
    err, termid = dbontology.AddTerm(g.con, g.cur, term, parent, ontologyname, synonyms)
    if err:
        debug(2, 'add_ontology_term error %s encountered' % err)
        return(err)
    return json.dumps({'termid': termid})


@Ontology_Flask_Obj.route('/ontology/get_parents', methods=['GET'])
@auto.doc()
def ontology_get_parents():
    """
    Title: Get all parents for a given ontology term
    URL: /ontology/get_parents
    Description : Get a list of all the parents for a given ontology term
    Method: GET
    URL Params:
        {
            "term" : str
                the ontology term to get the parents for
        }
    Data Params:
    Success Response:
        Code : 201
        Content :
        {
            "parents" : list of str
                list of the parent terms
        }
    Details:
        Validation:
        NA
        Action:
        Get all the parents of the ontology term
        If it is a synonym for a term, get the original term first.
        Note that if the term is in more than one ontology, will return all parents
    """
    term = request.args.get('term')
    if term is None:
        # # TODO: retrun error
        return('missing argument term', 400)
    err, parents = dbontology.GetParents(g.con, g.cur, term)
    if err:
        return(err, 400)
    return(json.dumps({'parents': parents}))


@Ontology_Flask_Obj.route('/ontology/get_term', methods=['GET'])
@auto.doc()
def ontology_get_term():
    """
    Title: Query Ontology terms
    Description : Get all ontology terms starting from a given id
                    used to update the autocomplete list in the client
    URL: /ontology/get_term
    Method: GET
    URL Params:
        startid : int
            retrieve all ontology terms with id bigger than startid (incremental update client)
            (id from OntologyTable)
    Success Response:
        Code : 200
        Content :
        {
            "terms" : list of
            {
                "id" : int
                    the ontology term id (id from OntologyTable)
                "description" : str
                    the ontology term (description from OntologyTable)
            }
        }
    """
    cid = request.args.get('startid')
    if cid is None:
        return(getdoc(ontology_get_term))
    jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTable_GetRecsByStartId(cid, con=g.con, cur=g.cur)
    return json.dumps(jsonRetData, ensure_ascii=False)


@Ontology_Flask_Obj.route('/ontology/get_synonym', methods=['GET'])
@auto.doc()
def ontology_get_synonym():
    """
    Title: Query Ontology synonyms
    Description : Get all ontology synonyms starting from a given id
                    used to update the autocomplete list in the client
    URL: /ontology/get_synonym?startid=<startid>
    Method: GET
    URL Params:
        startid : int
            retrieve all ontology synonyms with id bigger than startid (incremental update client)
            (id from OntologySynonymTable)
    Success Response:
        Code : 200
        Content :
        {
            "terms" : list of
            {
                "id" : int
                    the synonym relation id (id from SynonymTable)
                "synonymterm" : str
                    the synonym term (description from OntologyTable linked by idSynonym from OntologySynonymTable)
                "originalterm" : str
                    the ontology term to which it is a synonym (description from OntologyTable linked by idOntology)
            }
        }
    """
    cid = request.args.get('startid')
    if cid is None:
        return(getdoc(ontology_get_synonym))
    jsonRetData = db_access.DB_ACCESS_FLASK_SynonymTable_GetRecsByStartId(cid, g.con, g.cur)
    return json.dumps(jsonRetData, ensure_ascii=False)


@login_required
@Ontology_Flask_Obj.route('/ontology/get_annotations', methods=['GET'])
@auto.doc()
def get_ontology_annotations():
    """
    Title: get_annotations
    Description : Get all annotations associated with an ontology term
    URL: ontology/get_annotations
    Method: GET
    URL Params:
    Data Params: Parameters
        {
            term : str
                the ontology term to get the annotations for
        }
    Success Response:
        Code : 200
        Content : JSON
        {
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
        }
    Details :
        Validation:
            If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
            If annotation is not private, return it (no need for authentication)
    """
    cfunc = get_ontology_annotations
    ontology_term = request.args.get('term')
    if ontology_term is None:
        return(getdoc(cfunc))
    err, annotations = dbontology.GetTermAnnotations(g.con, g.cur, ontology_term)
    if err:
        debug(6, err)
        return ('Problem geting details. error=%s' % err, 400)
    return json.dumps({'annotations': annotations})


@Ontology_Flask_Obj.route('/ontology/get_all_descriptions', methods=['GET'])
@auto.doc()
def get_all_descriptions():
    """
    Title: Query Ontology
    Description : Get all ontology descriptions
    Method: GET
    Success Response:
        Code : 200
        Content :
        {
            "ontology" : list of
            {
                "description" : str
                    the ontology terms
            }
        }
    """
    jsonRetData = dbontology.GetListOfOntologies(g.con, g.cur)
    return json.dumps(jsonRetData, ensure_ascii=False)


@Ontology_Flask_Obj.route('/ontology/get_all_synonyms', methods=['GET'])
@auto.doc()
def get_all_synonyms():
    """
    Title: Query synonyms
    Description : Get all synonym descriptions
    Method: GET
    Success Response:
        Code : 200
        Content :
            "synonym" : list of
            {
                "description" : str
                    the synonym terms
            }
        }
    """
    jsonRetData = dbontology.GetListOfSynonym(g.con, g.cur)
    return json.dumps(jsonRetData, ensure_ascii=False)


@Ontology_Flask_Obj.route('/ontology/get', methods=['POST'])
@auto.doc()
def get_ontology():
    """
    Title: Return ontology id for ones that exist
    URL: /ontology/get
    Method: POST
    URL Params:
    Data Params: JSON
        {
            "ontology" : list of str
                the sequences to add (acgt)
        }
    Success Response:
        Code : 201
        Content :
        {
            "ontIds" : list of int
                id of ontologies
        }
    Details:
        Validation:
        Action:
        Get ids for list of ontologies
    """

    cfunc = get_ontology
    if request.method == 'GET':
        return(getdoc(cfunc))

    alldat = request.get_json()
    ontologies = alldat.get('ontologies')
    if ontologies is None:
        return(getdoc(cfunc))

    err, ontids = dbontology.GetIDs(g.con, g.cur, ontList=ontologies)

    if err:
        return(err, 400)
    debug(2, 'added/found %d sequences' % len(ontids))
    return json.dumps({"ontIds": ontids})


@login_required
@Ontology_Flask_Obj.route('/ontology/get_term_stats', methods=['GET'])
@auto.doc()
def get_ontology_term_stats():
    """
    Title: get_tern_stats
    Description : Get statistics about ontology terms (in how many annotations it appears)
    URL: ontology/get_term_stats
    Method: GET
    URL Params:
    Data Params: JSON
        {
            terms : list of str
                list of ontology terms to get the statistics for. Can include term pairs in the format of 'term1+term2' where term1 is alphabetically before term2
        }
    Success Response:
        Code : 200
        Content :
        {
            term_info : dict of {term, dict}
            Information about each term which appears in the annotation parents. Key is the ontolgy term. the value dict is:
            'total_annotations' : int
                total number of annotations where this term appears (as a parent)
            'total_sequences' : int
                total number of sequences in annotations where this term appears (as a parent)
        }
    Details :
        Validation:
    """
    cfunc = get_ontology_term_stats
    alldat = request.get_json()
    ontology_terms = alldat.get('terms')
    if ontology_terms is None:
        return(getdoc(cfunc))
    # term_info = dbontology.GetTermCounts(g.con, g.cur, ontology_terms)
    term_info = dbontology.get_term_counts(g.con, g.cur, ontology_terms)
    # if err:
    #     debug(6, err)
    #     return ('Problem geting term stats. error=%s' % err, 400)
    return json.dumps({'term_info': term_info})


@Ontology_Flask_Obj.route('/ontology/get_term_pair_count', methods=['GET'])
@auto.doc()
def get_term_pair_count():
    """
    Title: get_term_pair_count
    Description : Get statistics about ontology term pair (i.e. "feces+homo sapiens") (in how many experiments it appears)
    URL: ontology/get_term_pair_count
    Method: GET
    URL Params:
    Data Params: JSON
        {
            term_pairs : list of str
                list of ontology term pairs to get the experiment count for
        }
    Success Response:
        Code : 200
        Content :
        {
            term_count : dict of {term, float}
                The total number of experiments each term pair appears in
        }
    Details :
        Validation:
    """
    cfunc = get_term_pair_count
    alldat = request.get_json()
    term_pairs = alldat.get('term_pairs')
    debug(1, 'get_term_pair_count for %d term pairs' % len(term_pairs))
    if term_pairs is None:
        return(getdoc(cfunc))
    term_count = dbontology.get_term_pairs_count(g.con, g.cur, term_pairs)
    # if err:
    #     debug(6, err)
    #     return ('Problem geting term stats. error=%s' % err, 400)
    return json.dumps({'term_count': term_count})
