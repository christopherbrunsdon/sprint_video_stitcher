# Disclaimer:

This is WIP and the code will change, it will break and will go boom.

To see sample of video created from the `/example` path:

[[!Demo](https://youtu.be/8_L99gbYABU)] (https://youtu.be/8_L99gbYABU "Video Stitcher Demo")



## Requirements

Ref: https://pypi.org/project/moviepy/

```bash
brew install imagemagick
brew install ffmpeg
brew install libmp3splt
```

## Config explained

Your `config.yml` contains your config. For now this filename is hardcoded. You must call the script with your working path that contains your file.

### config.yml

```yaml
Author: Bilbo B
Sprint: My Sprint Name
Project: My Project
Description: A description
Videos:
  - type: opening
    video: intro.mp4
    show duration: False
        
  - video: TICKET-329-demo.mp4
    ticket: TICKET-329

  - type: closing
    video: credits.mp4
```

Required:

Section Videos:

- video (name of the video file)

Optional:

- type (to define "opening" and "closing" videos)
- youtube-url (Youtube URL and it will use the "video" filename to save the file as)
- ticket (This is a sticky render at bottom left corner)
- description (A description to display at bottom of video for five seconds)
- show duration (Defaults `True` and this will display the timer in bottom right corner)
- skip (Defaults `True`)
- background (The background colour, it will replace the video and only keep audio)
- title (A title to display in the middle of the video)
- color (The color of the title)
 
### config.yml - opening and closing videos

You need to declare two types "opening" and "closing" as your start/stop videos. There can be multiple, but at least one of each.

```yaml
Videos:
  - type: opening
    video: intro.mp4

  - type: closing
    video: credits.mp4
 ```

Required:
- type ("opening" and "closing")
- video (file name of vide)

### config.yaml - standard videos

```yaml
Videos:
  - ...

  - video: TICKET-107-demo.mp4
    ticket: TICKET-107
    description: This is a another cool feature.
    skip: False

  - video: TICKET-99-demp.mp4
    ticket: TICKET-99
    description: This is a another cool feature. 99 Bottles
    show duration: False

  - video: yt-end.mp4
    youtube-url: https://www.youtube.com/watch?v=wFZHa5rWddo
    title: Just something...
    description: to listen too from Youtube with text
    ticket: Middle
    background: [0, 0, 0]
    color: orange

```

Remember: To skip the video, use `skip: False`. It will not get processed at all.


### Config: URLs as video source

You can use URLs as video sources. The script will download the video.

```yaml
  - video: yt-end.mp4
    youtube-url: https://www.youtube.com/watch?v=wFZHa5rWddo
    title: Just something...
    description: to listen too from Youtube with text
    ticket: Middle
    background: [0, 0, 0]
    color: orange
```




### Config: Adding A Watermark

```yaml
Watermark:
  url: https://sample-videos.com/img/Sample-png-image-100kb.png
  path: sample.png
  position: ["right","top"]
  height-ratio: 0.05
```

The code will first take `url:` if it exists, else `path:`

The watermark will be rendered through the entire video, first to last frame.


### Run it

There are two params

`-dir` - the working directory containing your config file and all your assets. For now, it will look for `config.yml` in the path.

`-preview` - ability to cut your videos to value in seconds. Great for quickly previewing your video.

When running, you will see a preview modal popup to preview the text overlays for each video. These start at frame one and close when script is done.

To build the example path config
```bash
python video_stitch.py -dir=example -preview=10
```

Credit: Base Rebels for Copyright free music: https://www.youtube.com/@BassRebels




### Manual add chapters:

A todo feature is to capture the captures, for now, follow the following readme and make use of the stats dump when building your video to get the chapter positions.

https://ikyle.me/blog/2020/add-mp4-chapters-ffmpeg

When building a video you will get a dump of stats:

```
Total duration: 43.0
Total clips: 2
Starting times for each clip in the final video (in seconds):
Chapter 1: 0 sec
Chapter 2: 5.0 sec
Chapter 3: 10.0 sec
Chapter 4: 15.0 sec
Chapter 5: 20.0 sec
Chapter 6: 25.0 sec
Chapter 7: 30.0 sec
Chapter 8: 33.0 sec
Chapter 9: 38.0 sec

```

You can use this to create a chapter file

Example: Chapters.txt
```
0:23:20 Start
0:40:30 First Performance
0:40:56 Break
1:04:44 Second Performance
1:24:45 Crowd Shots
1:27:45 Credits
```


### Transport streams

Transport streams are created from each video.

# Known Issues

### Why opencv-python?

We need to install `opencv-python` for the resizing due to a moviepy bug with PIL

Ref: https://github.com/Zulko/moviepy/issues/2002

