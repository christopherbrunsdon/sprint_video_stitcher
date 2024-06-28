import argparse

from code.video_stitch import VideoData

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Stitch sprint videos")

    parser.add_argument('-dir', metavar='dir', type=str, help='the working directory for your videos')
    parser.add_argument('-preview', metavar='preview', type=int, nargs='?',
                        help='Create preview clip in seconds of each video before stitching')
    parser.add_argument('-config', metavar='config', type=str, default="config.yml",
                        help='the yaml data config file for your videos in your working directory')
    args = parser.parse_args()
    print(f"Stitching Sprint Video from directory: {args.dir}")

    if args.preview:
        print(f"PREVIEW MODE: All clips to be cut to {args.preview} seconds")

    videos = VideoData(dir=args.dir, config=args.config, subclip_duration=args.preview)
    videos.run()
