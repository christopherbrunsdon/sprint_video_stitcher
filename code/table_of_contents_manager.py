from moviepy.editor import *

class TableOfContentsManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.videos = self.config_manager.videos
        self.toc_fade_time =  self.config_manager.toc_fade_time
        self.txt_ticket_fontsize = self.config_manager.txt_ticket_fontsize

    def clip(self, margin=5):
        """
        Render a table of contents clips of list of videos

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
                    TextClip(
                        self._duration_str(video.get("duration")),
                        fontsize=self.txt_ticket_fontsize,
                        color="yellow"
                    )
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
            self._composite_video_clip(clips)
            .set_duration(self.toc_fade_time)
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

    def _composite_video_clip(self, clips):
        clips = [clip for clip in clips if clip is not None]
        print(f"  - Composite Video: {len(clips)} clips")
        return CompositeVideoClip(clips, size=self.config_manager.size) if len(clips) else None

    def _duration_str(self, duration):
        return f"{int(duration)} sec"