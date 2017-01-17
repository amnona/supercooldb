from flask import Blueprint,request,g
import json
import dbannotations
import dbsequences
from utils import debug,getdoc
from flask.ext.login import current_user
from flask.ext.login import login_required


Annotation_Flask_Obj = Blueprint('Annottion_Flask_Obj', __name__,template_folder='templates')


@login_required
@Annotation_Flask_Obj.route('/annotations/add',methods=['POST','GET'])
def add_annotations():
	"""
	Title: Add new annotation
	URL: /annotations/add
	Method: POST
	URL Params:
	Data Params: JSON
		{
			"expId" : int
				(expId from ExperimentsTable)
			"sequences" : list of str (ACGT)
				the sequences to add the annotation to
			"region" : str (optional)
				the name of the primner region where the sequence is from or None for 'na'
				(id from PrimersTable)
			"annotationType" : str
				annotation type (differential expression/contaminant/etc.)
				(description from AnnotationTypesTable)
			"method" : str (optional)
				The method used to detect this behavior (i.e. observation/ranksum/clustering/etc")
				(description from MethodTypesTable)
			"agentType" : str (optional)
				Name of the program which submitted this annotation (i.e. heatsequer)
				(description from AgentTypesTable)
			"description" : str (optional)
				Free text describing this annotation (i.e. "lower in green tomatoes comapred to red ones")
			"private" : bool (optional)
				default=False
				is this annotation private
				private from AnnotationsTable
			"AnnotationList" : list of
				{
					"detail" : str
						the type of detail (i.e. ALL/HIGH/LOW)
						(description from AnnotationDetailsTypeTable)
					"term" : str
						the ontology term for this detail (i.e. feces/ibd/homo sapiens)
						(description from OntologyTable)
				}
		}
	Success Response:
		Code : 201
		Content :
		{
			"annotationId" : int
			the id from AnnotationsTable for the new annotation.
		}
	Details:
		Validation:
			expId exists in ExperimentsTable
			sequences are all valid ACGT sequences
			region is a valid id from PrimersTable
		Action:
			iterate over sequences, if sequence does not exist, add it to SequencesTable (what to do about taxonomy? - keep it empty?)
			if currType does not exist, add it to AnnotationTypesTable
			if method does not exist, add it to MethodTypesTable
			if agentType does not exist, add it to AgentTypesTable
			iterate over all AnnotationList:
				if detail does not exist, add it to AnnotationsDetailsTypeTable
				if term does not exist, add it to OntologyNamesTable
			Create a new Annotation in AnnotationsTable
			Add all sequence/Annotation pairs to SequenceAnnotationTable
			Add all annotation details to AnnotationsTable (automatically adding userId and addedDate)
			Add all pairs to AnnotationListTable
	"""
	cfunc=add_annotations
	if request.method=='GET':
		return(getdoc(cfunc),400)
	alldat=request.get_json()
	expid=alldat.get('expId')
	if expid is None:
		return(getdoc(cfunc),400)
	sequences=alldat.get('sequences')
	if sequences is None:
		return(getdoc(cfunc),400)
	primer=alldat.get('region')
	if primer is None:
		primer='na'
	annotationtype=alldat.get('annotationType')
	method=alldat.get('method')
	agenttype=alldat.get('agentType')
	description=alldat.get('description')
	private=alldat.get('private')
	userid=current_user.user_id
	annotationlist=alldat.get('annotationList')
	err,annotationid=dbannotations.AddSequenceAnnotations(g.con,g.cur,sequences,primer,expid,annotationtype,annotationlist,method,description,agenttype,private,userid=userid,commit=True)
	if not err:
		debug(2,'added sequece annotations')
		return json.dumps({"annotationId":annotationid})
	debug(6,"error encountered %s" % err)
	return ("error enountered %s" % err,400)


@login_required
@Annotation_Flask_Obj.route('/annotations/get_sequences',methods=['GET'])
def get_annotation_sequences():
	"""
	Title: get_sequences
	Description : Get all sequences ids associated with an annotation
	URL: annotations/get_sequences
	Method: GET
	URL Params:
	Data Params: JSON
		{
			annotationid : int
				the annotationid to get the sequences for
		}
	Success Response:
		Code : 200
		Content :
		{
			seqids : list of int
				the seqids for all sequences participating in this annotation
		}
	Details :
		Validation:
			If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
			If annotation is not private, return it (no need for authentication)
	"""
	cfunc=get_annotation_sequences
	alldat=request.get_json()
	if alldat is None:
		return ('No json parameters supplied',400)
	annotationid=alldat.get('annotationid')
	if annotationid is None:
		return('annotationid parameter missing',400)
	err,seqids=dbannotations.GetSequencesFromAnnotationID(g.con,g.cur,annotationid,userid=current_user.user_id)
	if err:
		debug(6,err)
		return ('Problem geting details. error=%s' % err,400)
	return json.dumps({'seqids':seqids})


