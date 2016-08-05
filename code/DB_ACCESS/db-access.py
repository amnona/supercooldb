import psycopg2;
import crypt;


################################################################################################################################
#Begining of common functions
################################################################################################################################

# connect to the db
# return 1 if connected successfully
# return 0 if failed to connect
def PostGresConnect():
    try:
        global con 
        con = psycopg2.connect(database='postgres', user='postgres', password='admin123') 
        global cur 
        cur = con.cursor()
        return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return 0;

################################################################################################################################
#End of common functions
################################################################################################################################

################################################################################################################################
#Begining of userstable section
################################################################################################################################

#Return the new user name id
# return the new added user id
# -1 doesn't exist
# -2 Exception
# -3 already exist
def DB_ACCESS_AddUser(userName, password, name, description):
    try:
        dbExist = DB_ACCESS_GetUserId(userName);
        
        if dbExist >= 0 :
            return -3;
        else:
            hashPwd = DB_ACCESS_Hash_Password(password)
            cur.execute('INSERT INTO "CurationSchema"."UsersTable" ("userName", "passwordHash",name,description,"isActive") values (\'%s\', \'%s\', \'%s\', \'%s\' , true)' % (userName,hashPwd,name,description) );
            con.commit()
            return DB_ACCESS_GetUserId(userName)
        
    except psycopg2.DatabaseError as e:
        return -2;
    return;

#Hash the password
def DB_ACCESS_Hash_Password(password):
    ctype = "6" #for sha512 (see man crypt)
    salt = "qwerty"
    insalt = '${}${}$'.format(ctype, salt)
    
    hashPwd = crypt.crypt(password, insalt)
    return hashPwd
    
#Return user name id if exist or 
# 1 correct password
#-1 if doesn't exist
#-2 wrong password
#-3 exception
def DB_ACCESS_UserLogin(userName, password):
    try:
        hashPwd = DB_ACCESS_Hash_Password(password)
        
        cur.execute('SELECT "passwordHash" from "CurationSchema"."UsersTable" where "userName" = \'%s\'' % userName)
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            ver = cur.fetchone()
            if ver[0] == hashPwd :
                return 1;
            else:
                return -2;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -3;
    
#Return user name id if exist or 
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_GetUserId(name):
    try:
        cur.execute('SELECT id from "CurationSchema"."UsersTable" where "userName" = \'%s\'' % name)
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            ver = cur.fetchone()
            return ver[0]; #Return the id
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

#Delete user by id
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_DeleteUserById(id):
    return DB_ACCESS_GenDeleteRecById("UsersTable",id);
    #try:
    #    cur.execute('SELECT id from "CurationSchema"."UsersTable" where "id" = %s' % id)
    #    rowCount = cur.rowcount
    #    if rowCount == 0 : 
    #        return -1;  #username was not found
    #    else:
    #        cur.execute('delete from "CurationSchema"."UsersTable" where "id" = %s' % id)
    #        con.commit();
    #        return 1;
    #except psycopg2.DatabaseError as e:
    #    print ('Error %s' % e)
    #    return -2   #DB exception

#Activate the user (in case we would like to reuse)
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_ActivateUserById(id):
    try:
        cur.execute('SELECT id from "CurationSchema"."UsersTable" where "id" = %s' % id)
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('update "CurationSchema"."UsersTable" set "isActive" = TRUE where "id" = %s' % id)
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

#Deactiveate the user (instead of deleting)
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_DeactivateUserById(id):
    try:
        cur.execute('SELECT id from "CurationSchema"."UsersTable" where "id" = %s' % id)
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('update "CurationSchema"."UsersTable" set "isActive" = FALSE where "id" = %s' % id)
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

#Delete user by id
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_GetUserRecById(id):
    try:
        cur.execute('SELECT id,"userName","name","description","isActive" from "CurationSchema"."UsersTable" where "id" = %s' % id)
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            ver = cur.fetchone()
            #return the record
            return {"id":ver[0],"userName":ver[1],"name":ver[2],"description":ver[3],"isActive":ver[4]}; 
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

################################################################################################################################
#End of users table section
################################################################################################################################


################################################################################################################################
#Start of (id,description) tables functions - we named it IandD tables
################################################################################################################################

#Return the description
#-1 id not exist
#-2 Exception
def DB_ACCESS_GenGetDescription(tableName,id):
    try:
        cur.execute('SELECT description from "CurationSchema"."%s" where "id" = \'%s\'' % (tableName,id))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            ver = cur.fetchone()
            return ver[0]; #Return the description
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

