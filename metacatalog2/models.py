from datetime import datetime as dt

from elasticsearch_dsl import Text, Object, Date, GeoPoint, GeoShape, Integer
from elasticsearch_dsl import Index
from elasticsearch_dsl.response.hit import Hit
from elasticsearch.exceptions import TransportError
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

    @classmethod
    def by_name(cls, name, strict=True):
        """
        Return an Context instance by name.

        This will filter for a Context exactly matching the name attribute.
        The name is case sensitive. If multiple instances in the index match the exact
        pattern and :param strict: is `True` (default), an Error is raised, else only
        the first instance is returned.

        Parameter
        ---------
        :param name: string, the name of the context
        :param strict: bool, if True a multi-match will cause an exception
        :return: the `metacatalog2.models.Context` of `name`
        """
        s = cls.search().filter('term', name=name)

        # check
        if strict and s.count() > 1:
            raise HTTPError(412, 'There is more than one Context of name "%s" and that\'s bad.' % name)
        elif s.count() == 0:
            raise HTTPError(404, 'A Context of name "%s" could not be found.' % name)
        else:
            return list(s).pop()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.has('v') or self.v is None:
            self.v = 1

    def has(self, key):
        return hasattr(self, key)

    @property
    def index_endpoint(self):
        return es.transport.get_connection().host + '/%s_v%d' % (self.name, self.v)

    @property
    def index_name(self):
        return '%s_v%d' % (self.name, self.v)

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
        index = 'meta'
        doc_type = 'page'
        using = es

    @classmethod
    def from_hit(cls, hit):
        """
        Create a new Page object from a given `elasticsearch_dsl.hit.Hit` from search results.
        Although simple CRUD can be done on the hit, the Page class offers some helpful  methods
        not present in the `Hit`.

        Parameter
        ---------
        :param hit: `elasticsearch_dsl.hit.Hit`, or dict of the same structure.
        :return:  Page, created from the hit
        """
        if isinstance(hit, Hit):
            doc = hit.to_dict()
            meta = hit.meta.to_dict()
        elif isinstance(hit, dict):
            meta = hit['meta']
            del hit['meta']
            doc = hit
        else:
            raise AttributeError('The hit has to be of type Hit or dict, found %s.' % hit.__class__)

        # build the page
        page = cls(**doc)
        page.meta.index = meta['index']
        page.meta.id = meta['id']

        return page

    # ------------------------------
    # Methods
    def to_shapely(self):
        if hasattr(self, 'location'):
            return wkt.loads(self.location)
        else:
            return None

    # customize the CRUD methods
    def save(self, **kwargs):
        # update the edited field
        self.edited = dt.utcnow()

        return super().save(**kwargs)

    @classmethod
    def get(cls, id, using=None, index=None, context=None, strict=False, **kwargs):
        """
        Native get overwrite
        --------------------
        This extends the native `elasticsearch_dsl.DocType.get` method. If the index is not set, a context
        can be passed. Then the `Page` object will be fetched from that index. If context is not of type
        `metacatalog2.models.Context`, but a string, the object will be *searched* at that context and
        the best match will be returned. If strict is `True`, this will raise a HTTPError if more than
        one document is found during search.

        Parameter
        ---------
        :param id:          string, the id of the requested object
        :param using:       `elasticsearch.Elasticsearch` instance to connect to
        :param index:       the index where the object will be fetched from
        :param context:     instead of index, either a context name or context obeject can be used
        :param strict:      raise a HTTPError if more than one hit is found
        :param kwargs:      will be passed to the native `get` method
        :return:            the requested object
        """
        # if a Context is given, us the index for search
        if isinstance(context, Context):
            index = context.index_name
            context = None

        # the exact index is known, use the parent get method
        if context is None:
            try:
                return super().get(id=id, using=using, index=index, **kwargs)
            except TransportError as e:
                if e.status_code != 400:
                    raise
                else:
                    print('TransportError [400], search the meta context for id %s' % id)
                    context = 'meta'

        # only the index is known, search for the object
        if isinstance(context, str):
            results = list(cls.search(index=context).filter('match', _id=id))

            if len(results) > 1 and strict:
                raise HTTPError(409, 'Conflict: Multiple Pages found for id={0} in Context={1}'.format(id, context))
            elif len(results) == 0:
                return None
            else:
                return Page.from_hit(hit=results.pop())

        # raise a 405 if context is of wrong type
        else:
            raise HTTPError(405, 'context must be of instance Context, or a context name as string')

    @classmethod
    def all(cls, index=None, limit=None):
        """
        Return all documents
        --------------------

        Return all instances of this DocType objects from the index.
        Note: it does by default set the hit return range to 0:total_hits, that might cause some
        traffic for large indices.
        The query is implemented by the `elasticsearch_dsl.Search.execute` method with caching activated.
        Nevertheless, the search object is re-created on every call, therefore I am not sure if the
        hits are actually cached.

        Page overwrite
        --------------
        This overwrite of the `metacatalog2.elastic.DocType.all` method always uses the hit objects in the
        response and builds new Page instances from the `Page.from_hit` method. This is needed as the
        Page documents most likely live in different indices and are fetched from an alias.
        Therefore the `mget` method does not work

        Parameters
        ----------
        :param index: The index to be used for searching. Can overwrite the default in inheriting classes.
        :param limit: integer, limit the output, similar to SQL LIMIT.
        :return: list, all documents in the index
        """
        hits = super().all(as_hit=True, index=index, limit=limit)

        # return
        return [cls.from_hit(hit) for hit in hits]

    @classmethod
    def all_coordinates(cls, precision='1m', index=None):
        """
        Use a aggregation to create a geohash grid from all documents with coordinate information.
        The precision defines the aggregation level. The default setting of 1 meter will slow the
        aggregation down for larger bounding boxes, then a coarser precision should be chosen.

        TODO: add a optional bounding box filter to narrow the results down

        :param precision: integer or string, the geohash precision.
        :param index: the index (or alias) that should be used for searching
        :return: JSON of all requested coordiantes
        """
        # get the search object
        s = cls.search()

        # parse the indices
        if index is not None:
            s = s.index()
            s = s.index(index.split(','))

        # aggregate, catch the agg object
        s.aggs.bucket('coordinates', 'geohash_grid', field='coordinates', precision=precision)
        result = s[0:0].execute()

        return result.aggregations.coordinates.buckets



    def create(self, **kwargs):
        # update the created and edited field
        now = dt.utcnow()
        self.edited = now
        self.created = now

        # invoke any content check for validity here

        return super().save(**kwargs)
