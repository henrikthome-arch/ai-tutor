"""
API blueprint for the REST API
"""

from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api.v1 import routes