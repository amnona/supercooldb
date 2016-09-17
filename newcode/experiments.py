from utils import debug
import datetime


def GetExperimentId(con,cur,details,userid=None):
	"""
	Get the id of an experiment matching the details

	input:
	details : list of (dtype,value) of str
		the details specific to the experiment (i.e. ("MD5Exp","0x445A2"))
	userid : int (optional)
		the userid asking the query (for private studies)
	output:
	expids : int
		experimentid if exists
		-1 if not found
		-2 if error encountered
		-3 if more than one match
	"""
	try:
		expids=None
		for (dtype,value) in details:
			dtype=dtype.lower()
			value=value.lower()
			cur.execute('SELECT expId,private,userId from ExperimentsTable where (type,value)=(%s,%s)',[dtype,value])
			cids=set()
			for cres in cur:
				# if private and different user - ignore
				if cres[1]=='y':
					if cres[2]!=userid:
						continue
				cids.add(cres[0])
			if expids is None:
				expids = cids
			else:
				expids=expids.intersection(cids)
			if len(expids)==0:
				debug(2,"No experiments found matching all details")
				return -1
		if len(expids)>1:
			debug(2,"Problem. Found %d experiments matching details" % len(expids))
			return(-3)
		expids=expids.pop()
		debug(2,"found expid %d" % expids)
		return expids
	except:
		debug(7,"GetExperimentID failed")
		return -2


def AddExperimentDetails(con,cur,expid,details,userid,private='n',commit=True):
	"""
	Add details to an existing or new experiment

	input:
	expid : int or None
		if int, add a detail for the expid
		if None, create a new experiment
	details : list of (type,value) of str
		the details specific to the experiment (i.e. ("MD5Exp","0x445A2"))
	userid : int
		the userid which is adding this detail
	commit : bool (optional)
		True (default) to commit, False to skip the commit

	output:
	expid : int
		the expid for which the details were added
		-1 if expid not found
		-2 if error encountered
	"""
# try:
	cdate=datetime.date.today().isoformat()
	if expid is None:
		cur.execute("SELECT nextval('ExperimentsTable_expId_seq')")
		expid=cur.fetchone()[0]
	else:
		# test if expid exists
		if not TestExpIdExists(con,cur,expid):
			debug(5,"expid %d does not exist" % expid)
			return -1
	print(details)
	for ctype,cval in details:
		cur.execute('INSERT INTO ExperimentsTable (expId,type,value,date,userid,private) VALUES(%s,%s,%s,%s,%s,%s)',[expid,ctype,cval,cdate,userid,private])
	if commit:
		con.commit()
	return expid
# except:
	debug(7,"AddExperimentDetails failed")
	return -2


def TestExpIdExists(con,cur,expid,userid=None):
	"""
	test if expid exists in table

	input:
	expid : int
	userid : int (optional)

	output:
	True if exists and not private or (private and userid match), False if does not exist, or error encountered
	"""
# try:
	debug(1,"TestExpIdExists %d userid %s" % (expid,userid))
	cur.execute('SELECT private,userId from ExperimentsTable where expId=%s LIMIT 1',[expid])
	if cur.rowcount==0:
		debug(2,"expid %d does not exist" % expid)
		return False
	res=cur.fetchone()
	# if not private - say it exists
	if res[0]=='n':
		debug(2,"expid %d public - exists" % expid)
		return True
	# if private and same user - say it exists
	if res[1]==userid:
		debug(2,"expid %d private but same user - exists" % expid)
		return True
	# so private and different user - say it does not exist
	debug(2,"expid %d private and different users (created by %d, queried by %s). Say it doesn't exist" % (expid,res[1],userid))
	return False
# except:
	debug(7,"error in TestExpIdExists")
	return False
