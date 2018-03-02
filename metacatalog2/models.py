from elasticsearch_dsl import DocType, Text

from metacatalog2.elastic import es


class Context(DocType):
    name = Text()
    part_of = Text()

    # define the index in the Meta object
    class Meta:
        index = 'mgt'
        doc_type = 'context'
        using = es

    @staticmethod
    def all():
        """
        Return all instances of Context objects from the index.
        If you need an iterator over all instances, use the `Context.iterall` method.

        :return: list, all Context documents in the index
        """
        s = Context.search()

        # overwrite the default result range of 10 hits
        s = s[0:s.count()]

        # execute a empty search on the context document type
        return [hit for hit in s.execute()]

    @staticmethod
    def iterall():
        """
        Return an iterator over all instances.
        If you need all hits as a list, use the `Context.all` method.

        Note: at the current stage, this method will retrieve all documents and iterate over them.
        Thus, there won't be a performance gain. The method is defined for a future implementation of
        a iterator using the elasticsearch pagination.

        :return: iterator over all Context documents in the index
        """
        s = Context.search()

        #overwrite the default result range of 10 hits.
        s = s[0:s.count()]

        for hit in s.execute():
            yield hit

    # customize the save method
    def save(self, **kwargs):
        # do nothing
        return super().save(**kwargs)