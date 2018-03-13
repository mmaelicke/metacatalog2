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

    :param id: str, the unique ID of the requested Context
    :return: the Context as JSON
    """
    ctx = Context.get(id)
    return jsonify(ctx.to_json())


@api.route('/context',defaults={'id': None}, methods=['PUT'])
@api.route('/context/<int:id>', methods=['PUT'])
def new_context(id):
    """
    Inset a new Context object. If it does not exist as index, the index will be
    created. If a definition is present, this definition will be used.

    Parameter
    ---------
    :param id: str, the unique ID of the requested Context
    :return: the newly created Context as JSON
    """
    # get the JSON request
    context_dict = request.json
    if id is not None:
        context_dict['meta'] = dict(id=str(id))

    # build the context
    new_context = Context(**context_dict)

    # create the index
    definition_name=request.args.get('definition', 'page')

    if not request.args.get('suppress_index', False):
        idx = new_context.create_index(definition_name=definition_name)

    # save the context
    new_context.save()

    # return the document
    return jsonify(new_context.to_json())


@api.route('/context/<string:id>', methods=['POST'])
def edit_context(id):
    """
    Edit an existing Context.
    All contents of the part_of property will be re-aliased, but the index will NOT be reindexed, yet.

    Note: the old index will NOT be reindexed. This has to be done externally.

    :param id: str, the unique ID of the requested Context
    :return: the edited Context as JSON
    """
    # get the object
    ctx = Context.get(id)
    print('Context:', ctx)
    # get the old name to extract the index name
    old_name = ctx.name
    new_name = request.json.get('name', old_name)
    print('Name  old: %s  new: %s' % (old_name, new_name))
    if not old_name==new_name:
        return jsonify(dict(
            error=dict(
                message='The name field cannot be updated at the current stage.',
                status=405
            )
        ))
    else:
        ctx.update(**request.json)
        print('updated')
        # re-alias
        ctx.realias()
        print('realiased')

    # return the changed document
    return jsonify(ctx.to_json())


@api.route('/context/<string:id>', methods=['DELETE'])
def delete_context(id):
    """
    Delete the requested context object.
    This WILL delete the index, but any alias of the same name.

    :param id: str, the unique ID of the requested Context
    :return: aknowledge message as JSON
    """
    # get the object
    ctx = Context.get(id)
    ctx.delete(delete_index=request.args.get('delete_index', True))

    return jsonify(dict(
        acknowleged=True,
        message='context of ID=%s was deleted.' % id
    ))