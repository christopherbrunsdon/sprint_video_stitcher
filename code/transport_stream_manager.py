import subprocess

from moviepy.editor import *


class TransportStreamManager:

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.dir_ts = os.path.join(self.config_manager.dir, "ts/")
        self.setup_path()

    def setup_path(self):
        # Create subdirectory "ts" if not exists and then check .ts files.
        if not os.path.exists(self.dir_ts):
            os.makedirs(self.dir_ts)

    def convert(self, input_file, output_file):
        command = f"ffmpeg -i '{input_file}' -c copy -bsf:v h264_mp4toannexb -f mpegts '{output_file}'"
        subprocess.run(command, shell=True, check=True)

    def get_file_path(self, video):
        file_path = self._get_file_path(video)
        filename_without_ext = os.path.splitext(os.path.basename(file_path))[0]
        ts_file_path = os.path.join(self.dir_ts, filename_without_ext + '.ts')
        return ts_file_path

    def _get_file_path(self, video):
        return os.path.join(self.config_manager.dir, video['video'])
