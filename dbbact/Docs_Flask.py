from flask import Blueprint
# from flask.ext.login import current_user
from flask.ext.login import login_required
from .autodoc import auto

Docs_Flask_Obj = Blueprint('Docs_Flask_Obj', __name__, template_folder='templates')

# @login_required
@Docs_Flask_Obj.route('/docs', methods=['POST', 'GET'])
def docs():
    '''
    The documentation for all the REST API using flask-autodoc
    '''
    debug(1,g.amnon)
    return auto.html()
