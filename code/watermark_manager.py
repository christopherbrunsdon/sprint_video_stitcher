import io

import numpy as np
import requests
from PIL import Image
from moviepy.editor import *

class WatermarkManager:
    """
    Class responsible for handling watermark_manager-related operations
    """

    def __init__(self, config_manager):
        self.watermark = None
        self.config_manager = config_manager
        self._load()

    def _load(self):
        watermark_url = self.config_manager.watermark.get('url', None)
        watermark_path = self.config_manager.watermark.get('path', None)

        if watermark_url:
            response = requests.get(watermark_url)
            self.watermark = np.array(Image.open(io.BytesIO(response.content)))
        elif watermark_path:
            filepath = os.path.join(self.config_manager.dir, watermark_path)
            self.watermark = imageio.v2.imread(filepath)

    def embed(self, clip):
        if self.watermark is not None:
            position = self.config_manager.watermark.get('position', ("right", "top"))
            height_ratio = self.config_manager.watermark.get('height-ratio', 0.1)

            watermark = ImageClip(self.watermark, duration=clip.duration)
            watermark = watermark.resize(height=int(clip.size[1] * height_ratio))
            watermark = watermark.set_position(pos=position).set_duration(clip.duration)
            clip = CompositeVideoClip([clip, watermark])

        return clip
