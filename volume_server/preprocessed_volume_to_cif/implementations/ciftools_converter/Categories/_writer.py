from ciftools.Writer.CategoryDesc import CategoryDesc
from ciftools.Writer.FieldDesc import FieldDesc


class CategoryDesc(CategoryDesc):
    def __init__(self, name: str, fields: list[FieldDesc]):
        self.name = name
        self.fields = fields


