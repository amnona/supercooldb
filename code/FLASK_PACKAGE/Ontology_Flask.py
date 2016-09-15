from flask import Blueprint, render_template, abort,g,request
from .DB_ACCESS import db_access
import json


Ontology_Flask_Obj = Blueprint('Ontology_Flask_Obj', __name__,template_folder='templates')


def return_doc(func):
	"""
	return the json version of the doc for the function func

	input:
	func : function
		the function who's doc we want to return

	output:
	doc : str (html)
		the html of the doc of the function
	"""
	print(func.__doc__)
	s=func.__doc__
	s="<pre>\n%s\n</pre>" % s
	# s = s.replace("\r\n", "<br />")
	# s = s.replace("\n", "<br />")
	return(s)


@Ontology_Flask_Obj.route('/ontology/add_term',methods=['GET','POST'])
def ontology_add_term():
	"""
	Title: Add new ontology term
	URL: /ontology/add_term
	Description : Add a new term to the ontology term list and link to parent, synonyms
	Method: POST
	URL Params:
	Data Params:
		{
			"term" : str
				the new term to add (description from OntologyTable)
			"parent" : str (optional)
				default="root"
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
			"id" : int
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
	if request.method=='GET':
		return(return_doc(ontology_add_term))
	term=request.form.get('term')
	if term is None:
		# # TODO: retrun error
		return(return_doc(ontology_add_term))
	parent=request.form.get('parent')
	if parent is None:
		parent="root"
	ontologyname=request.form.get('ontologyname')
	if ontologyname is None:
		print("no ontology name supplied")
		ontologyname="scdb"
	synonyms=request.form.getlist('synonyms')

	# add/get the ontology term
	res = db_access.DB_ACCESS_FLASK_OntologyTable_AddOntology(term,g.con,g.cur)
	cid=res['id']

	# add/get the ontology parent term
	res = db_access.DB_ACCESS_FLASK_OntologyTable_AddOntology(parent,g.con,g.cur)
	parentid=res['id']

	# add/get the ontology name
	res=db_access.DB_ACCESS_FLASK_OntologyNamesTable_AddOntologyName(ontologyname,g.con,g.cur)
	ontologynameid=res['id']

	# add the term/parent to the tree structure
	res = db_access.DB_ACCESS_FLASK_OntologyTreeStructureTable_AddByName(term,parent,ontologyname,g.con,g.cur)
	jsonRetData=res

	# add the synonyms
	for csyn in synonyms:
		res=db_access.DB_ACCESS_FLASK_OntologySynonymTable_AddByNameId(cid,csyn,g.con,g.cur)

	return json.dumps(jsonRetData, ensure_ascii=False)


@Ontology_Flask_Obj.route('/ontology/get_parents',methods=['GET'])
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
	term=request.args.get('term')
	if term is None:
		# # TODO: retrun error
		return(return_doc(ontology_get_parents))

	res=db_access.DB_ACCESS_FLASK_OntologyTable_GetRecByName(term,g.con,g.cur)
	if 'id' not in res:
		return json.dumps(res, ensure_ascii=False)
	cid=res['id']
	print(cid)
	plist=[cid]
	parents=[]
	while len(plist)>0:
		cid=plist.pop(0)
		res=db_access.DB_ACCESS_FLASK_OntologyTreeStructureTable_GetOntologyTreeParentsByOntId(cid,g.con,g.cur)
		if 'ontologyParentId' not in res:
			continue
		plist.extend(res['ontologyParentId'])
		for cparent in res['ontologyParentId']:
			res=db_access.DB_ACCESS_FLASK_OntologyTable_GetRecById(cparent,g.con,g.cur)
			parents.append(res['description'])
	print(parents)
	return json.dumps(parents, ensure_ascii=False)


@Ontology_Flask_Obj.route('/ontology/get_term',methods=['GET'])
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
	cid=request.args.get('startid')
	if cid is None:
		return(return_doc(ontology_get_term))
	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTable_GetRecsByStartId(cid,con=g.con,cur=g.cur)
	return json.dumps(jsonRetData, ensure_ascii=False)


@Ontology_Flask_Obj.route('/ontology/get_synonym',methods=['GET'])
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
	cid=request.args.get('startid')
	if cid is None:
		return(return_doc(ontology_get_synonym))
	jsonRetData = db_access.DB_ACCESS_FLASK_SynonymTable_GetRecsByStartId(cid,g.con,g.cur)
	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/AddOntology/ontName=<name>')
# def AddOntology(name):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTable_AddOntology(name,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologyIDs/fromId=<id>')
# def GetOntologyRangeById(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTable_GetRecsByStartId(id,con=g.con,cur=g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologyName/ontName=<name>')
# def GetOntologyByName(name):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTable_GetRecByName(name,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologyID/ontId=<id>')
# def GetOntologyById(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTable_GetRecById(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)

# #Ontology Name


# @Ontology_Flask_Obj.route('/AddOntologyName/ontName=<name>')
# def AddOntologyName(name):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyNamesTable_AddOntologyName(name,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologyNameIDs/fromId=<id>')
# def GetOntologyNameRangeById(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyNamesTable_GetRecsByStartId(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologyNameName/ontNameName=<name>')
# def GetOntologyNameByName(name):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyNamesTable_GetRecByName(name,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologyNameID/ontNameId=<id>')
# def GetOntologyNameById(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyNamesTable_GetRecById(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# #Synonym

# @Ontology_Flask_Obj.route('/AddSynonym/synName=<name>')
# def AddSynonym(name):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_SynonymTable_AddSynonym(name,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QuerySynonymIDs/fromId=<id>')
# def GetSynonymRangeById(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_SynonymTable_GetRecsByStartId(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QuerySynonymName/synName=<name>')
# def GetSynonymByName(name):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_SynonymTable_GetRecByName(name,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QuerySynonymID/synId=<id>')
# def GetSynonymById(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_SynonymTable_GetRecById(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# #Ontology Synonym Table

# @Ontology_Flask_Obj.route('/AddOntologySynonymById/ontId=<oId>&synId=<sId>')
# def AddOntologySynonymById(oId,sId):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologySynonymTable_AddById(oId,sId,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/AddOntologySynonymByName/ontName=<oName>&synName=<sName>')
# def AddOntologySynonymByName(oName,sName):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologySynonymTable_AddByName(oName,sName,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologySynonymIDs/fromId=<id>')
# def GetOntologySynonymRangeById(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologySynonymTable_GetRecsByStartId(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologySynonymSynId/synId=<id>')
# def GetOntologySynonymBySynId(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologySynonymTable_GetRecBySynId(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologySynonymOntId/ontId=<id>')
# def GetOntologySynonymByOntId(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologySynonymTable_GetRecByOntId(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)

# #Ontology Tree Table


# @Ontology_Flask_Obj.route('/AddOntologyTreeStructureById/ontId=<oId>&parentId=<pId>&ontNameId=<ontNameId>')
# def AddOntologyStructureById(oId,pId,ontNameId):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTreeStructureTable_AddById(oId,pId,ontNameId,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/AddOntologyTreeStructureByName/ontName=<oName>&parentName=<pName>&ontNameName=<oNameName>')
# def AddOntologyStructureByName(oName,pName,oNameName):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTreeStructureTable_AddByName(oName,pName,oNameName,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologyTreeIDs/fromId=<id>')
# def GetOntologyTreeRangeById(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTreeStructureTable_GetRecsByStartId(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)


# @Ontology_Flask_Obj.route('/QueryOntologyParents/ontId=<id>')
# def GetOntologyTreeParentsByOntId(id):
# 	jsonRetData = db_access.DB_ACCESS_FLASK_OntologyTreeStructureTable_GetOntologyTreeParentsByOntId(id,g.con,g.cur)
# 	return json.dumps(jsonRetData, ensure_ascii=False)
