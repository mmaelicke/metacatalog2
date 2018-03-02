import os

from flask import Flask

from metacatalog2.config import config
from metacatalog2.main import main
from metacatalog2.api import api
from metacatalog2.elastic import es

# load the flask configuration as specified in the environment variables, or use the default
conf = config[os.environ.get('FLASK_CONFIG', 'default')]

# build the basic flask app
app = Flask(__name__)
app.config.from_object(conf)
conf.init_app(app)

# register the blueprints
app.register_blueprint(main)
app.register_blueprint(api, url_prefix='/api')

# define a custom shell context
@app.shell_context_processor
def make_shell_context():
    from metacatalog2.models import Context
    return dict(
        app=app,
        es=es,
        Context=Context
    )

if __name__ == '__main__':
    app.run()
