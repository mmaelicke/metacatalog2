import os

from flask import Flask
from elasticsearch import Elasticsearch

from metacatalog2.config import config


def app_factory(conf):
    app = Flask(__name__)
    app.config.from_object(config[conf])
    config[conf].init_app(app)

    # blueprints
    from metacatalog2.main import main
    app.register_blueprint(main)

    from metacatalog2.api import api
    app.register_blueprint(api, url_prefix='/api')

    # register a elasticserach factory
    app.new_es = lambda: Elasticsearch(app.config.get('ELASTIC_NODE'))
    app.es = app.new_es()

    return app


if __name__ == '__main__':
    conf = os.environ.get('FLASK_CONFIG', 'default')
    app = app_factory(conf)
    app.run()
