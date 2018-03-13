from flask import jsonify, request, session
from requests import HTTPError

from metacatalog2.api import api
from metacatalog2.models import Page, Context


def invoke_context():
    """
    Invoke the current context and return the Elasticsearch alias.
    Can be set (and hierachically overwrite):

     1. in the request.args
     2. in the flask session as 'context'
     3. return the global `meta` context

    :return:
    """
    # first option
    if request.args.get('context') is not None:
        return request.args.get('context')

    # second option
    elif session.get('context') is not None:
        return session.get('context')

    # default
    else:
        return 'meta'


@api.route('/pages', defaults={'context': None}, methods=['GET'])
@api.route('/<string:context>/pages', methods=['GET'])
def get_pages(context):
    """
    Return all pages from the current context. The context can be overwritten by request GET argument `context`.
    If no session is registered and no GET argument is set, the global `meta` context will be used.

    :param context: string, name of the context where the documents shall be fetched from
    :return: JSON of all pages
    """
    # set the current search context
    if context is None:
        context  = invoke_context()
        print('invoked context: %s' % context)
    limit = request.args.get('limit', None)
    return jsonify([page.to_json() for page in Page.all(index=context, limit=limit)])


@api.route('/page/<string:id>', defaults={'context': None}, methods=['GET'])
@api.route('/<string:context>/page/<string:id>', methods=['GET'])
def get_page(id, context):
    """
    Return the page of `id` from the current search context. The context can be overwritte by
    request GET arugment `context`.

    :param id: string, id of the requested Page
    :param context: string, name of the context where the document shall be fetched from
    :return: JSON of the requested Page
    """
    if context is None:
        context = invoke_context()
    page = Page.get(id, index=context)
    return jsonify(page.to_json())


@api.route('/page', defaults={'id': None, 'context': None}, methods=['PUT'])
@api.route('/page/<string:id>', defaults={'context': None}, methods=['PUT'])
@api.route('/<string:context>/page', defaults={'id': None}, methods=['PUT'])
@api.route('/<string:context>/page/<string:id>', methods=['PUT'])
def new_page(id, context):
    """
    Create a new Page
    -----------------
    Create a new metadata page in the current context. It is highly recommended NOT to create
    pages at the global context as these pages will always inflate searches.

    Note: if you do not specify the context, where the Page should live, it will be at the global context.
    In case the global context does not allow indexing at global level, an error will be raised.

    Parameters
    ----------
    :param id: string, id of the requested Page
    :param context: string, name of the context where the document shall be indexed
    :return: the newly created page as JSON
    """
    # get the JSON request
    page_dict = request.json
    if id is not None:
        page_dict['meta'] = dict(id=str(id))
    if context is None:
        context = invoke_context()
    try:
        index = Context.by_name(name=context).index_name
    except HTTPError as e:
        return jsonify(dict(error=dict(status=e.errno, message=e.strerror)))
    page_dict['meta']['index'] = index

    # build the page
    page = Page(**page_dict)
    page.create()

    return jsonify(page.to_json())


@api.route('/page/<string:id>', defaults={'context': None}, methods=['POST'])
@api.route('/<string:context>/page/<string:id>', methods=['POST'])
def edit_page(id, context):
    """
    Edit the requested page.

    Any JSON passed to the Request will be passed through to the Page object and
    updated.
    If the context is not passed (either by URL or GET parameter), the Page document will be
    searched for at the global meta context. This works fine, but takes longer than a fetch.

    Parameter
    ---------
    :param id: string, the id identifying the Page
    :param context: string, name of the context where the document lives
    :return: the updated requested Page as JSON
    """
    # get the page and update
    page = Page.get(id, context=context)
    page.update(**request.json)

    # return the JSON
    return jsonify(page.to_json())


@api.route('/page/<string:id>',defaults={'context': None}, methods=['DELETE'])
@api.route('/<string:context>/page/<string:id>', methods=['DELETE'])
def delete_page(id, context):
    """
    Delete the requested Page object.

    Parameter
    ---------
    :param id: string, the id identifying the page
    :param context: string, name of the context where the document lives
    :return: acknowlege message as JSON
    """
    page = Page.get(id, context=context)
    page.delete()

    return jsonify(dict(
        acknowleged=True,
        message='Page of ID=%s was deleted' % (id)
    ))
