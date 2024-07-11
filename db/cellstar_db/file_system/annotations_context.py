from uuid import uuid4

from cellstar_db.file_system.constants import ANNOTATION_METADATA_FILENAME
from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    SegmentAnnotationData,
)
from cellstar_db.protocol import VolumeServerDB
from cellstar_preprocessor.flows.common import save_dict_to_json_file


class AnnnotationsEditContext:
    async def update_annotations_json(self, annotations_json: AnnotationsMetadata):
        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(
            annotations_json.model_dump(), ANNOTATION_METADATA_FILENAME, path
        )

    async def remove_descriptions(self, ids: list[str]):
        # 1. read annotations.json file using existing read_annotations function to AnnotationsMetadata TypedDict in d variable
        d = await self.db.read_annotations(namespace=self.namespace, key=self.key)
        # 2. for id in ids, if id exists in annotations.description.keys()
        for id in ids:
            if id in d["descriptions"].keys():
                # 3. remove that key from d variable
                del d["descriptions"][id]
        # 4. write d back to annotations.json
        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(d.model_dump(), ANNOTATION_METADATA_FILENAME, path)

    async def add_or_modify_descriptions(self, xs: list[DescriptionData]):
        # 1. read annotations.json file using existing read_annotations function to AnnotationsMetadata TypedDict in d variable
        d = await self.db.read_annotations(namespace=self.namespace, key=self.key)
        # 2. loop over xs:
        for x in xs:
            # 2. if 'id' in x:
            if "id" in x.keys():
                descr_id = str(x["id"])
            else:
                descr_id = str(uuid4())

            if descr_id in d["descriptions"].keys():
                # loop over each field in x except external_references and replace the fields with the same name in d['descriptions'][descr_id]
                for field_name in x.keys():
                    if field_name != "external_references":
                        d["descriptions"][descr_id][field_name] = x[field_name]
                    else:
                        for ref in x["external_references"]:
                            if "id" not in ref:
                                ref["id"] = str(uuid4())

                            # if ref with that id exists
                            if any(
                                r["id"] == ref["id"]
                                for r in d["descriptions"][descr_id][field_name]
                            ):
                                for idx, item in enumerate(
                                    d["descriptions"][descr_id][field_name]
                                ):
                                    if item["id"] == ref["id"]:
                                        # do stuff on item
                                        # NOTE: replacing fields of the reference
                                        for ref_field_name in ref.keys():
                                            item[ref_field_name] = ref[ref_field_name]

                                        # NOTE: replacing the reference item
                                        d["descriptions"][descr_id][field_name][
                                            idx
                                        ] = item

                            # ref with that id does not exist, append
                            else:
                                d["descriptions"][descr_id][field_name].append(ref)

            # id does not exist, add description
            else:
                d["descriptions"][descr_id] = x
        # 4. write d back to annotations.json
        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(d.model_dump(), ANNOTATION_METADATA_FILENAME, path)

    async def remove_segment_annotations(self, ids: list[str]):
        """
        Removes (segment) annotations by annotation ids.
        """
        # 1. read annotations.json file using existing read_annotations function to AnnotationsMetadata TypedDict in d variable
        d = await self.db.read_annotations(namespace=self.namespace, key=self.key)
        # filter annotations list to leave only those which id is not in ids
        old_annotations_list: list[SegmentAnnotationData] = d["segment_annotations"]
        new_annotations_list = list(
            filter(lambda a: a["id"] not in ids, old_annotations_list)
        )
        d["segment_annotations"] = new_annotations_list
        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(d.model_dump(), ANNOTATION_METADATA_FILENAME, path)

    async def add_or_modify_segment_annotations(self, xs: list[SegmentAnnotationData]):
        # 1. read annotations.json file using existing read_annotations function to AnnotationsMetadata TypedDict in d variable
        d = await self.db.read_annotations(namespace=self.namespace, key=self.key)
        # 2. loop over xs:
        for x in xs:
            # 2. if 'id' in x:
            if "id" in x.keys():
                annotation_id = x["id"]
            else:
                annotation_id = str(uuid4())
            # id exists, replacing annotation
            if any(a["id"] == annotation_id for a in d["segment_annotations"]):
                for idx, item in enumerate(d["segment_annotations"]):
                    if item["id"] == annotation_id:
                        # do stuff on item
                        for field_name in x.keys():
                            item[field_name] = x[field_name]

                        d["segment_annotations"][idx] = item

                print(f"Annotation with id {annotation_id} was modified")
            # id does not exist, add annotation
            else:
                d["segment_annotations"].append(x)
                print(f"Annotation with id {annotation_id} was added")

        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(d.model_dump(), ANNOTATION_METADATA_FILENAME, path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # if hasattr(self.store, "close"):
        #     self.store.close()
        # else:
        #     pass
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        # if hasattr(self.store, "aclose"):
        #     await self.store.aclose()
        # if hasattr(self.store, "close"):
        #     self.store.close()
        # else:
        #     pass
        pass

    def __init__(self, db: VolumeServerDB, namespace: str, key: str):
        self.db = db
        self.namespace = namespace
        self.key = key
        self.path = db.path_to_zarr_root_data(namespace=self.namespace, key=self.key)
        assert self.path.exists(), f"Path {self.path} does not exist"
