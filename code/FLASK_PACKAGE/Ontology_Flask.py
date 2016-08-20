from flask import Blueprint, render_template, abort
from .DB_ACCESS import db_access
import json;

Ontology_Flask_Obj = Blueprint('Ontology_Flask_Obj', __name__,
                        template_folder='templates')

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