@login_required
@Annotation_Flask_Obj.route('/annotations/get_full_sequences',methods=['GET'])
def get_annotation_full_sequences():
	"""
	Title: get_full_sequences
	Description : Get all the sequences (ACGT) associated with an annotation
	URL: annotations/get_full_sequences
	Method: GET
	URL Params:
	Data Params: JSON
		{
			annotationid : int
				the annotationid to get the sequences for
		}
	Success Response:
		Code : 200
		Content :
		{
			sequences : list of str (ACGT)
				the sequences participating in this annotation
		}
	Details :
		Validation:
			If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
			If annotation is not private, return it (no need for authentication)
	"""
	cfunc=get_annotation_full_sequences
	alldat=request.get_json()
	if alldat is None:
		return ('No json parameters supplied',400)
	annotationid=alldat.get('annotationid')
	if annotationid is None:
		return('annotationid parameter missing',400)
	err,seqids=dbannotations.GetFullSequencesFromAnnotationID(g.con,g.cur,annotationid,userid=current_user.user_id)
	if err:
		debug(6,err)
		return ('Problem geting details. error=%s' % err,400)
	return json.dumps({'sequences':seqids})


@login_required
@Annotation_Flask_Obj.route('/annotations/delete',methods=['GET','POST'])
def delete_annotation():
	"""
	Title: delete
	Description : Delete annotation
	URL: annotations/delete
	Method: POST
	URL Params:
	Data Params: JSON
		{
			annotationid : int
				the annotationid to delete
		}
	Success Response:
		Code : 200
		Content :
		{
			annotationid : int
				the annotationid deleted
		}
	Details :
		Validation:
			If user is not logged in, cannot delete
			Can only delete annotations created by the user
	"""
	cfunc=delete_annotation
	if request.method=='GET':
		return(getdoc(cfunc),400)
	alldat=request.get_json()
	if alldat is None:
		return ('No json parameters supplied',400)
	annotationid=alldat.get('annotationid')
	if annotationid is None:
		return('annotationid parameter missing',400)
	err=dbannotations.DeleteAnnotation(g.con,g.cur,annotationid,userid=current_user.user_id)
	if err:
		debug(6,err)
		return ('Problem deleting annotation. error=%s' % err,400)
	return json.dumps({'annotationid':annotationid})


@login_required
@Annotation_Flask_Obj.route('/annotations/delete_sequences_from_annotation',methods=['GET','POST'])
def delete_sequences_from_annotation():
	"""
	Title: Delete sequences from annotation
	Description : Delete sequences from an existing annotation
	URL: annotations/delete_sequences_from_annotation
	Method: POST
	URL Params:
	Data Params: JSON
		{
			annotationid : int
				the annotationid to delete
			sequences : list of str ('ACGT')
				the sequences to delete from the annotation
		}
	Success Response:
		Code : 200
		Content :
		{
			annotationid : int
				the annotationid from which the sequences were deleted
		}
	Details :
		Validation:
			If user is not logged in, cannot delete non-annonymous
			Can only delete annotations created by the user
	"""
	cfunc=delete_sequences_from_annotation
	if request.method=='GET':
		return(getdoc(cfunc),400)
	alldat=request.get_json()
	if alldat is None:
		return ('No json parameters supplied',400)
	annotationid=alldat.get('annotationid')
	if annotationid is None:
		return('annotationid parameter missing',400)
	sequences=alldat.get('sequences')
	if sequences is None:
		return('sequences parameter missing',400)
	err=dbannotations.DeleteSequenceFromAnnotation(g.con,g.cur,sequences,annotationid,userid=current_user.user_id)
	if err:
		debug(6,err)
		return ('Problem deleting sequences. error=%s' % err,400)
	return json.dumps({'annotationid':annotationid})



@login_required
@Annotation_Flask_Obj.route('/annotations/get_annotation',methods=['GET'])
def get_annotation():
	"""
	Title: get_annotation
	Description : Get all annotations associated with an ontology term
	URL: annotations/get_annotation
	Method: GET
	URL Params:
	Data Params: JSON
		{
			annotationid : int
				the annotationid to get the details for
		}
	Success Response:
		Code : 200
		Content :
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
	Details :
		Validation:
			If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
			If annotation is not private, return it (no need for authentication)
	"""
	cfunc=get_annotation
	annotationid=int(request.args.get('annotationid'))
	if annotationid is None:
		return(getdoc(cfunc))
	err,annotation=dbannotations.GetAnnotationsFromID(g.con,g.cur,annotationid)
	if err:
		debug(6,err)
		return ('Problem geting details. error=%s' % err,400)
	return json.dumps(annotation)


@login_required
@Annotation_Flask_Obj.route('/annotations/get_annotation_ontology_parents',methods=['GET'])
def get_annotation_ontology_parents():
	"""
	Title: get_annotation_ontology_parents
	Description : Get all the ontology terms (and their parents in the ontolgy DAG) for the annotation
	URL: annotations/get_annotation_ontology_parents
	Method: GET
	URL Params:
	Data Params: JSON
		{
			annotationid : int
				the annotationid to get the ontology parents for
		}
	Success Response:
		Code : 200
		Content :
		{
			parents : dict of (str:list of str) (detail type (i.e. 'higher in'), list of ontology terms)
		}
	Details :
		Validation:
			If an annotation is private, return it only if user is authenticated and created the curation. If user not authenticated, do not return it in the list
			If annotation is not private, return it (no need for authentication)
	"""
	cfunc=get_annotation_ontology_parents
	annotationid=int(request.args.get('annotationid'))
	if annotationid is None:
		return(getdoc(cfunc))
	err,parents=dbannotations.GetAnnotationParents(g.con,g.cur,annotationid)
	if err:
		debug(6,err)
		return ('Problem geting details. error=%s' % err,400)
	return json.dumps(parents)
