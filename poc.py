import argparse
import subprocess

import yaml
from moviepy.editor import *


class VideoData:
    def __init__(self, dir, config, subclip_duration=None, output_file="output.mp4"):
        self.clips = None
        self.videos = None
        self.closing_videos = None
        self.opening_videos = None
        self.sprint = None
        self.project = None
        self.dir = dir
        self.dir_ts = os.path.join(self.dir, "ts/")
        self.subclip_duration = subclip_duration
        self.output_file = output_file
        self.size = None

        self.load_config(config)
        valid, msg = self.verify_config()
        if not valid:
            raise Exception(msg)

        # hard coded for now
        self.fadein = 1
        self.fadeout = 1
        self.txt_ticket_fontsize = 22

    def run(self):
        self.prepare()
        self.get_max_video_size()
        self.stitch()

    def load_config(self, config):
        """
        Loading of config

        Example of valid config file:
            Sprint: My Sprint Name
            Project: My Project Name
            Videos:
              - video: ABC123-my-ticket.mp4
                description: Adding some feature.
              - video: Open.mp4
                type: opening
              - video: Close.mp4
                type: closing

        :param config:
        :return:
        """
        with open(os.path.join(self.dir, config), 'r') as ymlfile:
            config_dict = yaml.safe_load(ymlfile)
            self.sprint = config_dict.get('Sprint')
            self.project = config_dict.get('Project')
            self.videos = [video for video in config_dict.get('Videos') if not video.get('_skip')]

        self.opening_videos = [video for video in self.videos if video.get('type') == 'opening']
        self.closing_videos = [video for video in self.videos if video.get('type') == 'closing']

    def verify_config(self):
        """
        Verify the config file is valid.

        Required:
        - Sprint: string
        - Project: string
        - Videos: list of strings

        Rules:
        1 - One video tagged with type opening
        2 - One video tagged with type closing

        Example of valid config file:
            Sprint: My Sprint Name
            Project: My Project Name
            Videos:
              - video: ABC123-my-ticket.mp4
                description: Adding some feature.
              - video: Open.mp4
                type: opening
              - video: Close.mp4
                type: closing

        :return:
        """
        if not isinstance(self.sprint, str):
            return False, "Sprint is not a string"
        if not isinstance(self.project, str):
            return False, "Project is not a string"
        if not isinstance(self.videos, list):
            return False, "Videos are not a list"

        if len(self.opening_videos) != 1 or len(self.closing_videos) != 1:
            return False, "There should be one video tagged with type 'opening' and one with type 'closing'"

        return True, "Config file is valid"

    def convert_to_ts(self, input_file, output_file):
        command = f"ffmpeg -i '{input_file}' -c copy -bsf:v h264_mp4toannexb -f mpegts '{output_file}'"
        subprocess.run(command, shell=True, check=True)

    def prepare(self):
        """
        :return:
        """
        # Create subdirectory "ts" if not exists and then check .ts files.
        if not os.path.exists(self.dir_ts):
            os.makedirs(self.dir_ts)

        for video in self.videos:
            file_path = self.get_file_path(video)
            ts_file_path = self.get_ts_file_path(video)

            if os.path.isfile(file_path):
                if not os.path.isfile(ts_file_path):
                    self.convert_to_ts(file_path, ts_file_path)
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
        file_path = self.get_ts_file_path(video)
        clip = VideoFileClip(file_path)

        if self.subclip_duration:
            print(f"  - Clip Duration: {self.subclip_duration} seconds")
            clip = clip.subclip(0, self.subclip_duration)

        if self.fadein:
            print(f"  - Fadein: {self.fadein} seconds")
            clip = clip.fx(vfx.fadein, self.fadein)

        if self.fadeout:
            print(f"  - Fadeout: {self.fadeout} seconds")
            clip = clip.fx(vfx.fadeout, self.fadeout)

        return clip

    def video_text_overlay_clip(self, video, clip_duration, description_duration=3):
        txt_clip = None
        ticket_clip = None
        duration_clip = None
        timelapse_clip = None
        margin = 5
        ticket_width = margin
        duration_width = margin

        # Display ticket
        ticket = video.get('ticket', None)
        if ticket is not None:
            txt = TextClip(ticket, font="Amiri-Bold", fontsize=self.txt_ticket_fontsize, color="red")
            ticket_clip = (
                txt.on_color(size=(txt.w + 6, txt.h + 6),
                             color=3 * [255])
                .margin(1)
                .margin(bottom=margin, left=margin, opacity=0.0)
                .set_pos(('left', 'bottom'))
            )
            ticket_width = ticket_clip.w
            ticket_clip = ticket_clip.set_duration(clip_duration).fx(vfx.fadeout, self.fadeout)
            txt.close()

        # Display duration of clip
        if video.get('show duration', True):
            # txt = TextClip(f"{int(clip_duration)} sec", font="Amiri-Bold", fontsize=self.txt_ticket_fontsize,
            #                color='blue').set_duration(
            #     description_duration).fx(vfx.fadeout, self.fadeout)
            # duration_clip = (
            #     txt.on_color(size=(txt.w + 6, txt.h + 6),
            #                  color=3 * [255])
            #     .margin(1)
            #     .margin(bottom=margin, left=margin, right=margin, opacity=0.0)
            #     .set_pos(('right', 'bottom'))
            # )
            # duration_width = duration_clip.w - margin
            # duration_clip = duration_clip.set_duration(description_duration).fx(vfx.fadein, self.fadein)
            # txt.close()

            timelapse_clip = self.render_timelapse_clip(clip_duration)

        # Display description
        description = video.get('description')
        if description is not None:
            # calculate width to fill between ticket and duration to create a solid bar
            width, _ = self.size
            width = width - ticket_width - margin  # - duration_width

            txt = TextClip(description, font="Amiri-Bold", fontsize=self.txt_ticket_fontsize, color='black')
            txt_clip = (
                txt.on_color(size=(max(1 - width, txt.w + 6), txt.h + 6),
                             color=3 * [255])
                .margin(0)
                .margin(bottom=margin + 1, left=ticket_width, opacity=0.0)
                .set_pos(('left', 'bottom'))
            )
            # Full width hack
            bg_clip = (
                TextClip("n/a", font="Amiri-Bold", fontsize=self.txt_ticket_fontsize, color='white')
                .on_color(size=(width, txt.h + 6),
                          color=3 * [255])
                .margin(1)
                .margin(bottom=margin, left=ticket_width, opacity=0.0)
                .set_pos(('left', 'bottom'))
            )

            # keep these two the same
            fadein = self.fadein
            txt_clip = txt_clip.set_duration(description_duration).fx(vfx.fadein, fadein)
            bg_clip = bg_clip.set_duration(txt_clip.duration).fx(vfx.fadein, fadein)

            # Render into single clip
            txt_clip = self.composite_video_clip([bg_clip, txt_clip, ])
            txt.close()

        # Process and return
        clips = [ticket_clip, txt_clip, timelapse_clip, ]
        result = self.composite_video_clip(clips)
        if result:
            result.show()
        return result

    def render_timelapse_clip(self, duration):
        txt_clips = []
        for i in range(0, int(duration)):
            mins, secs = divmod(i, 60)
            # format as MM:SS
            time_format = "{:02d}:{:02d}/{:02d}:{:02d}".format(mins, secs, duration // 60, duration % 60)
            txt = TextClip(time_format, fontsize=self.txt_ticket_fontsize, color='white')
            txt = txt.set_duration(1).set_pos(('right', 'bottom'))
            txt_clips.append(txt)
        timelapse_bar = concatenate_videoclips(txt_clips, method="compose")
        timelapse_bar.set_duration(duration)
        timelapse_bar = timelapse_bar.fx(vfx.fadeout, 1.0)  # for smooth fadeout
        return timelapse_bar.set_position(("right", "bottom"))

    def table_of_contents_clip(self, duration=5):
        """
        Render a table of contents clip of list of videos

        @todo: this will always render in the center. Need to do this line by line.

        :return:
        """
        toc = ["Videos:"]
        counter = 1
        for video in self.videos:
            if video.get('type', 'video') == 'video':
                toc.append(f"{counter}. - {video.get('ticket')} - {video.get('description')}")
                counter += 1

        toc_text = "\n".join(toc)
        print(f"Table of Contents:\n{toc_text}")

        toc_clip = TextClip(toc_text, fontsize=self.txt_ticket_fontsize, color='blue')
        toc_clip = (
            toc_clip.on_color(size=(toc_clip.w + 6, toc_clip.h + 6),
                         color=3 * [255])
            .margin(1)
            # .margin(bottom=margin, left=margin, opacity=0.0)
            .set_pos(('left', 'bottom'))
        )
        toc_clip = toc_clip.set_position(('left','center')).set_duration(duration)


        # toc_clip = toc_clip.fx(vfx.fadeout, 1.0).fx(vfx.fadein, 1.0)  # for smooth fadeout
        toc_clip.show()
        return toc_clip


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
        opening_clips = [
            self.composite_video_clip(
                [
                    self.prepare_clip(video).fx(vfx.fadeout, 5.0),
                    self.table_of_contents_clip(),
                ]
            ) for video in self.opening_videos
        ]
        # toc_clips = [self.table_of_contents_clip()]

        # Prepare clips for videos where type is not None
        print(f"Preparing middle clips:")
        middle_clips = [self.prepare_clip(video) for video in self.videos if video.get('type') is None]

        # Prepare the closing clips
        print(f"Preparing closing clips:")
        closing_clips = [self.prepare_clip(video) for video in self.closing_videos]

        # Combine opening, middle and closing clips in order
        self.clips = opening_clips  #+ middle_clips + closing_clips

    def stitch(self):
        """
        Stitch all the clips into final video
        :return:
        """
        self.prepare_clips()
        # time.sleep(1)
        # return
        final_clip = concatenate_videoclips(self.clips)
        output_file_path = os.path.join(self.dir, self.output_file)
        final_clip.write_videofile(output_file_path, codec='libx264', audio_codec='aac')

    def get_file_path(self, video):
        return os.path.join(self.dir, video['video'])

    def get_ts_file_path(self, video):
        file_path = self.get_file_path(video)
        filename_without_ext = os.path.splitext(os.path.basename(file_path))[0]
        ts_file_path = os.path.join(self.dir_ts, filename_without_ext + '.ts')
        return ts_file_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Stitch sprint videos")

    parser.add_argument('-dir', metavar='dir', type=str, help='the working directory for your videos')
    parser.add_argument('-preview', metavar='preview', type=int, nargs='?',
                        help='Create preview clip in seconds of each video before stitching')
    parser.add_argument('-config', metavar='config', type=str, default="config.yml",
                        help='the yaml data config file for your videos')
    args = parser.parse_args()
    print(f"Stitching Sprint Video from directory: {args.dir}")

    if args.preview:
        print(f"PREVIEW MODE: All clips to be cut to {args.preview} seconds")

    videos = VideoData(dir=args.dir, config=args.config, subclip_duration=args.preview)
    videos.run()
