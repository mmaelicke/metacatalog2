import os

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

new_elastic = lambda: Elasticsearch(os.environ.get('ELASTIC_NODE', 'http://localhost:9200'))
es = new_elastic()

# build a Search object
search = Search(using=es)