import dbsequences
import dbexperiments
import dbidval
from utils import debug
import datetime
import psycopg2
import dbontology


def AddSequenceAnnotations(con,cur,sequences,primer,expid,annotationtype,annotationdetails,method='',description='',agenttype='',private='n',userid=None,commit=True):
	"""
	Add an annotation to the annotation table

	input:
	con,cur : database connection and cursor
	sequences : list of str
		the sequences for which to add the annotation
		if they do not appear in the SequencesTable, they will be added
	primer : str
		the primer region name for the sequences (i.e. 'V4') or None for na
	expid : int
		the expid for the experiment for which we add the annotations
		(can be obtained via experiments.GetExperimentId() )
	annotationtype : str
		the annotation type (i.e. "isa","differential")
	annotationdetails : list of tuples (detailtype,ontologyterm) of str
		detailtype is ("higher","lower","all")
		ontologyterm is string which should match the ontologytable terms
	user : str or None (optional)
		username of the user creating this annotation or None (default) for anonymous user
	commit : bool (optional)
		True (default) to commit, False to wait with the commit

	output:
	err : str
		the error encountered or '' if ok
	res : int
		annotationid if ok, -1 if error encouneted
	"""
	# add the sequences
	err,seqids=dbsequences.AddSequences(con,cur,sequences,primer=primer,commit=False)
	if err:
		return err,-1
	err,annotationid=AddAnnotation(con,cur,expid,annotationtype,annotationdetails,method,description,agenttype,private,userid,commit=False)
	if err:
		return err,-1
	for cseqid in seqids:
		cur.execute('INSERT INTO SequencesAnnotationTable (seqId,annotationId) VALUES (%s,%s)',[cseqid,annotationid])
	debug(2,"Added %d sequence annotations" % len(seqids))
	if commit:
		con.commit()
	return '',annotationid


def AddAnnotation(con,cur,expid,annotationtype,annotationdetails,method='',description='',agenttype='',private='n',userid=None,commit=True):
	"""
	Add an annotation to the annotation table

	input:
	con,cur : database connection and cursor
	expid : int
		the expid for the experiment for which we add the annotations
		(can be obtained via experiments.GetExperimentId() )
	annotationtype : str
		the annotation type (i.e. "isa","differential")
	annotationdetails : list of tuples (detailtype,ontologyterm) of str
		detailtype is ("higher","lower","all")
		ontologyterm is string which should match the ontologytable terms
	user : str or None (optional)
		username of the user creating this annotation or None (default) for anonymous user
	commit : bool (optional)
		True (default) to commit, False to wait with the commit

	output:
	err : str
		the error encountered or '' if ok
	cid : int
		the new curation identifier or <0 if failed
	"""
	# test if experiment exists
	if not dbexperiments.TestExpIdExists(con,cur,expid,userid):
		debug(4,'expid %d does not exists' % expid)
		return 'expid %d does not exist' % expid,-1
	# handle userid
	if userid is None:
		userid=0
		# TODO: add user exists check
	# get annotationtypeid
	annotationtypeid=dbidval.GetIdFromDescription(con,cur,'AnnotationTypesTable',annotationtype)
	if annotationtypeid<0:
		return 'annotation type %s unknown' % annotationtype,-1
	# get annotationtypeid
	methodid=dbidval.GetIdFromDescription(con,cur,'MethodTypesTable',method,noneok=True)
	if methodid<0:
		return 'method %s unknown' % method,-1
	# get annotationtypeid
	agenttypeid=dbidval.GetIdFromDescription(con,cur,'AgentTypesTable',agenttype,noneok=True)
	if agenttypeid<0:
		return 'agenttype %s unknown' % agenttype,-1
	# get the current date
	cdate=datetime.date.today().isoformat()

	if private is None:
		private='n'
	# lowercase the private
	private=private.lower()

	cur.execute('INSERT INTO AnnotationsTable (idExp,idUser,idAnnotationType,idMethod,description,idAgentType,isPrivate,addedDate) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id',[
				expid,userid,annotationtypeid,methodid,description,agenttypeid,private,cdate])
	cid=cur.fetchone()[0]
	debug(2,"added annotation id is %d. adding %d annotationdetails" % (cid,len(annotationdetails)))
	err,numadded=AddAnnotationDetails(con,cur,cid,annotationdetails,commit=False)
	if err:
		debug(3,"failed to add annotation details. aborting")
		return err,-1
	debug(2,"%d annotationdetails added" % numadded)
	if commit:
		con.commit()
	return '',cid


