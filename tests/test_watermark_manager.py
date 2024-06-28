import io
import os
import unittest
from unittest.mock import Mock

import requests
from PIL import Image

from code.watermark_manager import WatermarkManager


class TestWatermarkManager(unittest.TestCase):
    def setUp(self):
        self.config_manager = Mock()
        mock_response = Mock()
        # Create mock image and assign to response
        image = Image.new('RGB', (50, 50))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        mock_response.content = img_byte_arr
        #
        self.get_patcher = unittest.mock.patch.object(requests, 'get', return_value=mock_response)
        self.get_patcher.start()
        self.watermark_manager = WatermarkManager(self.config_manager)

    def tearDown(self):  # This method gets called after each test
        self.get_patcher.stop()

    def test_load_watermark_from_path(self):
        pass

    def test_load_watermark_from_url(self):
        pass

    def test_embed_with_watermark(self):
        pass

    def test_embed_without_watermark(self):
        mock_clip = Mock()
        mock_clip.duration = 10
        self.watermark_manager.watermark = None
        result = self.watermark_manager.embed(mock_clip)
        self.assertEqual(result, mock_clip)


if __name__ == '__main__':
    unittest.main()
