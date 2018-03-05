import os

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl import DocType as ElasticDocType

new_elastic = lambda: Elasticsearch(os.environ.get('ELASTIC_NODE', 'http://localhost:9200'))
es = new_elastic()

# build a Search object
search = Search(using=es)


# build a custom DocType class, which is extended by some useful fuctions
class DocType(ElasticDocType):
    @classmethod
    def all(cls, as_hit=False):
        """
        Return all instances of this DocType objects from the index.
        Note: it does by default set the hit return range to 0:total_hits, that might cause some
        traffic for large indices.
        The query is implemented by the `elasticsearch_dsl.Search.execute` method with caching activated.
        Nevertheless, the search object is re-created on every call, therefore I am not sure if the
        hits are actually cached.
        By default, the hits will be converted into the calling clss `cls`, if as_hit is True, they will
        be returned as search hit objects (including the score of 1).

        :return: list, all documents in the index
        :param as_hit: bool, if True the instances will be returned as `elasticsearch_dsl.response.hit.Hit`, else as
                `elasticsearch_dsl.DocType`.
        """
        s = cls.search()

        # overwrite the default result range of 10 hits
        s = s[0:s.count()]

        # execute a empty search on the context document type
        if as_hit:
            return [hit for hit in s.execute()]
        else:
            return cls.mget([hit.meta.id for hit in s.execute()])

    def to_json(self):
        """
        This method does just wrap the to_dict method with :param include_meta: set to True by default.
        Can be used to overwrite the json output by inheriting classes.

        :return: dict of the document
        """
        return self.to_dict(include_meta=True)

