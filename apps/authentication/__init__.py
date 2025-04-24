# -*- encoding: utf-8 -*-


from flask import Blueprint

# blueprint enables sandboxed sessions 
blueprint = Blueprint(
    'authentication_blueprint',
    __name__,
    url_prefix=''
)
