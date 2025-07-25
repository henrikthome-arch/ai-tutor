"""
Main blueprint for the admin UI
"""

from flask import Blueprint

bp = Blueprint('main', __name__, template_folder='../../../frontend/templates')

from app.main import routes