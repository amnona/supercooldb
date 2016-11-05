from flask import Blueprint,request,g
from flask.ext.login import login_required
import json
import dbuser
from utils import debug,getdoc

Users_Flask_Obj = Blueprint('Users_Flask_Obj', __name__,template_folder='templates')


@Users_Flask_Obj.route('/users/add_temp_users',methods=['POST','GET'])
def add_temp_users():
	"""
	Title: Add temp users
	URL: users/add_temp_users
	Method: POST
    """
    
	cfunc=add_temp_users
	if request.method=='GET':
		return(getdoc(cfunc))
	alldat=request.get_json()

	err=dbuser.addTempUsers(g.con,g.cur)
	if err:
		return(err,400)
	debug(2,'Added temp user completed successfully')
	return ""

@Users_Flask_Obj.route('/users/add_temp_users2',methods=['POST','GET'])
def add_temp_users2():
	"""
	Title: Add temp users
	URL: users/add_temp_users
	Method: POST
    """
    
	cfunc=add_temp_users2
	if request.method=='GET':
		return(getdoc(cfunc))
	alldat=request.get_json()

	err=dbuser.addTempUsers2(g.con,g.cur)
	if err:
		return(err,400)
	debug(2,'Added temp user completed successfully')
	return ""

@Users_Flask_Obj.route('/users/get_user_id',methods=['POST','GET'])
def get_user_id():
	"""
	Title: Get user id
	URL: users/test_user_login
	Method: POST
    """    
    
	cfunc=get_user_id
	if request.method=='GET':
		return(getdoc(cfunc))
	alldat=request.get_json()
	user=alldat.get('user')
	pwd=alldat.get('pwd')
    
	err,userid=dbuser.GetUserId(g.con,g.cur,user,pwd)
	if err:
	   return(err,400)
	debug(2,err)
	return json.dumps({"user":userid})


@Users_Flask_Obj.route('/users/test_user_login',methods=['POST','GET'])
@login_required
def test_user_login():
	"""
	Title: test user login
	URL: users/test_user_login
	Method: POST
    """    
    
	return "login succeed"



         