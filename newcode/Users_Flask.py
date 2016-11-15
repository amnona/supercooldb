from flask import Blueprint,request,g
from flask.ext.login import login_required
from flask.ext.login import current_user
import json
import dbuser
from utils import debug,getdoc,send_email

Users_Flask_Obj = Blueprint('Users_Flask_Obj', __name__,template_folder='templates')


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
    
	err,userid=dbuser.getUserId(g.con,g.cur,user,pwd)
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
	
	debug(6,'login succeed. id=%s' % current_user.user_id)
    
	return 'login succeed. id=%s' % current_user.user_id

@Users_Flask_Obj.route('/users/register_user',methods=['POST','GET'])
def register_user():
	"""
    Title: register new user
	URL: /users/register_user
	Method: POST
	URL Params:
	Data Params: JSON
		{
			"sequence" : str
				the sequence to get data about
            'user': str
                user name
            'pwd': str,
                password
            'name': str
                name (optional)
            'description': str
                description (optional)
            'email': str
                email address
            'publish': 'y' or 'n'
                publish user email
		}
	Success Response:
		Code : 201
		Content :
		{
	       "status" : 1
		}
	Details:
		Validation:
		Action:
    """    
	cfunc=register_user
	if request.method=='GET':
		return(getdoc(cfunc))
	alldat=request.get_json()
	if alldat is None:
		return(getdoc(cfunc))
               
	user=alldat.get('user')
	pwd=alldat.get('pwd')
	name=alldat.get('name')
	description=alldat.get('description')
	mail=alldat.get('email')
	publish=alldat.get('publish')
    
	err,retval=dbuser.addUser(g.con,g.cur,user,pwd,name,description,mail,publish)
	if retval <= 0:
		return(err,400)
	debug(2,'Added temp user completed successfully')
	return json.dumps({"status":1})

#user, pwd, recipient, subject, body

@Users_Flask_Obj.route('/users/send_mail_test',methods=['POST','GET'])
def send_mail_test():
	"""
    Title: Send email test
    """
    
	user = "o.eitan@gmail.com"
	password = ""
	recipient = "eitanozel@gmail.com"
	subject = "test2"
	body = "test3"
    
	cfunc=send_mail_test
	if request.method=='GET':
		return(getdoc(cfunc))
	
	debug(3,"send email before");           
	send_email(user,password,recipient,subject,body)
	debug(3,"send email after");    
	return json.dumps({"status":1})

"""
@Users_Flask_Obj.route('/users/add_temp_users',methods=['POST','GET'])
def add_temp_users():
	
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
    
	cfunc=add_temp_users2
	if request.method=='GET':
		return(getdoc(cfunc))
	alldat=request.get_json()

	err=dbuser.addTempUsers2(g.con,g.cur)
	if err:
		return(err,400)
	debug(2,'Added temp user completed successfully')
	return ""
"""
	
	
         