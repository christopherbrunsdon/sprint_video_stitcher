## Requirements

Ref: https://pypi.org/project/moviepy/

```bash
brew install imagemagick
brew install ffmpeg
brew install libmp3splt
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
