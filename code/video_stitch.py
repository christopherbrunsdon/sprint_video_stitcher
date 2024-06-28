from moviepy.editor import *

from code.table_of_contents_manager import TableOfContentsManager
from code.text_overlay_manager import TextOverlayManager
from code.transport_stream_manager import TransportStreamManager
from code.video_config_manager import VideoConfigManager
from code.watermark_manager import WatermarkManager
from code.youtube_manager import youtube_download


class VideoData:
    def __init__(self, dir, config, subclip_duration=None, output_file=None):
        self.config_manager = VideoConfigManager(dir)
        self.config_manager.load_and_verify_config(config)
        self.watermark_manager = WatermarkManager(self.config_manager)
        self.transport_stream_manager = TransportStreamManager(self.config_manager)
        self.text_overlay_manager = TextOverlayManager(self.config_manager)
        self.table_of_contents_manager = TableOfContentsManager(self.config_manager)

        self.clips = None
        self.videos = self.config_manager.videos
        self.closing_videos = self.config_manager.closing_videos
        self.opening_videos = self.config_manager.opening_videos
        self.sprint = self.config_manager.sprint
        self.project = self.config_manager.project
        self.dir = dir

        self.subclip_duration = subclip_duration
        self.output_file = self.config_manager.output_file
        self.size = None

        self.txt_ticket_fontsize = self.config_manager.txt_ticket_fontsize
        self.fadein = self.config_manager.fadein
        self.fadeout = self.config_manager.fadeout
        # hard coded for now
        self.toc_fade_time = self.config_manager.toc_fade_time

    def run(self):
        self.prepare()
        self.get_max_video_size()
        self.stitch()

    def prepare(self):
        """
        :return:
        """

        for video in self.videos:
            file_path = self.get_file_path(video)
            youtube_download(video.get('youtube-url'), file_path)

            if os.path.isfile(file_path):
                self.transport_stream_manager.convert(file_path, video)
            else:
                print(f"{file_path} does not exists")

    def get_max_video_size(self):
        """
        Calculate max video size
        :param video:
        :return:
        """
        max_width = 0
        max_height = 0

        for video in self.videos:
            clip = self.video_clip(video)
            size = clip.size
            duration = clip.duration
            clip.close()
            print(f"  - Size is {size}")
            max_width = max(max_width, size[0])
            max_height = max(max_height, size[1])
            video['size'] = size
            # We re-assign duration
            video['duration'] = min(video['duration'], duration) if 'duration' in video else duration

        print(f"Max width is {max_width}, Max height is {max_height}")
        self.size = (max_width, max_height)
        self.config_manager.size = self.size

    def video_clip(self, video):
        file_path = self.transport_stream_manager.get_file_path(video)
        clip = VideoFileClip(file_path)

        subclip_start = video.get('start', 0)
        max_duration = video.get('duration')

        subclip_end = None
        if self.subclip_duration is not None:
            subclip_end = subclip_start + self.subclip_duration
        elif max_duration is not None:
            subclip_end = subclip_start + max_duration

        clip = clip.subclip(subclip_start, subclip_end)
        print(f"  - Start time: {subclip_start} seconds")
        print(f"  - End time: {subclip_end} seconds")

        if self.fadein:
            print(f"  - Fadein: {self.fadein} seconds")
            clip = clip.fx(vfx.fadein, self.fadein)

        if self.fadeout:
            print(f"  - Fadeout: {self.fadeout} seconds")
            clip = clip.fx(vfx.fadeout, self.fadeout)

        background_color = video.get('background', False)
        if background_color:
            # Ensure that the background color is not a string, and it has only 3 elements
            assert isinstance(background_color, (list, tuple)) and len(background_color) == 3
            background_color = tuple(map(int, background_color))  # Convert to a tuple of integers

            print(f"  - Rendering a {background_color} bg video with audio")
            audio_clip = clip.audio
            bg_clip = (ColorClip(clip.size, col=background_color)
                       .set_duration(clip.duration)
                       .set_audio(audio_clip)
                       .set_mask(None)
                       .set_ismask(False))
            clip = bg_clip

        if video.get('title', False):
            color = video.get('color', 'white')

            # Create a TextClip
            txt_clip = TextClip(video.get('title'), fontsize=50, color=color)

            # Center it on the screen
            txt_clip = txt_clip.set_position('center').set_duration(clip.duration)

            # Composite the TextClip and the original clip
            clip = CompositeVideoClip([clip, txt_clip])

        return clip

    def composite_video_clip(self, clips, size=None):
        clips = [clip for clip in clips if clip is not None]
        print(f"  - Composite Video: {len(clips)} clips")
        return CompositeVideoClip(clips, size=size if size else self.size) if len(clips) else None

    def prepare_clip(self, video):
        print(f"- Prepared '{video.get('type', 'demo')}' clip for '{video['video']}'")

        clip = self.video_clip(video)
        txt_clip = self.text_overlay_manager.video_text_overlay_clip(video, clip_duration=clip.duration)

        clips = [clip, txt_clip, ]
        return self.composite_video_clip(clips)

    def prepare_clips(self):
        print(f"Preparing clips for {self.project}")

        # Prepare the opening clips
        print(f"Preparing opening clips:")
        self.clips = [self.prepare_clip_with_toc(video) for video in self.opening_videos]

        # Prepare clips for videos where type is not None
        print(f"Preparing middle clips:")
        self.clips.extend([self.prepare_clip(video) for video in self.videos if video.get('type') is None])

        # Prepare the closing clips
        print(f"Preparing closing clips:")
        self.clips.extend([self.prepare_clip(video) for video in self.closing_videos])

    def prepare_clip_with_toc(self, video):
        clip = self.prepare_clip(video)
        toc_clip = None
        if video.get("show toc", False):
            black_clip_length = self.toc_fade_time - 1
            clip_length = clip.duration - self.toc_fade_time

            # Shorten the video length by self.toc_fade_time seconds, then append a self.toc_fade_time -1 second
            # black screen
            audio = clip.audio  # Strip out audio
            clip = clip.subclip(0, clip_length)
            clip = concatenate_videoclips([
                clip.fx(vfx.fadeout, 1).set_audio(audio),
                ColorClip((clip.size), col=(0, 0, 0), duration=black_clip_length)  # .set_audio(audio)
            ])
            clip = clip.set_audio(audio)  # Restore audio

            toc_clip = self.table_of_contents_manager.clip().set_start(clip_length)

        return self.composite_video_clip([clip, toc_clip, ])

    def stitch(self):
        """
        Stitch all the clips into final video
        :return:
        """
        output_file_path = os.path.join(self.dir, self.output_file)

        self.prepare_clips()
        final_clip = self.concatenate_with_chapters()
        final_clip = self.watermark_manager.embed(final_clip)
        final_clip.write_videofile(output_file_path, codec='libx264', audio_codec='aac')

    def concatenate_with_chapters(self):
        start_times = []  # To track start times for each clip
        total_duration = 0  # To track total duration up to current clip
        final_clip = None  # The final output clip

        for clip in self.clips:
            # Append the start time of current clip
            start_times.append(total_duration)
            # Increase total_duration with current clip duration
            total_duration += clip.duration
            # Concatenate the current clip to final clip
            if final_clip is None:
                final_clip = clip
            else:
                final_clip = concatenate_videoclips([final_clip, clip])

        print(f"Total duration: {total_duration}")
        print(f"Total clips: {len(final_clip.clips)}")

        # Print the starting times for each clip
        print("Starting times for each clip in the final video (in seconds):")
        for i, start_time in enumerate(start_times):
            print(f"Chapter {i + 1}: {start_time} sec")

        return final_clip

    def get_file_path(self, video):
        return os.path.join(self.dir, video['video'])
