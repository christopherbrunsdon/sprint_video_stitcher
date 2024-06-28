import shutil
import ssl

from moviepy.editor import *
from pytube import YouTube

from code.transport_stream_manager import TransportStreamManager
from code.video_config_manager import VideoConfigManager
from code.watermark_manager import WatermarkManager

# Ignore SSL
# Resolves: urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000)>
ssl._create_default_https_context = ssl._create_unverified_context


def my_hook(self, d):
    if d['status'] == 'finished':
        print('Download completed, now converting...')


class VideoData:
    def __init__(self, dir, config, subclip_duration=None, output_file=None):
        self.config_manager = VideoConfigManager(dir)
        self.config_manager.load_and_verify_config(config)
        self.watermark_manager = WatermarkManager(self.config_manager)
        self.transport_stream_manager = TransportStreamManager(self.config_manager)

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

        # hard coded for now
        self.fadein = 1
        self.fadeout = 1
        self.txt_ticket_fontsize = 22
        self.toc_fade_time = 5.0

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
            ts_file_path = self.transport_stream_manager.get_file_path(video)

            # Check if the video is a YouTube URL and we have not downloaded it yet
            youtube_url = video.get('youtube-url')
            if youtube_url and not os.path.isfile(file_path):
                download_path = f"{file_path}-youtube-download"
                yt = YouTube(youtube_url)

                # Get all streams and filter for mp4 files and progressive streams
                progressive_streams = yt.streams.filter(file_extension='mp4', progressive=True)

                # Get the video with the highest resolution
                d_video = progressive_streams.get_highest_resolution()

                # Download the video to the directory of file_path
                filename = d_video.download(output_path=download_path)

                # Rename the file
                os.rename(os.path.join(download_path, filename), file_path)

                # Drop download folder
                shutil.rmtree(download_path)

            if os.path.isfile(file_path):
                if not os.path.isfile(ts_file_path):
                    self.transport_stream_manager.convert(file_path, ts_file_path)
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
            clip.close()
            print(f"  - Size is {size}")
            max_width = max(max_width, size[0])
            max_height = max(max_height, size[1])

        print(f"Max width is {max_width}, Max height is {max_height}")
        self.size = (max_width, max_height)

    def video_clip(self, video):
        file_path =  self.transport_stream_manager.get_file_path(video)
        clip = VideoFileClip(file_path)

        start_time = video.get('start', 0)
        max_duration = video.get('duration')
        subclip_start, subclip_end = start_time, None

        if max_duration is not None:
            # Set end time only if max_duration is not None
            subclip_end = start_time + max_duration
        elif self.subclip_duration is not None:
            subclip_end = start_time + self.subclip_duration

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
            # Ensure that the background color is not a string and it has only 3 elements
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

    def video_text_overlay_clip(self, video, clip_duration, description_duration=3, margin=5):

        ticket_clip, ticket_width = self.render_ticket_clip(clip_duration, margin, video)
        # duration_clip, duration_width = self.render_duration_clip(clip_duration, description_duration, margin, video)
        duration_clip, duration_width = self.render_remaining_duration_clip(video=video, duration=clip_duration,
                                                                            margin=margin)
        txt_clip = self.render_description_clip(description_duration, margin, ticket_width, duration_width, video)

        timelapse_clip = None  # self.render_timelapse_clip(video, clip_duration)

        # Process and return
        clips = [ticket_clip, txt_clip, duration_clip, timelapse_clip, ]
        result = self.composite_video_clip(clips)
        if result:
            result.show()
        return result

    def render_duration_clip(self, clip_duration, description_duration, margin, video):
        # Display duration of clip
        duration_width = 0
        duration_clip = None
        if video.get('show duration', True):
            txt = TextClip(f"{int(clip_duration)} sec", font="Amiri-Bold", fontsize=self.txt_ticket_fontsize,
                           color='blue').set_duration(
                description_duration).fx(vfx.fadeout, self.fadeout)
            duration_clip = (
                txt.on_color(size=(txt.w + 6, txt.h + 6),
                             color=3 * [255])
                .margin(1)
                .margin(bottom=margin, left=margin, right=margin, opacity=0.0)
                .set_pos(('right', 'bottom'))
            )
            duration_width = duration_clip.w - margin
            duration_clip = duration_clip.set_duration(description_duration).fx(vfx.fadein, self.fadein)
            txt.close()
        return duration_clip, duration_width

    def render_remaining_duration_clip(self, video, duration, margin, time_step=1):
        # Display duration of clip
        duration_width = 0
        timelapse_bar = None
        if video.get('show duration', True):
            txt_clips = []
            for i in range(int(duration), 0, -time_step):
                minutes, secs = divmod(i, 60)
                time_format = "{:02d}:{:02d}".format(minutes, secs, duration // 60, duration % 60)

                txt = (TextClip(time_format, font="Amiri-Bold", fontsize=self.txt_ticket_fontsize,
                                color='white').set_duration(time_step)
                       # .fx(vfx.fadeout, self.fadeout) # Enable the fadeout/in if you want a cool "flash" effect
                       )
                txt = (
                    txt.on_color(size=(txt.w + 6, txt.h + 6),
                                 color=(255, 0, 0))
                    .margin(1)
                    .margin(bottom=margin, left=margin, right=margin, opacity=0.0)
                )
                txt_clips.append(txt)
                txt.close()

            timelapse_bar = concatenate_videoclips(txt_clips, method="compose")
            timelapse_bar = timelapse_bar.set_duration(duration).set_position(('right', 'bottom'))
            duration_width = timelapse_bar.w - margin

        return timelapse_bar, duration_width

    def render_description_clip(self, description_duration, margin, left_offset, right_offset, video):
        # Display description
        txt_clip = None
        description = video.get('description')
        if description is not None:
            # calculate width to fill between ticket and duration to create a solid bar
            width, _ = self.size
            width = width - left_offset - margin - right_offset

            txt = TextClip(description, font="Amiri-Bold", fontsize=self.txt_ticket_fontsize, color='black')
            txt_clip = (
                txt.on_color(size=(max(1 - width, txt.w + 6), txt.h + 6),
                             color=3 * [255])
                .margin(0)
                .margin(bottom=margin + 1, left=left_offset, opacity=0.0)
                .set_pos(('left', 'bottom'))
            )
            # Full width hack
            bg_clip = (
                TextClip("n/a", font="Amiri-Bold", fontsize=self.txt_ticket_fontsize, color='white')
                .on_color(size=(width, txt.h + 6),
                          color=3 * [255])
                .margin(1)
                .margin(bottom=margin, left=left_offset, opacity=0.0)
                .set_pos(('left', 'bottom'))
            )
            # keep these two the same
            fadein = self.fadein
            txt_clip = txt_clip.set_duration(description_duration).fx(vfx.fadein, fadein)
            bg_clip = bg_clip.set_duration(txt_clip.duration).fx(vfx.fadein, fadein)

            # Render into single clip
            txt_clip = self.composite_video_clip([bg_clip, txt_clip, ])
            txt.close()
        return txt_clip

    def render_ticket_clip(self, clip_duration, margin, video, pos_y='bottom', margin_top=0):
        # Display ticket
        ticket_clip = None
        ticket_width = margin

        ticket = video.get('ticket', None)
        if ticket is not None:
            txt = TextClip(ticket, font="Amiri-Bold", fontsize=self.txt_ticket_fontsize, color="red")
            ticket_clip = (
                txt.on_color(size=(txt.w + 6, txt.h + 6),
                             color=3 * [255])
                .margin(1)
                .margin(top=margin_top, bottom=margin, left=margin, opacity=0.0)
                .set_pos(('left', pos_y))
            )
            ticket_width = ticket_clip.w
            ticket_clip = ticket_clip.set_duration(clip_duration).fx(vfx.fadeout, self.fadeout)
            txt.close()
        return ticket_clip, ticket_width

    def render_timelapse_clip(self, video, duration):
        duration = int(round(duration))
        timelapse_bar = None
        if video.get('show duration', True):
            txt_clips = []
            for i in range(0, int(duration)):
                minutes, secs = divmod(i, 60)
                # format as MM:SS
                time_format = "{:02d}:{:02d}/{:02d}:{:02d}".format(minutes, secs, duration // 60, duration % 60)
                txt = TextClip(time_format, fontsize=self.txt_ticket_fontsize, color='white')
                txt = txt.set_duration(1).set_pos(('right', 'bottom'))
                txt_clips.append(txt)

            timelapse_bar = concatenate_videoclips(txt_clips, method="compose")
            timelapse_bar.set_duration(duration)
            timelapse_bar = timelapse_bar.fx(vfx.fadeout, 1.0)  # for smooth fadeout
            timelapse_bar.set_position(("right", "bottom"))
        return timelapse_bar

    def str_duration(self, clip):
        duration = clip.duration
        return f"{int(duration)} sec"

    def table_of_contents_clip(self, clip_duration=5, margin=5):
        """
        Render a table of contents clip of list of videos

        :return:
        """
        clips = []
        clips_middle = []
        toc = ["Videos:"]  # For debugging
        counter = 1
        offset_y = margin
        offset_x_middle = 0

        # Add Title and Header Line
        title = TextClip("List of demo videos", fontsize=self.txt_ticket_fontsize * 2,
                         color="orange").set_position(('center', offset_y))
        offset_y = (title.h * 2) + margin

        header = [
            TextClip("Ticket", fontsize=self.txt_ticket_fontsize,
                     color="orange").set_position(('left', offset_y)).margin(margin),
            TextClip("Description", fontsize=self.txt_ticket_fontsize,
                     color="orange").set_position(('center', offset_y)).margin(margin),
            TextClip("Length", fontsize=self.txt_ticket_fontsize,
                     color="orange").set_position(('right', offset_y)).margin(margin),
        ]
        offset_y += (header[0].h * 2) + margin

        clips.append(title)
        clips.extend(header)

        # Add TOC lines
        for video in self.videos:
            if video.get('type', 'video') == 'video' and video.get('show on toc', True):
                txt_ticket = (
                    TextClip(video.get("ticket", "-"), fontsize=self.txt_ticket_fontsize,
                             color="yellow")
                    .set_position(('left', offset_y))
                    .margin(left=margin, right=margin, )
                )

                txt_duration = (
                    TextClip(self.str_duration(self.video_clip(video)), fontsize=self.txt_ticket_fontsize,
                             color="yellow")
                    .margin(left=margin, right=margin, )
                    .set_position(('right', offset_y))
                )

                txt_description = (
                    TextClip(video.get("description", "-"), fontsize=self.txt_ticket_fontsize,
                             color="white")
                    .margin(left=margin, right=margin, )
                )

                font_height = max(txt_ticket.h, txt_duration.h, txt_description.h)
                # we want to offset the "middle" clip using the widest ticket colum.
                offset_x_middle = max(offset_x_middle, txt_ticket.w)

                clips.extend([txt_ticket, txt_duration])
                clips_middle.append({
                    "clip": txt_description,
                    "pos_y": offset_y,
                })

                # next
                offset_y += (font_height * 2) + margin
                counter += 1

        # we want to offset the "middle" clip using the widest ticket colum.
        for clip_dict in clips_middle:
            actual_clip = clip_dict["clip"]
            pos_y = clip_dict["pos_y"]

            actual_clip = actual_clip.set_pos((offset_x_middle, pos_y))
            clips.append(actual_clip)

        # Debug to CLI
        toc_text = "\n".join(toc)
        print(f"Table of Contents:\n{toc_text}")

        result = (
            self.composite_video_clip(clips)
            .set_duration(clip_duration)
            .fx(vfx.fadeout, 1.0)
            .fx(vfx.fadein, 1.0)  # for smooth fadeout
        )

        if result:
            result.show()

        result = (
            result
            .fx(vfx.fadeout, 1.0)
            .fx(vfx.fadein, 1.0)  # for smooth fadeout
        )
        return result

    def prepare_clip(self, video):
        print(f"- Prepared '{video.get('type', 'demo')}' clip for '{video['video']}'")

        clip = self.video_clip(video)
        txt_clip = self.video_text_overlay_clip(video, clip_duration=clip.duration)

        clips = [clip, txt_clip, ]
        return self.composite_video_clip(clips)

    def composite_video_clip(self, clips, size=None):
        clips = [clip for clip in clips if clip is not None]
        print(f"  - Composite Video: {len(clips)} clips")
        return CompositeVideoClip(clips, size=size if size else self.size) if len(clips) else None

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

            toc_clip = self.table_of_contents_clip(clip_duration=self.toc_fade_time).set_start(clip_length)

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