#Return the description
#-1 id not exist
#-2 Exception
def DB_ACCESS_GenGetId(tableName,description):
    try:
        cur.execute('SELECT id from "CurationSchema"."%s" where "description" = \'%s\'' % (tableName,description))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            ver = cur.fetchone()
            return ver[0]; #Return the description
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

    
#Delete record by id
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_GenDeleteRecById(tableName,id):
    try:
        cur.execute('SELECT id from "CurationSchema"."%s" where "id" = %s' % (tableName,id))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('delete from "CurationSchema"."%s" where "id" = %s' % (tableName,id))
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

#Return the new user name id
# return the new added user id
# -1 doesn't exist
# -2 Exception
# -3 already exist
def DB_ACCESS_GenAddRec(tableName, description):
    try:
        dbExist = DB_ACCESS_GenGetId(tableName,description);
        
        if dbExist >= 0 :
            return -3;
        else:
            cur.execute('INSERT INTO "CurationSchema"."%s" (description) values (\'%s\')' % (tableName,description) );
            con.commit()
            return DB_ACCESS_GenGetId(tableName,description)
        
    except psycopg2.DatabaseError as e:
        return -2;
    return;

################################################################################################################################
#End of (id,description) table section
################################################################################################################################

################################################################################################################################
#Start of AgentTypesTable table functions
################################################################################################################################

def DB_ACCESS_AgentTypesTable_GetDescription(id)
    return DB_ACCESS_GenGetDescription("AgentTypesTable",id);

def DB_ACCESS_AgentTypesTable_DeleteById(id)
    return DB_ACCESS_GenDeleteRecById("AgentTypesTable",id);

def DB_ACCESS_AgentTypesTable_AddRec(desc)
    return DB_ACCESS_GenAddRec("AgentTypesTable",desc);

def DB_ACCESS_AgentTypesTable_GedId(desc)
    return DB_ACCESS_GenGetId("AgentTypesTable",desc);

################################################################################################################################
#End of AgentTypesTable table functions
################################################################################################################################

################################################################################################################################
#Start of CurationDetailsTypesTable table functions
################################################################################################################################

def DB_ACCESS_CurationDetailsTypesTable_GetDescription(id)
    return DB_ACCESS_GenGetDescription("CurationDetailsTypesTable",id);

def DB_ACCESS_CurationDetailsTypesTable_DeleteById(id)
    return DB_ACCESS_GenDeleteRecById("CurationDetailsTypesTable",id);

def DB_ACCESS_CurationDetailsTypesTable_AddRec(desc)
    return DB_ACCESS_GenAddRec("CurationDetailsTypesTable",desc);

def DB_ACCESS_CurationDetailsTypesTable_GedId(desc)
    return DB_ACCESS_GenGetId("CurationDetailsTypesTable",desc);

################################################################################################################################
#End of CurationDetailsTypesTable table functions
################################################################################################################################

################################################################################################################################
#Start of CurationTypesTable table functions
################################################################################################################################

def DB_ACCESS_CurationTypesTable_GetDescription(id)
    return DB_ACCESS_GenGetDescription("CurationTypesTable",id);

def DB_ACCESS_CurationTypesTable_DeleteById(id)
    return DB_ACCESS_GenDeleteRecById("CurationTypesTable",id);

def DB_ACCESS_CurationTypesTable_AddRec(desc)
    return DB_ACCESS_GenAddRec("CurationTypesTable",desc);

def DB_ACCESS_CurationTypesTable_GedId(desc)
    return DB_ACCESS_GenGetId("CurationTypesTable",desc);

################################################################################################################################
#End of CurationTypesTable table functions
################################################################################################################################

################################################################################################################################
#Start of MethodTypesTable table functions
################################################################################################################################

def DB_ACCESS_MethodTypesTable_GetDescription(id)
    return DB_ACCESS_GenGetDescription("MethodTypesTable",id);

def DB_ACCESS_MethodTypesTable_DeleteById(id)
    return DB_ACCESS_GenDeleteRecById("MethodTypesTable",id);

def DB_ACCESS_MethodTypesTable_AddRec(desc)
    return DB_ACCESS_GenAddRec("MethodTypesTable",desc);

def DB_ACCESS_MethodTypesTable_GedId(desc)
    return DB_ACCESS_GenGetId("MethodTypesTable",desc);

