from utils import debug
import psycopg2


def GetStats(con,cur):
	"""
	Get statistics about the database
	input:
	con,cur : database connection and cursor

	output:
	errmsg : str
		"" if ok, error msg if error encountered
	stats : json
		containing statistics about the database tables
	"""

	# number of unique sequences
	stats={}
	cur.execute("SELECT reltuples AS approximate_row_count FROM pg_class WHERE relname = 'sequencestable'")
	stats['NumSequences']=cur.fetchone()[0]
	return '',stats
