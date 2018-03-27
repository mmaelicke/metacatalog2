from flask import jsonify

from metacatalog2.api import api
from metacatalog2.elastic import es


@api.route('/info')
def info():
    return jsonify({
        'elasticsearch_info': es.info(),
        'cluster_health': es.cat.health()
    })