################################################################################################################################
#End of MethodTypesTable table functions
################################################################################################################################

################################################################################################################################
#Start of OntologyNamesTable table functions
################################################################################################################################

def DB_ACCESS_OntologyNamesTable_GetDescription(id)
    return DB_ACCESS_GenGetDescription("OntologyNamesTable",id);

def DB_ACCESS_OntologyNamesTable_DeleteById(id)
    return DB_ACCESS_GenDeleteRecById("OntologyNamesTable",id);

def DB_ACCESS_OntologyNamesTable_AddRec(desc)
    return DB_ACCESS_GenAddRec("OntologyNamesTable",desc);

def DB_ACCESS_OntologyNamesTable_GedId(desc)
    return DB_ACCESS_GenGetId("OntologyNamesTable",desc);

################################################################################################################################
#End of OntologyNamesTable table functions
################################################################################################################################

################################################################################################################################
#Start of OntologyTable table functions
################################################################################################################################

def DB_ACCESS_OntologyTable_GetDescription(id)
    return DB_ACCESS_GenGetDescription("OntologyTable",id);

def DB_ACCESS_OntologyTable_DeleteById(id)
    return DB_ACCESS_GenDeleteRecById("OntologyTable",id);

def DB_ACCESS_OntologyTable_AddRec(desc)
    return DB_ACCESS_GenAddRec("OntologyTable",desc);

def DB_ACCESS_OntologyTable_GedId(desc)
    return DB_ACCESS_GenGetId("OntologyTable",desc);

################################################################################################################################
#End of OntologyTable table functions
################################################################################################################################

################################################################################################################################
#Start of PrimerRegionTypesTable table functions
################################################################################################################################

def DB_ACCESS_PrimerRegionTypesTable_GetDescription(id)
    return DB_ACCESS_GenGetDescription("PrimerRegionTypesTable",id);

def DB_ACCESS_PrimerRegionTypesTable_DeleteById(id)
    return DB_ACCESS_GenDeleteRecById("PrimerRegionTypesTable",id);

def DB_ACCESS_PrimerRegionTypesTable_AddRec(desc)
    return DB_ACCESS_GenAddRec("PrimerRegionTypesTable",desc);

def DB_ACCESS_PrimerRegionTypesTable_GedId(desc)
    return DB_ACCESS_GenGetId("PrimerRegionTypesTable",desc);

################################################################################################################################
#End of PrimerRegionTypesTable table functions
################################################################################################################################


################################################################################################################################
#Start of SynonymTable table functions
################################################################################################################################

def DB_ACCESS_SynonymTable_GetDescription(id)
    return DB_ACCESS_GenGetDescription("SynonymTable",id);

def DB_ACCESS_SynonymTable_DeleteById(id)
    return DB_ACCESS_GenDeleteRecById("SynonymTable",id);

def DB_ACCESS_SynonymTable_AddRec(desc)
    return DB_ACCESS_GenAddRec("SynonymTable",desc);

def DB_ACCESS_SynonymTable_GedId(desc)
    return DB_ACCESS_GenGetId("SynonymTable",desc);

################################################################################################################################
#End of SynonymTable table functions
################################################################################################################################


#Unit test
PostGresConnect()

#print (DB_ACCESS_GenAddRec("MethodTypesTable","testValue1"));
print (DB_ACCESS_GenDeleteRecById("MethodTypesTable",5));
                           
#print (DB_ACCESS_GetDescription("MethodTypesTable",3));
#print (DB_ACCESS_GetDescription("MethodTypesTable",2));
#DB_ACCESS_DeleteUserById(6);

#print ('user2 ' + str(DB_ACCESS_GetUserId('user1')))
#print ('user2 ' + str(DB_ACCESS_GetUserId('user2')))
#print ('user4 ' + str(DB_ACCESS_GetUserId('user4')))
#print ('user3 ' + str(DB_ACCESS_GetUserId('user3')))

#DB_ACCESS_AddUser('testUserName1', 'testPwd1', 'testName1' , 'testDesc1')
#print (DB_ACCESS_UserLogin('testUserName1', 'testPwd'))
#print (DB_ACCESS_DeleteUserById(5));
#DB_ACCESS_DeactivateUserById(3);
#DB_ACCESS_ActivateUserById(1);
#DB_ACCESS_DeactivateUserById(2);

#print (DB_ACCESS_GetUserRecById(3));