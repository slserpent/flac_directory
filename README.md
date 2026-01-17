# flac_directory
Just a little python script to convert all uncompressed WAV audio files in a directory (and optionally all subdirectories) to FLAC for long-term storage. Can also convert the FLAC files back to WAV if needed and delete files after completion. Compression statistics are displayed at script completion. Uses FFmpeg.

## Usage
```
flac_directory.py [-r] [-d] [-w] [-o] input_dir

positional arguments:
  input_dir        Input directory containing files to convert

optional arguments:
  -r, --recursive  Recursively process subdirectories
  -d, --delete     Delete original files after conversion
  -w, --to-wav     Convert FLAC to WAV instead of WAV to FLAC
  -o, --overwrite  Overwrite existing files
```
