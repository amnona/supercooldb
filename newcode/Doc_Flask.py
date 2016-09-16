from flask import Blueprint
from flask.ext.autodoc import Autodoc


Doc_Flask_Obj = Blueprint('Doc_Flask_Obj', __name__)
auto = Autodoc()


@Doc_Flask_Obj.route('/doc')
def doc():
	print(auto.generate())
	return "amnon"
