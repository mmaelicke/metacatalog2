from flask import Blueprint

api = Blueprint('api', __name__)

from metacatalog2.api import views