import dbsequences


def AddAnnotaion(con,cur,expid,annotationtype,annotations,method='',description='',agenttype='',private='n',commit=True,user=None):
	"""
	Add an annotation to the annotation table

	input:
	con,cur : database connection and cursor
	expid : int
		the expid for the experiment for which we add the annotations
		(can be obtained via experiments.GetExperimentId() )
	annotationtype : str
		the annotation type (i.e. "isa","differential")
	annotations : list of tuples (detailtype,ontologyterm) of str
		detailtype is ("higher","lower","all")
		ontologyterm is string which should match the ontologytable terms
	commit : bool (optional)
		True (default) to commit, False to wait with the commit
	user : str or None (optional)
		username of the user creating this annotation or None (default) for anonymous user
	"""
