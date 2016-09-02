from flask import Blueprint, render_template, abort
from .DB_ACCESS import db_access
import json;

Ontology_Flask_Obj = Blueprint('Ontology_Flask_Obj', __name__,
                        template_folder='templates')

#Ontology

@Ontology_Flask_Obj.route('/AddOntology/ontName=<name>')
def AddOntology(name):
    jsonRetData = db_access.DB_ACCESS_OntologyTable_AddOntology(name);
    return json.dumps(jsonRetData, ensure_ascii=False);

@Ontology_Flask_Obj.route('/QueryOntologyIDs/fromId=<id>')
def GetOntologyRangeById(id):
    jsonRetData = db_access.DB_ACCESS_OntologyTable_GetRecsByStartId(id);
    return json.dumps(jsonRetData, ensure_ascii=False);
    
@Ontology_Flask_Obj.route('/QueryOntologyName/ontName=<name>')
def GetOntologyByName(name):
    jsonRetData = db_access.DB_ACCESS_OntologyTable_GetRecByName(name);
    return json.dumps(jsonRetData, ensure_ascii=False);

@Ontology_Flask_Obj.route('/QueryOntologyID/ontId=<id>')
def GetOntologyById(id):
    jsonRetData = db_access.DB_ACCESS_OntologyTable_GetRecById(id);
    return json.dumps(jsonRetData, ensure_ascii=False);

#Ontology Name

@Ontology_Flask_Obj.route('/AddOntologyName/ontName=<name>')
def AddOntologyName(name):
    jsonRetData = db_access.DB_ACCESS_OntologyNamesTable_AddOntologyName(name);
    return json.dumps(jsonRetData, ensure_ascii=False);

@Ontology_Flask_Obj.route('/QueryOntologyNameIDs/fromId=<id>')
def GetOntologyNameRangeById(id):
    jsonRetData = db_access.DB_ACCESS_OntologyNamesTable_GetRecsByStartId(id);
    return json.dumps(jsonRetData, ensure_ascii=False);
    
@Ontology_Flask_Obj.route('/QueryOntologyNameName/ontNameName=<name>')
def GetOntologyNameByName(name):
    jsonRetData = db_access.DB_ACCESS_OntologyNamesTable_GetRecByName(name);
    return json.dumps(jsonRetData, ensure_ascii=False);

@Ontology_Flask_Obj.route('/QueryOntologyNameID/ontNameId=<id>')
def GetOntologyNameById(id):
    jsonRetData = db_access.DB_ACCESS_OntologyNamesTable_GetRecById(id);
    return json.dumps(jsonRetData, ensure_ascii=False);


#Synonym

@Ontology_Flask_Obj.route('/AddSynonym/synName=<name>')
def AddSynonym(name):
    jsonRetData = db_access.DB_ACCESS_SynonymTable_AddSynonym(name);
    return json.dumps(jsonRetData, ensure_ascii=False);

@Ontology_Flask_Obj.route('/QuerySynonymIDs/fromId=<id>')
def GetSynonymRangeById(id):
    jsonRetData = db_access.DB_ACCESS_SynonymTable_GetRecsByStartId(id);
    return json.dumps(jsonRetData, ensure_ascii=False);
    
@Ontology_Flask_Obj.route('/QuerySynonymName/synName=<name>')
def GetSynonymByName(name):
    jsonRetData = db_access.DB_ACCESS_SynonymTable_GetRecByName(name);
    return json.dumps(jsonRetData, ensure_ascii=False);

@Ontology_Flask_Obj.route('/QuerySynonymID/synId=<id>')
def GetSynonymById(id):
    jsonRetData = db_access.DB_ACCESS_SynonymTable_GetRecById(id);
    return json.dumps(jsonRetData, ensure_ascii=False);


#Ontology Synonym Table

@Ontology_Flask_Obj.route('/QueryOntologySynonymIDs/fromId=<id>')
def GetOntologySynonymRangeById(id):
    jsonRetData = db_access.DB_ACCESS_OntologySynonymTable_GetRecsByStartId(id);
    return json.dumps(jsonRetData, ensure_ascii=False);
    
@Ontology_Flask_Obj.route('/QueryOntologySynonymSynId/synId=<id>')
def GetOntologySynonymBySynId(id):
    jsonRetData = db_access.DB_ACCESS_OntologySynonymTable_GetRecBySynId(id);
    return json.dumps(jsonRetData, ensure_ascii=False);

@Ontology_Flask_Obj.route('/QueryOntologySynonymOntId/ontId=<id>')
def GetOntologySynonymByOntId(id):
    jsonRetData = db_access.DB_ACCESS_OntologySynonymTable_GetRecByOntId(id);
    return json.dumps(jsonRetData, ensure_ascii=False);

#Ontology Tree Table

@Ontology_Flask_Obj.route('/QueryOntologyTreeIDs/fromId=<id>')
def GetOntologyTreeRangeById(id):
    jsonRetData = db_access.DB_ACCESS_OntologyTreeStructureTable_GetRecsByStartId(id);
    return json.dumps(jsonRetData, ensure_ascii=False);

@Ontology_Flask_Obj.route('/QueryOntologyParents/ontId=<id>')
def GetOntologyTreeParentsByOntId(id):
    jsonRetData = db_access.DB_ACCESS_OntologyTreeStructureTable_GetOntologyTreeParentsByOntId(id);
    return json.dumps(jsonRetData, ensure_ascii=False);


