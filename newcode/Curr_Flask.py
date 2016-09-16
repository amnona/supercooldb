from flask import Blueprint, render_template, abort
from .DB_ACCESS import *

Curr_Flask_Obj = Blueprint('Curr_Flask_Obj', __name__,
                        template_folder='templates')

@Curr_Flask_Obj.route('/')
def index():
    return ();