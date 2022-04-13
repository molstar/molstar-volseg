from ciftools.writer.fields import string_field

fields = [
    string_field(name="lattice_ids", value=lambda d, i: str(d))
]
