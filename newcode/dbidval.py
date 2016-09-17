from utils import debug


def GetIdFromDescription(con,cur,table,description,noneok=False):
	"""
	Get the id based on a value for a given table

	input:
	con,cur
	table : str
		Name of the table to search
	value : str
		The value to search for
	noneok : bool (optional)
		False (default) fails if value is None, True returns 0 if None encountered

	output:
	cid : int
		the id of the value, -1 if not found, -2 if error
	"""
	try:
		if description is None:
			if noneok:
				return 0
			else:
				return -1
		description=description.lower()
		cur.execute('SELECT id from %s WHERE description=%s LIMIT 1' % (table,'%s'),[description])
		if cur.rowcount==0:
			debug(2,"value %s not found in table %s" % (description,table))
			return -1
		cid=cur.fetchone()[0]
		debug(2,"value %s found in table %s id %d" % (description,table,cid))
		return cid
	except:
		debug(8,"error in GetIdFromValue")
		return -2
