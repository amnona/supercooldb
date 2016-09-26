from flask import Blueprint,request,g
import json
import dbannotations
import dbsequences
from utils import debug,getdoc

Annotation_Flask_Obj = Blueprint('Annottion_Flask_Obj', __name__,template_folder='templates')


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
	userid=alldat.get('userId')
	annotationlist=alldat.get('annotationList')
	err,annotationid=dbannotations.AddSequenceAnnotations(g.con,g.cur,sequences,primer,expid,annotationtype,annotationlist,method,description,agenttype,private,userid,commit=True)
	if not err:
		debug(2,'added sequece annotations')
		return json.dumps({"annotationId":annotationid})
	debug(6,"error encountered %s" % err)
	return ("error enountered %s" % err,400)

