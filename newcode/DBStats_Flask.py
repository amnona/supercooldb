from flask import Blueprint,g
import json
from utils import debug
import dbstats


DBStats_Flask_Obj = Blueprint('DBStats_Flask_Obj', __name__,template_folder='templates')


@Stats_Flask_Obj.route('/stats/stats',methods=['GET'])
def dbdstats():
	"""
	Title: Get statistics about the database
	URL: /stats/stats
	Method: GET
	URL Params:
	Data Params:
	 Success Response:
		Code : 201
		Content :
		stats : dict
		{
			"NumSequences" : int
				number of unique sequences in the sequenceTable (each sequence can appear in multiple annotations)
			"NumAnnotations" : int
				number of unique annotations (each annotation contains many sequences)
			"NumSeqAnnotations" : int
				number of sequence annotations in the sequenceTable

		}
	Details:
	"""
	err,stats=dbstats.GetStats(g.con,g.cur)
	if not err:
		debug(2,'Got statistics')
		return json.dumps({'stats':stats})
	debug(6,"error encountered %s" % err)
	return ("error enountered %s" % err,400)
