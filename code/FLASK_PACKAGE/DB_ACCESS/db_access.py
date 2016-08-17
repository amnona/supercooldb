import psycopg2;
import crypt;
import json;

def tempFunction(expId):
    return "test234";
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

def DB_ACCESS_AgentTypesTable_GetDescription(id):
    return DB_ACCESS_GenGetDescription("AgentTypesTable",id);

def DB_ACCESS_AgentTypesTable_DeleteById(id):
    return DB_ACCESS_GenDeleteRecById("AgentTypesTable",id);

def DB_ACCESS_AgentTypesTable_AddRec(desc):
    return DB_ACCESS_GenAddRec("AgentTypesTable",desc);

def DB_ACCESS_AgentTypesTable_GedId(desc):
    return DB_ACCESS_GenGetId("AgentTypesTable",desc);

################################################################################################################################
#End of AgentTypesTable table functions
################################################################################################################################

################################################################################################################################
#Start of CurationDetailsTypesTable table functions
################################################################################################################################

def DB_ACCESS_CurationDetailsTypesTable_GetDescription(id):
    return DB_ACCESS_GenGetDescription("CurationDetailsTypesTable",id);

def DB_ACCESS_CurationDetailsTypesTable_DeleteById(id):
    return DB_ACCESS_GenDeleteRecById("CurationDetailsTypesTable",id);

def DB_ACCESS_CurationDetailsTypesTable_AddRec(desc):
    return DB_ACCESS_GenAddRec("CurationDetailsTypesTable",desc);

def DB_ACCESS_CurationDetailsTypesTable_GedId(desc):
    return DB_ACCESS_GenGetId("CurationDetailsTypesTable",desc);

################################################################################################################################
#End of CurationDetailsTypesTable table functions
################################################################################################################################

################################################################################################################################
#Start of CurationTypesTable table functions
################################################################################################################################

def DB_ACCESS_CurationTypesTable_GetDescription(id):
    return DB_ACCESS_GenGetDescription("CurationTypesTable",id);

def DB_ACCESS_CurationTypesTable_DeleteById(id):
    return DB_ACCESS_GenDeleteRecById("CurationTypesTable",id);

def DB_ACCESS_CurationTypesTable_AddRec(desc):
    return DB_ACCESS_GenAddRec("CurationTypesTable",desc);

def DB_ACCESS_CurationTypesTable_GedId(desc):
    return DB_ACCESS_GenGetId("CurationTypesTable",desc);

################################################################################################################################
#End of CurationTypesTable table functions
################################################################################################################################

################################################################################################################################
#Start of MethodTypesTable table functions
################################################################################################################################

def DB_ACCESS_MethodTypesTable_GetDescription(id):
    return DB_ACCESS_GenGetDescription("MethodTypesTable",id);

def DB_ACCESS_MethodTypesTable_DeleteById(id):
    return DB_ACCESS_GenDeleteRecById("MethodTypesTable",id);

def DB_ACCESS_MethodTypesTable_AddRec(desc):
    return DB_ACCESS_GenAddRec("MethodTypesTable",desc);

def DB_ACCESS_MethodTypesTable_GedId(desc):
    return DB_ACCESS_GenGetId("MethodTypesTable",desc);

################################################################################################################################
#End of MethodTypesTable table functions
################################################################################################################################

################################################################################################################################
#Start of OntologyNamesTable table functions
################################################################################################################################

def DB_ACCESS_OntologyNamesTable_GetDescription(id):
    return DB_ACCESS_GenGetDescription("OntologyNamesTable",id);

def DB_ACCESS_OntologyNamesTable_DeleteById(id):
    return DB_ACCESS_GenDeleteRecById("OntologyNamesTable",id);

def DB_ACCESS_OntologyNamesTable_AddRec(desc):
    return DB_ACCESS_GenAddRec("OntologyNamesTable",desc);

def DB_ACCESS_OntologyNamesTable_GedId(desc):
    return DB_ACCESS_GenGetId("OntologyNamesTable",desc);

################################################################################################################################
#End of OntologyNamesTable table functions
################################################################################################################################

################################################################################################################################
#Start of OntologyTable table functions
################################################################################################################################

