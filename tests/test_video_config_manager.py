import unittest
from code.video_config_manager import VideoConfigManager


class TestVideoConfigManager(unittest.TestCase):
    def test___init__(self):
        manager = VideoConfigManager("/path/to/directory")
        self.assertIsNotNone(manager)
        self.assertEqual(manager.dir, "/path/to/directory")
        self.assertIsNone(manager.sprint)
        self.assertIsNone(manager.project)
        self.assertIsNone(manager.watermark)
        self.assertIsNone(manager.videos)
        self.assertIsNone(manager.output_file)
        self.assertIsNone(manager.opening_videos)
        self.assertIsNone(manager.closing_videos)


if __name__ == '__main__':
    unittest.main()