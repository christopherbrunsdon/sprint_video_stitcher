import subprocess

from moviepy.editor import *


class StageVideoManager:
    """
    This converts the existing video to mp4 (Again) to resolve recent issue from Zoom Clips where too many frames
    are picked up.
    """

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.dir = self.config_manager.dir
        self.dir_ts = os.path.join(self.dir, "stage/")
        self.setup_path()

    def setup_path(self):
        # Create subdirectory "ts" if not exists and then check .ts files.
        if not os.path.exists(self.dir_ts):
            os.makedirs(self.dir_ts)

    def convert(self, input_filepath, video):
        """
        ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4

        :param input_filepath:
        :param video:
        :return:
        """
        stage_file_path = self.get_file_path(video)
        if not os.path.isfile(stage_file_path):
            command = f"ffmpeg -i '{input_filepath}' -c:v libx264 -c:a aac '{stage_file_path}'"
            subprocess.run(command, shell=True, check=True)
        return stage_file_path

    def get_file_path(self, video):
        file_path = self._get_file_path(video)
        filename_without_ext = os.path.splitext(os.path.basename(file_path))[0]
        stage_file_path = os.path.join(self.dir_ts, filename_without_ext + '.mp4')
        return stage_file_path

    def _get_file_path(self, video):
        return os.path.join(self.dir, video['video'])
