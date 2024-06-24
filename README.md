# Disclaimer:

This is WIP and the code will change, it will break and will go boom.

## Requirements

Ref: https://pypi.org/project/moviepy/

```bash
brew install imagemagick
brew install ffmpeg
brew install libmp3splt
```


### Manual add chapters:

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

