from flask import Blueprint,request,g
import json
import dbsequences
from utils import debug,getdoc

Seq_Flask_Obj = Blueprint('Seq_Flask_Obj', __name__,template_folder='templates')


@Seq_Flask_Obj.route('/sequences/add',methods=['POST','GET'])
def add_sequences():
	"""
	Title: Add new sequences (or return seqid for ones that exist)
	URL: /sequences/add
	Method: POST
	URL Params:
	Data Params: JSON
		{
			"sequences" : list of str
				the sequences to add (acgt)
			"taxonomies" : list of str (optional)
				the taxonomy per sequence (if not provided, na will be used)
			"ggids" : list of int (optional)
				list of GreenGenes id per sample (if not provided, 0 will be used)
			"primer" : str
				name of the primer region (i.e. 'V4'). if region does not exist, will fail
		}
	Success Response:
		Code : 201
		Content :
		{
			"seqIds" : list of int
				the new sequence id per sequence in the list
		}
	Details:
		Validation:
		Action:
		Add all sequences that don't already exist in SequencesTable
	"""
	cfunc=add_sequences
	if request.method=='GET':
		return(getdoc(cfunc))
	alldat=request.get_json()
	sequences=alldat.get('sequences')
	if sequences is None:
		return(getdoc(cfunc))
	taxonomies=alldat.get('taxonomies')
	ggids=alldat.get('ggids')
	primer=alldat.get('primer')
	if primer is None:
		return(getdoc(cfunc))

	err,seqids=dbsequences.AddSequences(g.con,g.cur,sequences=sequences,taxonomies=taxonomies,ggids=ggids,primer=primer)
	if err:
		return(err,400)
	debug(2,'added/found %d sequences' % len(seqids))
	return json.dumps({"seqIds":seqids})
