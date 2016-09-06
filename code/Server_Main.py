from flask import Flask,jsonify,g
import json
from FLASK_PACKAGE.Exp_Flask import Exp_Flask_Obj
from FLASK_PACKAGE.Seq_Flask import Seq_Flask_Obj
from FLASK_PACKAGE.Ontology_Flask import Ontology_Flask_Obj
from FLASK_PACKAGE.DB_ACCESS.db_access import connect_db
from FLASK_PACKAGE.DB_ACCESS import db_access

app = Flask(__name__)
app.register_blueprint(Exp_Flask_Obj)
app.register_blueprint(Seq_Flask_Obj)
app.register_blueprint(Ontology_Flask_Obj)


# whenever a new request arrives, connect to the database and store in g.db
@app.before_request
def before_request():
	con,cur=connect_db()
	g.con = con
	g.cur = cur


# and when the request is over, disconnect
@app.teardown_request
def teardown_request(exception):
	g.con.close()

#@app.route('/')
#def index():
#	return "Hello, World!"


#@app.route('/seqstrings/<seq>/<seq2>/', methods=['GET'])
#def seqsetrings(seq,seq2):
	#hs.scdb=hs.supercooldb.dbconnect(hs.scdb)
	#notes=hs.supercooldb.getcurationstrings(hs.scdb,seq)
	#tt=jsonify({'notes':notes})
	#return (seq);
	#return ("temp 1,2");
	#   return(seq + " " + seq2)
	#return("<html><body><center>test1</center></body></html>");



if __name__ == '__main__':
	# need to check for database in a nicer way
	app.run(debug=True)
	# if db_access.PostGresConnect() == 0:
	# 	app.run(debug=True)
	# else:
	# 	print("Failed to load DB")
