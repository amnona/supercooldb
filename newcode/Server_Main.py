from flask import Flask,g
from Seq_Flask import Seq_Flask_Obj
from Exp_Flask import Exp_Flask_Obj
from Annotation_Flask import Annotation_Flask_Obj
from Ontology_Flask import Ontology_Flask_Obj
import db_access


app = Flask(__name__)
app.register_blueprint(Seq_Flask_Obj)
app.register_blueprint(Exp_Flask_Obj)
app.register_blueprint(Annotation_Flask_Obj)
app.register_blueprint(Ontology_Flask_Obj)


# whenever a new request arrives, connect to the database and store in g.db
@app.before_request
def before_request():
	con,cur=db_access.connect_db()
	g.con = con
	g.cur = cur


# and when the request is over, disconnect
@app.teardown_request
def teardown_request(exception):
	g.con.close()


if __name__ == '__main__':
	# need to check for database in a nicer way
	app.run(debug=True)
	# if db_access.PostGresConnect() == 0:
	# 	app.run(debug=True)
	# else:
	# 	print("Failed to load DB")
