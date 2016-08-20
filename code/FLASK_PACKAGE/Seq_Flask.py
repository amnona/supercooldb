from flask import Blueprint, render_template, abort
from .DB_ACCESS import db_access
import json;

Seq_Flask_Obj = Blueprint('Seq_Flask_Obj', __name__,
                        template_folder='templates')

@Seq_Flask_Obj.route('/QuerySeq/seq=<seq>&region=<region>')
def QuerySeq(seq,region):
    return db_access.DB_ACCESS_SequencesTable_GetSequence(seq,region);

@Seq_Flask_Obj.route('/QuerySeq/seq=<seq>')
def QuerySeqWithDefaultRegion(seq):
     return db_access.DB_ACCESS_SequencesTable_GetSequence(seq,'V4');
