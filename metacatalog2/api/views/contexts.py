from flask import jsonify, request

from metacatalog2.api import api
from metacatalog2.models import Context


@api.route('/contexts', methods=['GET'])
def get_contexts():
    """
    Return all Context documents from the mgt index.

    :return: json of all documents
    """
    return jsonify([ctx.to_json() for ctx in Context.all()])


@api.route('/context/<string:id>', methods=['GET'])
def get_context(id):
    """
    Return the Context of id.

    :param id:
    :return:
    """
    ctx = Context.get(id)
    return jsonify(ctx.to_json())


@api.route('/context',defaults={'id': None}, methods=['PUT'])
@api.route('/context/<int:id>', methods=['PUT'])
def new_context(id):
    context_dict = request.json
    if id is not None:
        context_dict['meta'] = dict(id=str(id))

    print(context_dict)

    new_context = Context(**context_dict)
    new_context.save()

    # return the document
    return jsonify(new_context.to_json())


@api.route('/context/<string:id>', methods=['POST'])
def edit_context(id):
    # get the object
    ctx = Context.get(id)
    ctx.update(**request.json)

    # return the changed document
    return jsonify(ctx.to_json())


@api.route('/context/<string:id>', methods=['DELETE'])
def delete_context(id):
    # get the object
    ctx = Context.get(id)
    ctx.delete()

    return jsonify(dict(
        acknowleged=True,
        message='context of ID=%s was deleted.' % id
    ))