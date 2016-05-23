#!/usr/bin/env python

# amnonscript

"""
restful api test
use:
source activate flask
and from another terminal
curl -i http://localhost:5000/seqstrings/TACGTAGGTGGCAAGCGTTATCCGGAATTATTGGGCGTAAAGCGCGCGTAGGCGGTTTTTTAAGTCTGATGTGAAAGCCCACGGCTCAACCGTGGAGGGTCATTGGAAACTGGAAAACTTGAGTGCAGAAGAGGAAAGTGGAATTCCATG
"""

from flask import Flask,jsonify
import heatsequer as hs
import json

app = Flask(__name__)


@app.route('/')
def index():
	return "Hello, World!"


@app.route('/seqstrings/<seq>', methods=['GET'])
def seqsetrings(seq):
	hs.scdb=hs.supercooldb.dbconnect(hs.scdb)
	notes=hs.supercooldb.getcurationstrings(hs.scdb,seq)
	tt=jsonify({'notes':notes})
	return(tt)



if __name__ == '__main__':
	app.run(debug=True)
