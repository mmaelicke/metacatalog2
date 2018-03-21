from flask import request, jsonify

from metacatalog2.api import api
from metacatalog2.models import Page
from metacatalog2.api.views.page import invoke_context
from metacatalog2.util.geohash import decode


@api.route('/<string:context>/pages/geohash', methods=['GET'])
@api.route('/pages/geohash', defaults={'context': None}, methods=['GET'])
def get_pages_geohash(context):
    """
    Return all

    :param context:
    :return:
    """
    if context is None:
        context = invoke_context()

    # get  the precision or set to 7 on default. this is about 150m by 150m
    precision = request.args.get('precision', 7)

    # get the pages
    hashlist = Page.all_coordinates(precision=precision, index=context)

    return jsonify(dict(
        points=[dict(count=h['doc_count'], coordinates=decode(h['key'])) for h in hashlist]
    ))
