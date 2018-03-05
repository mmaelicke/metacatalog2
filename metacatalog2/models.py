from elasticsearch_dsl import Text

from metacatalog2.elastic import es, DocType


class Context(DocType):
    name = Text()
    part_of = Text()

    # define the index in the Meta object
    class Meta:
        index = 'mgt'
        doc_type = 'context'
        using = es

    # customize the save method
    def save(self, **kwargs):
        # do nothing
        return super().save(**kwargs)
