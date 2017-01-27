from flask import Blueprint
# from flask.ext.login import current_user

from .autodoc import auto


Docs_Flask_Obj = Blueprint('Docs_Flask_Obj', __name__, template_folder='templates')


@Docs_Flask_Obj.route('/docs', methods=['POST', 'GET'])
def docs():
    '''
    The documentation for all the REST API using flask-autodoc
    '''
    return auto.html()


@Docs_Flask_Obj.route('/docs2', methods=['POST', 'GET'])
def docs2():
    '''
    The documentation for all the REST API using flask-autodoc
    '''
    return '%s' % auto.generate()
