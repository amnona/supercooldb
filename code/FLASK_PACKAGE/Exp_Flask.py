from flask import Blueprint, render_template, abort
from .DB_ACCESS import db_access

Exp_Flask_Obj = Blueprint('Exp_Flask_Obj', __name__,
                        template_folder='templates')

@Exp_Flask_Obj.route('/QueryExpID/expid=<exp>')
def GetExpById(exp):
    return db_access.DB_ACCESS_ExperimentsTable_GetRec(exp);
    #return DB_ACCESS_ExperimentsTable_GetRec(exp);
    #return "test";
    