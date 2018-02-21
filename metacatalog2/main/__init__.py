from flask import Blueprint

main = Blueprint('main', __name__)

from metacatalog2.main import views