def DB_ACCESS_OntologyTable_GetDescription(id):
    return DB_ACCESS_GenGetDescription("OntologyTable",id);

def DB_ACCESS_OntologyTable_DeleteById(id):
    return DB_ACCESS_GenDeleteRecById("OntologyTable",id);

def DB_ACCESS_OntologyTable_AddRec(desc):
    return DB_ACCESS_GenAddRec("OntologyTable",desc);

def DB_ACCESS_OntologyTable_GedId(desc):
    return DB_ACCESS_GenGetId("OntologyTable",desc);

################################################################################################################################
#End of OntologyTable table functions
################################################################################################################################

################################################################################################################################
#Start of PrimerRegionTypesTable table functions
################################################################################################################################

def DB_ACCESS_PrimerRegionTypesTable_GetDescription(id):
    return DB_ACCESS_GenGetDescription("PrimerRegionTypesTable",id);

def DB_ACCESS_PrimerRegionTypesTable_DeleteById(id):
    return DB_ACCESS_GenDeleteRecById("PrimerRegionTypesTable",id);

def DB_ACCESS_PrimerRegionTypesTable_AddRec(desc):
    return DB_ACCESS_GenAddRec("PrimerRegionTypesTable",desc);

def DB_ACCESS_PrimerRegionTypesTable_GedId(desc):
    return DB_ACCESS_GenGetId("PrimerRegionTypesTable",desc);

################################################################################################################################
#End of PrimerRegionTypesTable table functions
################################################################################################################################


################################################################################################################################
#Start of SynonymTable table functions
################################################################################################################################

def DB_ACCESS_SynonymTable_GetDescription(id):
    return DB_ACCESS_GenGetDescription("SynonymTable",id);

def DB_ACCESS_SynonymTable_DeleteById(id):
    return DB_ACCESS_GenDeleteRecById("SynonymTable",id);

def DB_ACCESS_SynonymTable_AddRec(desc):
    return DB_ACCESS_GenAddRec("SynonymTable",desc);

def DB_ACCESS_SynonymTable_GedId(desc):
    return DB_ACCESS_GenGetId("SynonymTable",desc);

################################################################################################################################
#End of SynonymTable table functions
################################################################################################################################

################################################################################################################################
#Start of CurationListTable table functions
################################################################################################################################

#Delete record 
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_CurationListTable_DeleteRec(idCurationVal,idCurrationDetailVal,idOntologyVal):
    try:
        cur.execute('SELECT "idCuration" from "CurationSchema"."CurationListTable" where ("idCuration" = %s AND "idCurrationDetail" = %s AND "idOntology" = %s )' % (idCurationVal,idCurrationDetailVal,idOntologyVal))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('delete from "CurationSchema"."CurationListTable" where ("idCuration" = %s AND "idCurrationDetail" = %s AND "idOntology" = %s )' % (idCurationVal,idCurrationDetailVal,idOntologyVal))
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

#Add record
# return 1 if succeed
# -1 doesn't exist
# -2 Exception
# -3 already exist
def DB_ACCESS_CurationListTable_AddRec(idCurationVal,idCurrationDetailVal,idOntologyVal):
    try:
        cur.execute('SELECT "idCuration" from "CurationSchema"."CurationListTable" where ("idCuration" = %s AND "idCurrationDetail" = %s AND "idOntology" = %s )' % (idCurationVal,idCurrationDetailVal,idOntologyVal))
        rowCount = cur.rowcount
        if rowCount > 0 : 
            return -3;
        else:
            cur.execute('INSERT INTO "CurationSchema"."CurationListTable" ("idCuration","idCurrationDetail","idOntology") values (%s,%s,%s)' % (idCurationVal,idCurrationDetailVal,idOntologyVal) );
            con.commit()
            return 1;
        
    except psycopg2.DatabaseError as e:
        return -2;
    return;

#Is exist 
# 1 - yes
# 0 - no
#-2 Exception
def DB_ACCESS_CurationListTable_IsExist(idCurationVal,idCurrationDetailVal,idOntologyVal):
    try:
        cur.execute('SELECT "idCuration" from "CurationSchema"."CurationListTable" where ("idCuration" = %s AND "idCurrationDetail" = %s AND "idOntology" = %s )' % (idCurationVal,idCurrationDetailVal,idOntologyVal))
         
        rowCount = cur.rowcount
        if rowCount > 0 : 
            return 1;  #record exist
        else:
            return 0; #record doesnt exist
    except psycopg2.DatabaseError as e:
        return -2;
    return;
    
