from flask import Blueprint, render_template, abort

Exp_Flask_Obj = Blueprint('Exp_Flask_Obj', __name__,
                        template_folder='templates')

@Exp_Flask_Obj.route('/')
def index():
    return ("test");