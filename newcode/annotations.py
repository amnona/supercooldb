import dbsequences
import experiments
import dbidval
from utils import debug
import datetime


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
	res : int
		1 if ok, -1 if error encouneted
	"""
	# add the sequences
	err,seqids=dbsequences.AddSequences(con,cur,sequences,primer=primer,commit=False)
	if err:
		return err,-1
	annotationid=AddAnnotation(con,cur,expid,annotationtype,annotationdetails,method,description,agenttype,private,userid,commit=False)
	if annotationid<0:
		return -1
	for cseqid in seqids:
		cur.execute('INSERT INTO SequencesAnnotationTable (seqId,annotationId) VALUES (%s,%s)',[cseqid,annotationid])
	return 1


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
	cid : int
		the new curation identifier or <0 if failed
	"""
	# test if experiment exists
	if not experiments.TestExpIdExists(con,cur,expid,userid):
		debug(4,'expid %d does not exists' % expid)
		return -1
	# handle userid
	if userid is None:
		userid=0
		# TODO: add user exists check
	# get annotationtypeid
	annotationtypeid=dbidval.GetIdFromDescription(con,cur,'AnnotationTypesTable',annotationtype)
	if annotationtypeid<0:
		return -1
	# get annotationtypeid
	methodid=dbidval.GetIdFromDescription(con,cur,'MethodTypesTable',method,noneok=True)
	if methodid<0:
		return -1
	# get annotationtypeid
	agenttypeid=dbidval.GetIdFromDescription(con,cur,'AgentTypesTable',agenttype,noneok=True)
	if agenttypeid<0:
		return -1
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
	numadded=AddAnnotationDetails(con,cur,cid,annotationdetails,commit=False)
	if numadded<0:
		debug(3,"failed to add annotation details. aborting")
		return -1
	debug(2,"%d annotationdetails added" % numadded)
	if commit:
		con.commit()
	return cid


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
	numadded : int
		Number of annotations added to the AnnotationListTable or -1 if error
	"""
	try:
		numadded=0
		for (cdetailtype,contologyterm) in annotationdetails:
			cdetailtypeid=dbidval.GetIdFromDescription(con,cur,"AnnotationDetailTypesTable",cdetailtype)
			if cdetailtypeid<0:
				debug(3,"detailtype %s not found" % cdetailtype)
				return -1
			contologytermid=dbidval.GetIdFromDescription(con,cur,"OntologyTable",contologyterm)
			if contologytermid<0:
				debug(3,"ontology term %s not found" % contologyterm)
				return -1
			cur.execute('INSERT INTO AnnotationListTable (idAnnotation,idAnnotationDetail,idOntology) VALUES (%s,%s,%s)',[annotationid,cdetailtypeid,contologytermid])
			numadded+=1
		debug("Added %d annotationlist items" % numadded)
		if commit:
			con.commit()
		return numadded
	except:
		debug(7,"error enountered in AddAnnotationDetails")
		return -2
