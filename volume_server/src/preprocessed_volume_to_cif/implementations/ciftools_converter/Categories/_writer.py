from src.ciftools.ciftools.writer.base import CategoryDesc, FieldDesc


# TODO: rename categoryDesc to CategoryDescBase to be more consistent
class CategoryDescImpl(CategoryDesc):
    def __init__(self, name: str, fields: list[FieldDesc]):
        self.name = name
        self.fields = fields
