import psycopg2
from utils import debug

maxfailedattempt = 3

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
        -3 user is locked
        -4 exception
		user id  >= 0 if the user exist
	"""
    try:
        debug(1,'SELECT id,attemptscounter FROM userstable WHERE username=%s' % user)
        cur.execute('SELECT id,attemptscounter FROM userstable WHERE username=%s' ,[user])
        if cur.rowcount==0:
            debug(3,'user %s was not found in userstable' % [user])
            return 'user %s was not found in userstable' % [user],-1
        else:
            #save the user id
            row = cur.fetchone()
            tempUserId = row[0]
            failAttemptCounter = row[1]
            if failAttemptCounter >= maxfailedattempt:
                #user exist but is currently locked
                debug(5,'user %s is locked after several login attempts' % [user])
                return 'user %s is locked after several login attempts' % [user],-3
            #user exist and not locked , try to log in
            cur.execute('SELECT id FROM userstable WHERE (username=%s and passwordhash = crypt(%s, passwordhash))',[user,password])
            if cur.rowcount==0:
                #increase the failure attempt counter
                failAttemptCounter = failAttemptCounter + 1
                debug(3,'increment failed attempt for user %s , fail attempt = %s' % (user,failAttemptCounter))
                setUserLoginAttempts(con,cur,tempUserId,failAttemptCounter)
                debug(3,'invalid password for user %s' % [user])
                return 'invalid password for user %s' % [user],-2
            else:
                userId = cur.fetchone()[0]
                debug(1,'login succeed for user %s' % [user,userId])
                if failAttemptCounter != 0 :
                    debug(3,'reset failed attempt for user %s' % [userId])
                    setUserLoginAttempts(con,cur,userId,0)
                
    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in GetUserId" % e)
        return "error %s enountered in GetUserId" % e,-4

    return "",userId

def setUserLoginAttempts(con,cur,usrid,val):
    """
	Set user login attempt

	input:
	con,cur : database connection and cursor
	user : user id
    val: number of login attempt

	output:
	"""
    returnVal = 0
    debug(3,'update userstable set attemptscounter=%s WHERE id=%s' % (val,usrid))
    cur.execute('update userstable set attemptscounter=%s WHERE id=%s',[val,usrid])
    con.commit()
    
def getUserLoginAttempts(con,cur,usrid):
    """
	Set user login attempt

	input:
	con,cur : database connection and cursor
	user : user id

	output:
    number of attempts : int
        return the number of failed attempts for a given user
	"""
    returnVal = 0
    cur.execute('SELECT attemptscounter FROM userstable WHERE id=%s',[usrid])
    if cur.rowcount==0:
        debug(6,'cant find user %s' % [user])
        returnVal = 0
    else:
        returnVal = cur.fetchone()[0]
    return returnVal
        
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
        return ""
    except psycopg2.DatabaseError as e:
        debug(7,"error %s enountered in addTempUsers" % e)
        return "error %s enountered in addTempUsers" % e
    
    
    