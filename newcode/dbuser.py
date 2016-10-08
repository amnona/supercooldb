import psycopg2
from utils import debug

def GetUserId(con,cur,user,password):
    """
	Get the user id after autontication

	input:
	con,cur : database connection and cursor
	user : user name
    pasword: user password

	output:
	errmsg : str
		"" if ok, error msg if error encountered
	id : int
        -1 if the user doesnt exist
        -2 if the user exist but using wrong password
        -3 exception
		user id  >= 0 if the user exist
	"""
    try:
        debug(1,'SELECT id FROM userstable WHERE username=%s' % user)
        cur.execute('SELECT id FROM userstable WHERE username=%s' ,[user])
        if cur.rowcount==0:
            debug(3,'user %s was not found in userstable' % [user])
            return 'user %s was not found in userstable' % [user],-1
        else:
            #user exist , try to log in
            cur.execute('SELECT id FROM userstable WHERE (username=%s and passwordhash = crypt(%s, passwordhash))',[user,password])
            if cur.rowcount==0:
                debug(3,'invalid password for user %s' % [user])
                return 'invalid password for user %s' % [user],-2
            else:
                userId = cur.fetchone()[0]
                debug(1,'login succeed for user %s' % [user,userId])
    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in GetUserId" % e)
        return "error %s enountered in GetUserId" % e,-3

    return "",userId


def addTempUsers(con,cur):
    
    pwd1 = "ptest1"
    pwd2 = "ptest2"
    pwd3 = "ptest3"
    
    sql1 = "insert into  annotationschematest.userstable (username, passwordhash,name,description,isactive) values ('user1', crypt('puser1', gen_salt('bf')), 'user1 name', 'user1 description' , true)"
    sql2 = "insert into  annotationschematest.userstable (username, passwordhash,name,description,isactive) values ('user2', crypt('puser2', gen_salt('bf')), 'user2 name', 'user2 description' , true)"
    sql3 = "insert into  annotationschematest.userstable (username, passwordhash,name,description,isactive) values ('user3', crypt('puser3', gen_salt('bf')), 'user3 name', 'user3 description' , true)"
    try:
        cur.execute(sql1)
        cur.execute(sql2)
        cur.execute(sql3)
        con.commit()
    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in addTempUsers" % e)
        return "error %s enountered in addTempUsers" % e,'',[]