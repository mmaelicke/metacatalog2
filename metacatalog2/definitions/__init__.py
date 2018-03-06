import os
import json


#TODO: how to handle the sav? needed anyway?
def get(name, as_dict=True):
    if not name.endswith('.json'):
        name += '.json'
    path = os.path.join(os.path.dirname(__file__), 'default', name)

    # does the definition exist
    if not os.path.exists(path):
        return None

    # return as dict
    elif as_dict:
        with open(path, 'r') as f:
            return json.load(f)

    # return the file content
    else:
        with open(path, 'r') as f:
            return f.read()
