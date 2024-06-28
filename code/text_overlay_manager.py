from moviepy.editor import *


class TextOverlayManager:

    def __init__(self, config_manager):
        self.config_manager = config_manager

        self.txt_ticket_fontsize = self.config_manager.txt_ticket_fontsize
        self.fadein = self.config_manager.fadein
        self.fadeout = self.config_manager.fadeout

    def video_text_overlay_clip(self, video, clip_duration, description_duration=3, margin=5):

        ticket_clip, ticket_width = self._render_ticket_clip(clip_duration, margin, video)
        # duration_clip, duration_width = self._render_duration_clip(clip_duration, description_duration, margin, video)
        duration_clip, duration_width = self._render_remaining_duration_clip(video=video, duration=clip_duration,
                                                                             margin=margin)
        txt_clip = self._render_description_clip(description_duration, margin, ticket_width, duration_width, video)

        timelapse_clip = None  # self.render_timelapse_clip(video, clip_duration)

        # Process and return
        clips = [ticket_clip, txt_clip, duration_clip, timelapse_clip, ]
        result = self._composite_video_clip(clips)
        if result:
            result.show()
        return result

    def _render_duration_clip(self, clip_duration, description_duration, margin, video):
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

    def _render_remaining_duration_clip(self, video, duration, margin, time_step=1):
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

    def _render_description_clip(self, description_duration, margin, left_offset, right_offset, video):
        # Display description
        txt_clip = None
        description = video.get('description')
        if description is not None:
            # calculate width to fill between ticket and duration to create a solid bar
            width, _ = self.config_manager.size
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
            txt_clip = self._composite_video_clip([bg_clip, txt_clip, ])
            txt.close()
        return txt_clip

    def _render_ticket_clip(self, clip_duration, margin, video, pos_y='bottom', margin_top=0):
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

    def _composite_video_clip(self, clips, size=None):
        clips = [clip for clip in clips if clip is not None]
        print(f"  - Composite Video: {len(clips)} clips")
        return CompositeVideoClip(clips, size=size if size else self.config_manager.size) if len(clips) else None
