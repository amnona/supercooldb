from flask import Blueprint,request,g
from flask.ext.login import login_required
import json
import dbsequences
import dbannotations
from utils import debug,getdoc

Seq_Flask_Obj = Blueprint('Seq_Flask_Obj', __name__,template_folder='templates')


@Seq_Flask_Obj.route('/sequences/add',methods=['POST','GET'])
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
	cfunc=add_sequences
	if request.method=='GET':
		return(getdoc(cfunc))
	alldat=request.get_json()
	sequences=alldat.get('sequences')
	if sequences is None:
		return(getdoc(cfunc))
	taxonomies=alldat.get('taxonomies')
	ggids=alldat.get('ggids')
	primer=alldat.get('primer')
	if primer is None:
		return(getdoc(cfunc))

	err,seqids=dbsequences.AddSequences(g.con,g.cur,sequences=sequences,taxonomies=taxonomies,ggids=ggids,primer=primer)
	if err:
		return(err,400)
	debug(2,'added/found %d sequences' % len(seqids))
	return json.dumps({"seqIds":seqids})


@Seq_Flask_Obj.route('/sequences/getid',methods=['GET'])
@login_required
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
		}
	Success Response:
		Code : 201
		Content :
		{
			"seqId" : int
				the sequence id, or -1 if doesn't exists
		}
	Details:
		Validation:
		Action:
	"""
	cfunc=get_sequenceid
	alldat=request.get_json()
	sequence=alldat.get('sequence')
	if sequence is None:
		return(getdoc(cfunc))

	err,seqid=dbsequences.GetSequenceId(g.con,g.cur,sequence=sequence,)
	if err:
		return(err,400)
	debug(2,'found sequences')
	return json.dumps({"seqId":seqid})


@Seq_Flask_Obj.route('/sequences/get_annotations',methods=['GET'])
@login_required
def get_sequence_annotations():
	"""
	Title: Query sequence:
	Description : Get all the annotations about a given sequence
	URL: /sequences/get_annotations
	Method: GET
	URL Params:
	Data Params: JSON
		{
			sequence : str ('ACGT')
				the sequence string to query the database (can be any length)
			region : int (optional)
				the region id (default=1 which is V4 515F 806R)
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
	cfunc=get_sequence_annotations
	alldat=request.get_json()
	if alldat is None:
		return(getdoc(cfunc))
	sequence=alldat.get('sequence')
	if sequence is None:
		return('sequence parameter missing',400)
	err,details=dbannotations.GetSequenceAnnotations(g.con,g.cur,sequence)
	if err:
		debug(6,err)
		return ('Problem geting details. error=%s' % err,400)
	return json.dumps({'annotations':details})

