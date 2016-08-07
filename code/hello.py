from flask import Flask,jsonify
#import sys
#import os
#sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
#import sys
#sys.path.append("Users/admin/supercolldb/Flask/");
#import dbaccess
#import heatsequer as hs
import json
from DB_ACCESS import db_access

app = Flask(__name__)


@app.route('/')
def index():
	return "Hello, World!"


@app.route('/seqstrings/<seq>/<seq2>/', methods=['GET'])
def seqsetrings(seq,seq2):
	#hs.scdb=hs.supercooldb.dbconnect(hs.scdb)
	#notes=hs.supercooldb.getcurationstrings(hs.scdb,seq)
	#tt=jsonify({'notes':notes})
	#return (seq);
    #return ("temp 1,2");
    return(seq + " " + seq2)
    #return("<html><body><center>test1</center></body></html>");



if __name__ == '__main__':
	app.run(debug=True)