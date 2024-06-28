import os
import yaml


class VideoConfigManager:
    def __init__(self, dir):
        self.dir = dir
        self.sprint = None
        self.project = None
        self.watermark = None
        self.videos = None
        self.output_file = None
        self.opening_videos = None
        self.closing_videos = None
        self.txt_ticket_fontsize = None
        self.fadeout = None
        self.fadein = None
        self.toc_fade_time = 5.0

    def load_and_verify_config(self, config_file):
        """
        Load and verify the configuration.
        :param config_file: The configuration file to read.
        """
        config_dict = self._read_config(config_file)

        self.sprint = self._get_config_value(config_dict, 'Sprint')
        self.project = self._get_config_value(config_dict, 'Project')
        self.watermark = self._get_config_value(config_dict, 'Watermark')
        self.videos = self._get_videos(config_dict)

        self.txt_ticket_fontsize = self._get_config_value(config_dict, 'txt_ticket_fontsize', 22)
        self.fadein = self._get_config_value(config_dict, 'fadein', 1.0)
        self.fadeout = self._get_config_value(config_dict, 'fadeout', 1.0)

        self.output_file = self._generate_output_file_name(config_dict) if not self.output_file else self.output_file
        self.opening_videos = [video for video in self.videos if video.get('type') == 'opening']
        self.closing_videos = [video for video in self.videos if video.get('type') == 'closing']

        if not self._is_config_valid():
            raise Exception("Config file is not valid")

    def _read_config(self, config_file):
        with open(os.path.join(self.dir, config_file), 'r') as ymlfile:
            return yaml.safe_load(ymlfile)

    def _get_config_value(self, config_dict, key, default=None):
        return config_dict.get(key, default)

    def _get_videos(self, config_dict):
        videos = self._get_config_value(config_dict, 'Videos')
        return [video for video in videos if not video.get('skip')]

    def _generate_output_file_name(self, config_dict):
        author = self._get_config_value(config_dict, 'Author', '')
        sprint = self._get_config_value(config_dict, 'Sprint', 'stitched output')
        output = f"{author}-sprint-demo-{sprint}".strip().strip('-').lower()  # Get the value, trim and lower case
        output = output.replace(' ', '-')  # Replace whitespaces with dash
        output += '.mp4'  # Append '.mp4'
        return output

    def _is_config_valid(self):
        validate_sprint = isinstance(self.sprint, str)
        validate_project = isinstance(self.project, str)
        validate_videos = isinstance(self.videos, list)
        validate_opening_and_closing_videos = len(self.opening_videos) == 1 and len(self.closing_videos) == 1
        return validate_sprint and validate_project and validate_videos and validate_opening_and_closing_videos
