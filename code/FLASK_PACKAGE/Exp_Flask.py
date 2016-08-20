from flask import Blueprint, render_template, abort
from .DB_ACCESS import db_access
import json;

Exp_Flask_Obj = Blueprint('Exp_Flask_Obj', __name__,
                        template_folder='templates')

@Exp_Flask_Obj.route('/QueryExpID/expid=<exp>')
def GetExpById(exp):
    jsonRetData = db_access.DB_ACCESS_ExperimentsTable_GetRec(exp);
    return json.dumps(jsonRetData, ensure_ascii=False)
    #return DB_ACCESS_ExperimentsTable_GetRec(exp);
    #return "test";
    