def AddAnnotationDetails(con,cur,annotationid,annotationdetails,commit=True):
	"""
	Add annotationdetails to the AnnotationListTable

	input:
	con,cur
	annotationid : int
		the idAnnotation field
	annotationdetails : list of tuples (detailtype,ontologyterm) of str
		detailtype is ("higher","lower","all")
		ontologyterm is string which should match the ontologytable terms
	commit : bool (optional)
		True (default) to commit, False to not commit to database

	output:
	err : str
		error encountered or '' if ok
	numadded : int
		Number of annotations added to the AnnotationListTable or -1 if error
	"""
	try:
		numadded=0
		print(annotationdetails)
		for (cdetailtype,contologyterm) in annotationdetails:
			cdetailtypeid=dbidval.GetIdFromDescription(con,cur,"AnnotationDetailsTypesTable",cdetailtype)
			if cdetailtypeid<0:
				debug(3,"detailtype %s not found" % cdetailtype)
				return "detailtype %s not found" % cdetailtype,-1
			contologytermid=dbidval.GetIdFromDescription(con,cur,"OntologyTable",contologyterm)
			if contologytermid<0:
				debug(3,"ontology term %s not found" % contologyterm)
				err,contologytermid=dbontology.AddTerm(con,cur,contologyterm,commit=False)
				if err:
					debug(7,'error enountered when adding ontology term %s' % contologyterm)
					return 'ontology term %s not found or added' % contologyterm,-1
				debug(3,'ontology term %s added' % contologyterm)
			cur.execute('INSERT INTO AnnotationListTable (idAnnotation,idAnnotationDetail,idOntology) VALUES (%s,%s,%s)',[annotationid,cdetailtypeid,contologytermid])
			numadded+=1
		debug(1,"Added %d annotationlist items" % numadded)
		if commit:
			con.commit()
		return '',numadded
	except psycopg2.DatabaseError as e:
		debug(7,"error %s enountered in AddAnnotationDetails" % e)
		return e,-2


def GetAnnotationDetails(con,cur,annotationid):
	"""
	Get the annotation details list for annotationid

	input:
	con,cur
	annotationid : int
		the annotationid for which to show the list of ontology terms

	output:
	err: str
		error encountered or '' if ok
	details : list of (str,str) (detail type (i.e. 'higher in'), ontology term (i.e. 'homo sapiens'))
	"""
	details=[]
	debug(1,'get annotationdetails from id %d' % annotationid)
	cur.execute('SELECT * FROM AnnotationListTable WHERE idAnnotation=%s',[annotationid])
	allres=cur.fetchall()
	for res in allres:
		iddetailtype=res['idannotationdetail']
		idontology=res['idontology']
		err,detailtype=dbidval.GetDescriptionFromId(con,cur,'AnnotationDetailsTypesTable',iddetailtype)
		if err:
			return err,[]
		err,ontology=dbidval.GetDescriptionFromId(con,cur,'OntologyTable',idontology)
		debug(1,'ontologyid %d term %s' % (idontology,ontology))
		if err:
			return err,[]
		details.append([detailtype,ontology])
	debug(1,'found %d annotation details' % len(details))
	return '',details


