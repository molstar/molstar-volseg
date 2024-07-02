import numpy as np
from cellstar_db.models import NumpyField
from PIL import ImageColor
from pydantic import BaseModel


class PreparedOMETIFFData(BaseModel):
    time: int
    channel_number: int
    data: np.ndarray = NumpyField

    class Config:
        arbitrary_types_allowed = True


def hex_to_rgba_normalized(channel_color_hex):
    channel_color_rgba = ImageColor.getcolor(f"#{channel_color_hex}", "RGBA")
    channel_color_rgba_fractional = tuple([i / 255 for i in channel_color_rgba])
    return channel_color_rgba_fractional
