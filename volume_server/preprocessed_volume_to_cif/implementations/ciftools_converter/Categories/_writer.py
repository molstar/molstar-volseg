from ciftools.writer.base import CategoryDesc, FieldDesc


class CategoryDesc(CategoryDesc):
    def __init__(self, name: str, fields: list[FieldDesc]):
        self.name = name
        self.fields = fields


