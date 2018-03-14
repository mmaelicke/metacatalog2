from flask import render_template, request, Response
import requests

from metacatalog2.main import main
from metacatalog2.elastic import es


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/add')
def add():
    return render_template('add_form.html')


# expose the GET and only the GET elasticsearch endpoint
@main.route('/es/<path:uri>', methods=['GET'])
def elasticsearch(uri):
    """
    send any request on host/es/URI to localhost:9200/URI and fetch the result

    :param uri: The API request to elasticsearch
    :return: the elasticsearch response as JSON
    """
    params = request.query_string.decode()
    full_url = '%s/%s%s' % (
        es.transport.get_connection().host,
        uri,
        '?%s' % params if len(params) > 0 else ''
    )
    print('forwarding to %s' % full_url)

    result = requests.get(full_url)
    return Response(result.content, mimetype='text/plain')