from elasticsearch_dsl import DocType, Text


class Context(DocType):
    name = Text()
    part_of = Text()

    # define the index in the Meta object
    class Meta:
        index = 'mgt'

    # customize the save method
    def save(self, **kwargs):
        # do nothing
        return super().save(**kwargs)