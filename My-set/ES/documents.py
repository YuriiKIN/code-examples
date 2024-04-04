@registry.register_document
class ProjectDocument(Document):
    technologies = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(fields={'keyword': fields.KeywordField()})
        }
    )
    industries = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(fields={'keyword': fields.KeywordField()})
        }
    )
    user = fields.ObjectField(properties={'id': fields.IntegerField()})

    class Index:
        name = 'projects'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 1}

    class Django:
        model = Project
        fields = [
            'id',
            'title',
            'url',
            'description',
            'notes',
            'is_public',
            'is_original'
        ]
