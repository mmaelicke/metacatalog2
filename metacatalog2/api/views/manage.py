from flask import jsonify

from metacatalog2.api import api
from metacatalog2.api.views.page import invoke_context
from metacatalog2.models import Page


@api.route('/variables', defaults={'context': None}, methods=['GET'])
@api.route('/<string:context>/variables', methods=['GET'])
def get_all_variables(context):
    """
    Return all unique variables on the current index.
    This performs a terms aggregation on the variables, therefore aggregations on smaller indices will
    perform better.

    Parameter
    ---------
    :param context: the context which shall be used
    :return: JSON of the aggregation result.
    """
    # get the context
    if context is None:
        context = invoke_context()

    # get the variables
    variables = Page.variables(index=context)

    return jsonify(
        [dict(variable=v['key'], count=v['doc_count']) for v in variables]
    )

