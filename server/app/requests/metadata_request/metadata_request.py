from app.requests.metadata_request.i_metadata_request import IMetadataRequest


class MetadataRequest(IMetadataRequest):
    def __init__(self,
                 source: str,
                 structure_id: str,
                 ):
        self._source = source
        self._structure_id = structure_id

    def source(self) -> str:
        return self._source

    def structure_id(self) -> str:
        return self._structure_id


