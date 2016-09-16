from flask import Blueprint, g, request
import json
from utils import getdoc
import experiments

Exp_Flask_Obj = Blueprint('Exp_Flask_Obj', __name__)


@Exp_Flask_Obj.route('/experiments/add_details',methods=['GET','POST'])
def add_details():
	"""
	Title: Add new experiment detail
	URL: /AddExpDetails/
	Method: POST
	URL Params:
	Data Params:
		{
			"expId" : int
				(expId from ExperimentsTable) or 0 to add a new experiment
			"private" : bool (optional)
					default=False
					whether the experiment should be private or public (default)
					(private from Experiments)
			"details" : list of
			{
				"type" : str
					the detail type (i.e. "pubmedid"/"author"/etc.)
					(description from ExperimentTypesTable linked from ExperimentsIdentifiers)
				"value" : str
					the detail value (i.e. "john smith"/"pmid003344"/etc.)
					(value from ExperimentsIdentifiers)
			}
		}
	Success Response:
		Code : 201
		Content :
		{
			"expId" : int
				the expId for the experiment with the details added
				same as the data expId if it was >0
				or the expId for the new experiment created
		}
	Details:
		Validation:
			if expId>0, make sure the experiment exists
			If the detail already exists for the experiment, update it?
		Action:
			If ExpId=0, get a new unique experimentId (can use the current uniqueid in ExperimentsTable) and add the private field and the userID/Date
			Add entries into ExperimentsTable for all the pairs in the list. For each one, automatically add the userId and date
			Return the new expId for these details
			for each "type"/"value" in the "details" list, if "type" exists in ExperimentTypesTable, get the id and add it to "type" field in ExperimentsIdentifiers table. Otherwise, create it there and get the id and add it to "type" field in ExperimentsIdentifiers.
	"""
	cfunc=add_details
	if request.method=='GET':
		return(getdoc(cfunc))
	alldat=request.get_json()
	expid=alldat.get('expId')
	details=alldat.get('details')
	if details is None:
		return(getdoc(cfunc))
	private=alldat.get('private')
	if private is None:
		private='n'
	# TODO: get userid
	userid=0
	res=experiments.AddExperimentDetails(g.con,g.cur,expid=expid,details=details,userid=userid,private=private,commit=True)
	if res>0:
		return(json.dumps({'expId':res}))
	if res==-1:
		return('expId %d does not exist' % expid,400)
	return("AddExperimentDetails failed",400)


@Exp_Flask_Obj.route('/experiments/get_id',methods=['GET'])
def get_id():
	"""
	Title: Query experiment based on type/value:
	Description: Get IDs of all experiments matching a field/value pair (i.e. "Pubmedid","111222")
	URL: /experimets/get_id
	Method: GET
	URL Params: JSON
		{
			details : list of tuples [type,value] of str where:
				type : str
					the detail type (i.e. "pubmedid"/"author"/etc.)
					(type from ExperimentsTable)
				value : str
					the detail value (i.e. "john smith"/"pmid003344"/etc.)
		}
	Success Response:
		Code : 200
		Content :
		{
			"experiments" : list of
			{
				expid : int
					the expId for an experiment matching the query
			}
		}
	Details :
		Validation:
			If study is private, return only if user is authenticated and created the study. If user not authenticated, do not return it in the list
			If study is not private, return it (no need for authentication)
	"""
	alldat=request.get_json()
	print(alldat)
	details=alldat.get('details')
	if details is None:
		return('no details')
	# TODO: get userid
	userid=0
	cid=experiments.GetExperimentId(g.con,g.cur,details,userid)
	return str(cid)
