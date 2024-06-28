import shutil
import ssl

from moviepy.editor import *
from pytube import YouTube

# Ignore SSL
# Resolves: urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000)>
ssl._create_default_https_context = ssl._create_unverified_context


def youtube_download(url, file_path):
    # Check if the video is a YouTube URL and we have not downloaded it yet

    filename = None
    if url and not os.path.isfile(file_path):
        download_path = f"{file_path}-youtube-download"
        yt = YouTube(url)

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

    return filename
