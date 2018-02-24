import os

from .app import app_factory
from .models import Context

# build a flask app from the environment
conf = os.environ.get('FLASK_CONFIG', 'default')
app = app_factory(conf)

# define a custom shell context
@app.shell_context_processor
def make_shell_context():
    return dict(
        app=app,
        Context=Context
    )