def GetAnnotationsFromID(con,cur,annotationid,userid=0):
	"""
	get annotation details from an annotation id. NOTE: tests

	input:
	con,cur
	annotationid : int
		the annotationid to get
	userid : int
		used to check if to return a private annotation


	output:
	err : str
		the error encountered or '' if ok
	data : dict
		the annotation data. includes:
		'description' : str
		'method' : str
		'agent' : str
		'annotationtype' : str
		'expid' : int
		'userid' : int (the user who added this annotation)
		'date' : str
		'details' : list of (str,str) of type (i.e. 'higher in') and value (i.e. 'homo sapiens')
	"""
	debug(1,'get annotation from id %d' % annotationid)
	cur.execute('SELECT * FROM AnnotationsTable WHERE id=%s',[annotationid])
	if cur.rowcount==0:
		debug(3,'annotationid %d not found' % annotationid)
		return 'Annotationid %d not found',None
	res=cur.fetchone()
	debug(4,res)
	data={}
	data['id']=annotationid
	data['description']=res['description']
	data['private']=res['isprivate']
	err,method=dbidval.GetDescriptionFromId(con,cur,'MethodTypesTable',res['idmethod'])
	if err:
		return err,None
	data['method']=method
	err,agent=dbidval.GetDescriptionFromId(con,cur,'AgentTypesTable',res['idagenttype'])
	if err:
		return err,None
	data['agent']=agent
	err,annotationtype=dbidval.GetDescriptionFromId(con,cur,'AnnotationTypesTable',res['idannotationtype'])
	if err:
		return err,None
	data['annotationtype']=annotationtype
	data['expid']=res['idexp']
	data['userid']=res['iduser']
	data['date']=res['addeddate'].isoformat()

	if res['isprivate']=='y':
		if userid!=data['userid']:
			debug(6,'Trying to view private annotation id %d from different user (orig user %d, current user %d)' % (annotationid,data['userid'],userid))
			return 'Annotation not found',None

	err,details=GetAnnotationDetails(con,cur,annotationid)
	if err:
		return err,None
	data['details']=details
	return '',data


def GetSequenceAnnotations(con,cur,sequence,region=None):
	"""
	Get all annotations for a sequence

	input:
	con,cur :
	sequence : str ('ACGT')
		the sequence to search for in the database
	region : int (optional)
		None to not compare region, or the regionid the sequence is from

	output:
	err : str
		The error encountered or '' if ok
	details: list of dict
		a list of all the info about each annotation (see GetAnnotationsFromID())
	"""
	details=[]
	debug(1,'GetSequenceAnnotations sequence %s' % sequence)
	err,sid=dbsequences.GetSequenceId(con,cur,sequence,region)
	if err:
		debug(6,'Sequence %s not found for GetSequenceAnnotations. error : %s' % (sequence,err))
		return err,None
	if sid==-1:
		debug(6,'Sequence %s not found for GetSequenceAnnotations.' % sequence)
		return '',[]
	debug(1,'sequenceid=%d' % sid)
	cur.execute('SELECT annotationId FROM SequencesAnnotationTable WHERE seqId=%s',[sid])
	if cur.rowcount==0:
		debug(3,'no annotations for sequenceid %s' % sid)
		return '',[]
	res=cur.fetchall()
	for cres in res:
		err,cdetails=GetAnnotationsFromID(con,cur,cres[0])
		if err:
			debug(6,err)
			return err,None
		details.append(cdetails)
	debug(3,'found %d annotations' % len(details))
	return '',details


def GetAnnotationsFromExpId(con,cur,expid,userid):
	"""
	Get annotations about an experiment

	input:
	con,cur
	expid : int
		the experimentid to get annotations for
	userid : int
		the user requesting the info (for private studies/annotations)

	output:
	err : str
		The error encountered or '' if ok
	annotations: list of dict
		a list of all the annotations associated with the experiment
	"""
	debug(1,'GetAnnotationsFromExpId expid=%d' % expid)
	# test if experiment exists and not private
	if not dbexperiments.TestExpIdExists(con,cur,expid,userid):
		debug(3,'experiment %d does not exist' % expid)
		return '',[]
	cur.execute('SELECT id from AnnotationsTable WHERE idExp=%s',[expid])
	res=cur.fetchall()
	debug(1,'found %d annotations for expid %d' % (len(res),expid))
	annotations=[]
	for cres in res:
		err,cannotation=GetAnnotationsFromID(con,cur,cres[0],userid)
		if err:
			debug(3,'error encountered for annotationid %d : %s' % (cres[0],err))
			return err,None
		annotations.append(cannotation)
	return '',annotations