################################################################################################################################
#End of CurationListTable table functions
################################################################################################################################

################################################################################################################################
#Start of Curations table functions
################################################################################################################################

#Delete record 
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_CurationsTable_DeleteRec(idExpVal,idUserVal,idCurrTypeVal,idMethodVal,dateVal,descriptionVal,agentTypeIdVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."CurationsTable" where ("idExp" = %s AND "idUser" = %s AND "idCurrType" = %s AND "idMethod" = %s AND "addedDate" = %s AND "description" = \'%s\' AND "agentTypeId" = %s )' % (idExpVal,idUserVal,idCurrTypeVal,idMethodVal,dateVal,descriptionVal,agentTypeIdVal))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('delete from "CurationSchema"."CurationsTable" where where ("idExp" = %s AND "idUser" = %s AND "idCurrType" = %s AND "idMethod" = %s AND "addedDate" = %s AND "description" = \'%s\' AND "agentTypeId" = %s )' % (idExpVal,idUserVal,idCurrTypeVal,idMethodVal,dateVal,descriptionVal,agentTypeIdVal))
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

#Delete record 
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_CurationsTable_DeleteRecById(idVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."CurationsTable" where ("id" = %s)' % (idVal))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('delete from "CurationSchema"."CurationsTable" where  ("id" = %s)' % (idVal))
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception    
    
#Add record
# return 1 if succeed
# -1 doesn't exist
# -2 Exception
# -3 already exist
def DB_ACCESS_CurationsTable_AddRec(idExpVal,idUserVal,idCurrTypeVal,idMethodVal,dateVal,descriptionVal,agentTypeIdVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."CurationsTable" where ("idExp" = %s AND "idUser" = %s AND "idCurrType" = %s AND "idMethod" = %s AND "addedDate" = %s AND "description" = \'%s\' AND "agentTypeId" = %s )' % (idExpVal,idUserVal,idCurrTypeVal,idMethodVal,dateVal,descriptionVal,agentTypeIdVal))
        rowCount = cur.rowcount
        if rowCount > 0 : 
            return -3;
        else:
            cur.execute('INSERT INTO "CurationSchema"."CurationsTable" ("idExp","idUser","idCurrType","idMethod","addedDate","description","agentTypeId") values (%s,%s,%s,%s,%s,\'%s\',%s)' % (idExpVal,idUserVal,idCurrTypeVal,idMethodVal,dateVal,descriptionVal,agentTypeIdVal) );
            con.commit()
            return 1;
        
    except psycopg2.DatabaseError as e:
        return -2;
    return;

################################################################################################################################
#End of Curations table functions
################################################################################################################################

################################################################################################################################
#Start of ExperimentsTable table functions
################################################################################################################################

#Delete record 
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_ExperimentsTable_DeleteRec(idExpVal,idUserVal,idCurrTypeVal,idMethodVal,dateVal,descriptionVal,agentTypeIdVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."ExperimentsTable" where ("uniqueId" = %s AND "expId" = %s AND "type" = \'%s\' AND "value" = \'%s\' AND "date" = %s AND "userId" = \'%s\')' % (uniqueIdVal,expIdVal,typeVal,valueVal,dateVal,userIdVal))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('delete from "CurationSchema"."ExperimentsTable" where ("uniqueId" = %s AND "expId" = %s AND "type" = \'%s\' AND "value" = \'%s\' AND "date" = %s AND "userId" = \'%s\')' % (uniqueIdVal,expIdVal,typeVal,valueVal,dateVal,userIdVal))
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

#Delete record by id
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_ExperimentsTable_DeleteRecById(idVal):
    try:
        cur.execute('SELECT "uniqueId" from "CurationSchema"."ExperimentsTable" where ("id" = %s)' % (idVal))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('delete from "CurationSchema"."ExperimentsTable" where  ("uniqueId" = %s)' % (idVal))
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception    
    
#Add record
# return 1 if succeed
# -1 doesn't exist
# -2 Exception
# -3 already exist
def DB_ACCESS_ExperimentsTable_AddRec(uniqueIdVal,expIdVal,typeVal,valueVal,dateVal,userIdVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."ExperimentsTable" where ("uniqueId" = %s AND "expId" = %s AND "type" = \'%s\' AND "value" = \'%s\' AND "date" = %s AND "userId" = \'%s\')' % (uniqueIdVal,expIdVal,typeVal,valueVal,dateVal,userIdVal))
        rowCount = cur.rowcount
        if rowCount > 0 : 
            return -3;
        else:
            cur.execute('INSERT INTO "CurationSchema"."ExperimentsTable" ("uniqueId","expId","type","value","date","userId") values (%s,%s,\'%s\',\'%s\',%s,%s)' % (uniqueIdVal,expIdVal,typeVal,valueVal,dateVal,userIdVal) );
            con.commit()
            return 1;
        
    except psycopg2.DatabaseError as e:
        return -2;
    return;

#Get record
def DB_ACCESS_ExperimentsTable_GetRec(expId):
    jsonRetData = dict()
    jsonRetData["ReturnCode"] = 0
    jsonRetData["ReturnDescription"] = "Succeed"
    try:
        cur.execute('SELECT type,value,"userId","ExperimentTypesTable".description from "CurationSchema"."ExperimentsTable","CurationSchema"."ExperimentsIdentifiers","CurationSchema"."ExperimentTypesTable" where ("expId" = %s and "expId" = "uniqueId" and "CurationSchema"."ExperimentTypesTable".id = "CurationSchema"."ExperimentsTable"."expTypeId" )' % (expId))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            jsonRetData["ReturnCode"] = -1
            jsonRetData["ReturnDescription"] = "Record doesnt exist"
        else:
            row = cur.fetchone()
            jsonRetData["UserId"] = row[2]
            jsonRetData["ExpType"] = row[3]
            jsonRetData.setdefault("Types", [])
            jsonRetData.setdefault("Values", [])
            while row is not None:
                jsonRetData["Types"].append(row[0]);
                jsonRetData["Values"].append(row[1]);
                row = cur.fetchone()
            
    except psycopg2.DatabaseError as e:
        jsonRetData["ReturnCode"] = -2
        jsonRetData["ReturnDescription"] = "Exception"
    #return;
    return json.dumps(jsonRetData, ensure_ascii=False)

################################################################################################################################
#End of ExperimentsTable table functions
################################################################################################################################

################################################################################################################################
#Start of OntologySynonymTable table functions
################################################################################################################################

#Delete record 
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_OntologySynonymTable_DeleteRec(idOntologyVal,idSynonymVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."OntologySynonymTable" where ("idOntology" = %s AND "idSynonym" = %s)' % (idOntologyVal,idSynonymVal))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('delete from "CurationSchema"."OntologySynonymTable" where ("idOntology" = %s AND "idSynonym" = %s)' % (idOntologyVal,idSynonymVal))
            con.commit()
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)  
        return -2   #DB exception

    
#Add record
# return 1 if succeed
# -1 doesn't exist
# -2 Exception
# -3 already exist
def DB_ACCESS_OntologySynonymTable_AddRec(uniqueIdVal,expIdVal,typeVal,valueVal,dateVal,userIdVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."OntologySynonymTable" where ("idOntology" = %s AND "idSynonym" = %s)' % (idOntologyVal,idSynonymVal))
        rowCount = cur.rowcount
        if rowCount > 0 : 
            return -3;
        else:
            cur.execute('INSERT INTO "CurationSchema"."OntologySynonymTable" ("idOntology","idSynonym") values (%s,%s)' % (idOntologyVal,idSynonymVal) );
            con.commit()
            return 1;
        
    except psycopg2.DatabaseError as e:
        return -2;
    return;

################################################################################################################################
#End of OntologySynonymTable table functions
################################################################################################################################

################################################################################################################################
#Start of OntologyTreeStructureTable table functions
################################################################################################################################

#Delete record 
# 1 - deleted succesfully
#-1 if doesn't exist
#-2 Exception
def DB_ACCESS_OntologyTreeStructureTable_DeleteRec(ontologyIdVal,ontologyParentIdVal,ontologyNameIdVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."OntologyTreeStructureTable" where ("ontologyId" = %s AND "ontologyParentId" = %s AND "ontologyNameId" = %s)' % (ontologyIdVal,ontologyParentIdVal,ontologyNameIdVal))
        rowCount = cur.rowcount
        if rowCount == 0 : 
            return -1;  #username was not found
        else:
            cur.execute('delete from "CurationSchema"."OntologyTreeStructureTable"  where ("ontologyId" = %s AND "ontologyParentId" = %s AND "ontologyNameId" = %s)' % (ontologyIdVal,ontologyParentIdVal,ontologyNameIdVal))
            con.commit();
            return 1;
    except psycopg2.DatabaseError as e:
        print ('Error %s' % e)
        return -2   #DB exception

    
#Add record
# return 1 if succeed
# -1 doesn't exist
# -2 Exception
# -3 already exist
def DB_ACCESS_OntologyTreeStructureTable_AddRec(ontologyIdVal,ontologyParentIdVal,ontologyNameIdVal):
    try:
        cur.execute('SELECT "id" from "CurationSchema"."OntologyTreeStructureTable" where ("ontologyId" = %s AND "ontologyParentId" = %s AND "ontologyNameId" = %s)' % (ontologyIdVal,ontologyParentIdVal,ontologyNameIdVal))
        rowCount = cur.rowcount
        if rowCount > 0 : 
            return -3;
        else:
            cur.execute('INSERT INTO "CurationSchema"."OntologyTreeStructureTable" ("idOntology","ontologyParentId","ontologyNameId") values (%s,%s,%s)' % (ontologyIdVal,ontologyParentIdVal,ontologyNameIdVal) );
            con.commit()
            return 1;
        
    except psycopg2.DatabaseError as e:
        return -2;
    return;

################################################################################################################################
#End of OntologyTreeStructureTable table functions
################################################################################################################################

################################################################################################################################
#Start of SequencesTable functions
################################################################################################################################


def DB_ACCESS_SequencesTable_GetSequence(seq,type):
    jsonRetData = dict()
    jsonRetData["ReturnCode"] = 0
    jsonRetData["ReturnDescription"] = "Succeed"
    try:
        cur.execute('SELECT "CurationSchema"."SequencesTable".sequence from "CurationSchema"."SequencesTable" where ( "CurationSchema"."SequencesTable".sequence = \'%s\'  )' % (seq));
        #return('SELECT "CurationSchema"."SequencesTable".sequence from "CurationSchema"."SequencesTable" where ( "CurationSchema"."SequencesTable".sequence = \'%s\'  )' % (seq));
 #       rowCount = cur.rowcount
  #      if rowCount == 0 : 
   #         jsonRetData["ReturnCode"] = -1
    #        jsonRetData["ReturnDescription"] = "Record doesnt exist"
     #   else:
      #      row = cur.fetchone()
       #     jsonRetData["UserId"] = row[2]
        #    jsonRetData["ExpType"] = row[3]
#            jsonRetData.setdefault("Types", [])
 #           jsonRetData.setdefault("Values", [])
  #          while row is not None:
   #             jsonRetData["Types"].append(row[0]);
    #            jsonRetData["Values"].append(row[1]);
     #           row = cur.fetchone()
            
    except psycopg2.DatabaseError as e:
        jsonRetData["ReturnCode"] = -2
        jsonRetData["ReturnDescription"] = "Exception"
    #return;
    return json.dumps(jsonRetData, ensure_ascii=False)
################################################################################################################################
#End of SequencesTable table functions
################################################################################################################################

#Unit test
PostGresConnect()

#print "test";
#print ( DB_ACCESS_CurationListTable_IsExist(2,3,1));
#print ( DB_ACCESS_CurationListTable_IsExist(2,7,1));
#print ( DB_ACCESS_CurationListTable_AddRec(1,1,1));
print ( DB_ACCESS_CurationListTable_DeleteRec(1,1,1));

#print (DB_ACCESS_GenAddRec("MethodTypesTable","testValue1"));
#print (DB_ACCESS_GenDeleteRecById("MethodTypesTable",5));
                           
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