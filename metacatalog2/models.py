from datetime import datetime as dt

from elasticsearch_dsl import Text, Object, Date, GeoPoint, GeoShape, Integer
from elasticsearch_dsl import Index
from shapely import wkt
import requests
from requests import HTTPError

from metacatalog2.elastic import es, DocType
from metacatalog2 import definitions


class Context(DocType):
    """
    Basic Context object
    --------------------

    The context represents a hierachical search index structure to allow for indexing each
    project into its own index using a custom document mapping. At the same time the
    search index alias will search over all context making institute, research group or global
    searches possible.
    """
    name = Text()
    part_of = Text(multi=True)
    v = Integer()

    # define the index in the Meta object
    class Meta:
        index = 'index_list_v1'
        doc_type = 'context'
        using = es

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.has('v') or self.v is None:
            self.v = 1

    def has(self, key):
        return hasattr(self, key)

    @property
    def index_endpoint(self):
        return es.transport.get_connection().host + '/%s_v%d' % (self.name, self.v)

    def create_index(self, definition_name='page'):
        """
        Create a new index of this Context object.
        It will load the definition name from the `metacatalog2.definitions` submodule and PUT it
        into elasticsearch as `Context.name + '_v1'.

        Parameter
        ---------
        :param definition_name: string, name of the json file holding the index definition
        :return: `elasticsearch_dsl.Index` object of the created instance
        """
        # build a Index and increment the version
        idx = Index(name='%s_v%d' % (self.name, self.v), using=es)
        while idx.exists():
            self.v += 1
            idx = Index(name='%s_v%d' % (self.name, self.v), using=es)

        mapping = definitions.get(definition_name)
        if mapping is None:
            raise FileNotFoundError('The default mapping could not be found')

        # sent the mapping to elasticsearch
        res = requests.put(es.transport.get_connection().host + '/%s_v1' % self.name, json=mapping)
        if res.status_code != 200:
            raise HTTPError(404, 'The mapping was not accepted by Elasticsearch. %s.' % res.content)

        # create the alias
        self.create_alias(self.name)

        # check parent indices
        if self.has('part_of'):
            [self.create_alias(name=n) for n in self.part_of]

        # save the index
        if not idx.exists():
            print('[DEV]: The index does not exist')
        return idx

    def create_alias(self, name):
        """
        Create an alias to the basic alias of this context.
        Note: This function operates directly on the elasticsearch node as the `elasticsearch_dsl.Index.aliases`
            function seems to work not correctly?

        :param name: string, will be used as alias
        :return: True, if the HTTP Response of Elasticsearch was of status 200
        """
        # create the alias
        res = requests.put(self.index_endpoint + '/_aliases/%s' % name)
        if res.status_code != 200:
            raise HTTPError(res.status_code, res.content)
        else:
            return True

    def realias(self):
        """
        Delete all alias endpoints of this context and recreate from the name and part_of property.

        :return:
        """
        res = requests.delete(self.index_endpoint + '/_aliases/*')
        self.create_alias(self.name)

        # part of
        if self.has('part_of'):
            [self.create_alias(name=n) for n in self.part_of]

    # customize the save method
    def save(self, **kwargs):
        # do nothing
        return super().save(**kwargs)

    # customize the delete method
    def delete(self, using=None, index=None, delete_index=False, **kwargs):
        # delete the index as well
        if delete_index:
            requests.delete(es.transport.get_connection().host + '/%s_v%d' % (self.name, self.v))
        return super().delete(using=using, index=index, **kwargs)


class Page(DocType):
    """
    Main Metadata object
    --------------------

    The Page can be used as the main metadata object in metacatalog. It does describe any kind of
    data source. The Page itself defines the most basic informations that should be available in
    order to satisfy metadata standards like Dublin core or INSPIRE.
    Each project or subproject context can nevertheless either fill the supplementary object or
    inherit Page and extend the structure.
    """
    title = Text()
    identifiers = Text(multi=True)
    description = Text()
    owner = Text()
    license = Text()
    coordinates = GeoPoint()
    location = GeoShape()
    variable = Text()
    supplemetary = Object()
    created = Date()
    edited = Date()
    info = Object(
        downloads=Integer(),
        votes=Integer()
    )

    # define the index in the Meta object
    class Meta:
        # TODO: create the global context
        index = 'caos'
        doc_type = 'page'
        using = es

    # ------------------------------
    # Methods
    def to_shapely(self):
        if hasattr(self, 'location'):
            return wkt.loads(self.location)
        else:
            return None


    # customize the save method
    def save(self, **kwargs):
        # update the edited field
        self.edited = dt.utcnow()

        return super().save(**kwargs)

    def create(self, **kwargs):
        # update the created and edited field
        now = dt.utcnow()
        self.edited = now
        self.created = now

        # invoke any content check for validity here

        return super().save(**kwargs)
