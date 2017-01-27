from flask import Flask, g
from flask.ext.login import LoginManager, UserMixin, login_required

from .autodoc import auto
from .Seq_Flask import Seq_Flask_Obj
from .Exp_Flask import Exp_Flask_Obj
from .Users_Flask import Users_Flask_Obj
from .Docs_Flask import Docs_Flask_Obj
from .DBStats_Flask import DBStats_Flask_Obj
from .Annotation_Flask import Annotation_Flask_Obj
from .Ontology_Flask import Ontology_Flask_Obj
from .utils import debug, SetDebugLevel
from . import db_access
from . import dbuser

dbDefaultUser = "na"  # anonymos user in case the field is empty
dbDefaultPwd = ""

recentLoginUsers = []

app = Flask(__name__)
app.register_blueprint(Seq_Flask_Obj)
app.register_blueprint(Exp_Flask_Obj)
app.register_blueprint(Annotation_Flask_Obj)
app.register_blueprint(Ontology_Flask_Obj)
app.register_blueprint(DBStats_Flask_Obj)
app.register_blueprint(Users_Flask_Obj)
app.register_blueprint(Docs_Flask_Obj)

auto.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, username, password, userId, isAdmin):
        self.name = username
        self.password = password
        self.user_id = userId
        self.is_admin = isAdmin


# whenever a new request arrives, connect to the database and store in g.db
@app.before_request
def before_request():
    con, cur = db_access.connect_db()
    g.con = con
    g.cur = cur


# and when the request is over, disconnect
@app.teardown_request
def teardown_request(exception):
    g.con.close()


# the following function will be called for every request autentication is required
@login_manager.request_loader
def load_user(request):
    debug(1, '>>>>>>>>>>>load_user login attempt')
    user = None
    alldat = request.get_json()
    if (alldat is not None):
        userName = alldat.get('user')
        password = alldat.get('pwd')
    else:
        userName = None
        password = None
    debug(1, 'username is %s' % userName)

    # use default user name when it was not sent
    if(userName is None and password is None):
        userName = dbDefaultUser  # anonymos user in case the field is empty
        password = dbDefaultPwd

    # check if exist in the recent array first & password didnt change
    # for tempUser in recentLoginUsers:
    #   if( tempUser.name == userName ):
    #       if( tempUser.password == password):
    #           user found, return
    #           debug(1,'user %s already found' % (tempUser.name))
    #           return tempUser
    #       else:
    #           debug(1,'remove user %s since it might that the password was changed' % (tempUser.id))
    #           # user exist but with different password, remove the user and continue login
    #           recentLoginUsers.remove(tempUser)

    # user was not found in the cache memory
    errorMes, userId = dbuser.getUserId(g.con, g.cur, userName, password)
    if userId >= 0:
        debug(1, 'load_user login succeeded userid=%d' % userId)
        errorMes, isadmin = dbuser.isAdmin(g.con, g.cur, userName)
        if isadmin != 1:
            isadmin = 0
        user = User(userName, password, userId, isadmin)
        # add the user to the recent users list
        # for tempUser in recentLoginUsers:
        #   if( tempUser.name == user.name ):
        #       debug(1,'user %s already found' % (user.id))
        # add the user to the list
        # recentLoginUsers.append(user)
    else:
        debug(1, 'user login failed %s' % (errorMes))
        # login failed, so fallback to default user
        errorMes, userId = dbuser.getUserId(g.con, g.cur, dbDefaultUser, dbDefaultPwd)
        isadmin = 0
        if userId >= 0:
            debug(1, 'logged in as default user userid=%d' % userId)
            user = User(dbDefaultUser, dbDefaultPwd, userId, isadmin)
    return user


if __name__ == '__main__':
    SetDebugLevel(0)
    debug(2, 'starting server')
    app.run(debug=True)
