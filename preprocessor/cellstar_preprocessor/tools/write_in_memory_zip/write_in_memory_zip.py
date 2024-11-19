import io
from pathlib import Path
import zipfile

from cellstar_db.models import Asset

def write_in_memory_zip(output_path: Path, assets: list[Asset]):
    zip_buffer = io.BytesIO()
    
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        # for file_name, data in [('1.txt', io.BytesIO(b'111')),
        #                         ('2.txt', io.BytesIO(b'222'))]:
        for item in assets:
            # zip_file.writestr(item.filename, data.getvalue())
            zip_file.writestr(item.filename, item.data)

    with open(str(output_path.resolve()), 'wb') as f:
        f.write(zip_buffer.getvalue())
        