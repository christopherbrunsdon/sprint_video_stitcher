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

73

for MP4 files:
If they are not exactly same (100% same codec, same resolution, same type) MP4 files, then you have to trans-code them into intermediate streams at first:

ffmpeg -i myfile1.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts temp1.ts
ffmpeg -i myfile2.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts temp2.ts
// now join
ffmpeg -i "concat:temp1.ts|temp2.ts" -c copy -bsf:a aac_adtstoasc output.mp4
NOTE!: Output will be like first file ( and not a second one)


# Scratchpad

Fun idea:

Display table of contents at start of video. Fadeout Start video for 5 seconds to table of contents with:
- Ticket, description, time

Output File:
- Use Sprint name to gen file:

# Time

For 4:49 video
/usr/local/bin/python3 poc.py -dir=videos  291.65s user 87.83s system 158% cpu 3:59.64 total
