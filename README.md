# cut and remux video from growing video file for use in video editor

## COE workflow
1. OBS handling the broadcast has source record filters on the sources we are interested in.
    1. Source record using a set of codecs that are easy to edit (h264/aac) and that fit in ISO-BMFF containers
    2. Recording output in MPEG-TS so that it doesn't matter that the file hasn't been closed yet
3. Uses ffmpeg and `-fflags fastseek` to seek 240 seconds from EOF
4. Remuxes into an mp4 file that can easily be read by video editors
5. ???
6. Profit?
