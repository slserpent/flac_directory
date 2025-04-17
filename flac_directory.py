#!/usr/bin/env python3
"""
WAV to FLAC converter script using ffmpeg.
Can also convert FLAC files back to WAV format.
Preserves original audio characteristics for truly lossless conversion.

Created with Claude 3.7
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def check_ffmpeg():
    """Check if ffmpeg is installed and available in the system path."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not in the system path.")
        print("Please install ffmpeg and try again.")
        return False


def convert_file(input_file, output_file, to_wav=False, overwrite=False):
    """
    Convert a single file using ffmpeg, preserving original audio characteristics.
    
    Args:
        input_file (Path): Source file path
        output_file (Path): Destination file path
        to_wav (bool): If True, convert FLAC to WAV. If False, convert WAV to FLAC.
        overwrite (bool): If True, overwrite existing files.
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    # Skip if output exists and overwrite is False
    if output_file.exists() and not overwrite:
        print(f"Skipping {input_file} (output file exists and overwrite is disabled)")
        return False
        
    if to_wav:
        # FLAC to WAV conversion settings - preserve original format
        cmd = [
            "ffmpeg", "-i", str(input_file), 
            str(output_file)
        ]
    else:
        # WAV to FLAC conversion settings. Use default compression level for speed.
        cmd = [
            "ffmpeg", "-i", str(input_file), 
            "-c:a", "flac",
            str(output_file)
        ]
    
    # Add overwrite parameter if needed
    if overwrite:
        cmd.append("-y")
    else:
        cmd.append("-n")  # Do not overwrite
    
    try:
        # Run the command and capture output
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            # Don't consider it an error if we skipped due to file exists
            if "already exists. Exiting." in result.stderr:
                print(f"Skipping {input_file} (output file exists)")
                return False
            
            print(f"Error converting {input_file}:")
            print(result.stderr)
            return False
        
        return True
    except Exception as e:
        print(f"Exception while converting {input_file}: {str(e)}")
        return False


def process_directory(input_dir, recursive=False, to_wav=False, delete_original=False, overwrite=False):
    """
    Process all WAV/FLAC files in the given directory.
    
    Args:
        input_dir (str): Directory to process
        recursive (bool): Whether to process subdirectories
        to_wav (bool): If True, convert FLAC to WAV. If False, convert WAV to FLAC.
        delete_original (bool): Whether to delete the original files after conversion
        overwrite (bool): Whether to overwrite existing files
    """
    import time
    start_time = time.time()
    
    input_path = Path(input_dir)
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: {input_dir} is not a valid directory.")
        return
    
    # Define which files to look for based on conversion direction
    source_ext = ".flac" if to_wav else ".wav"
    target_ext = ".wav" if to_wav else ".flac"
    
    # Set up source file discovery
    if recursive:
        source_files = list(input_path.glob(f"**/*{source_ext}"))
    else:
        source_files = list(input_path.glob(f"*{source_ext}"))
    
    if not source_files:
        print(f"No {source_ext} files found in {input_dir}" + (" and its subdirectories" if recursive else ""))
        return
    
    # Process all files
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    # For compression ratio calculation
    total_input_size = 0
    total_output_size = 0
    
    print(f"Converting {len(source_files)} {source_ext} files to {target_ext}...")
    
    for source_file in source_files:
        # Create output file path with changed extension
        output_file = source_file.with_suffix(target_ext)
        
        # Get input file size before conversion
        input_size = source_file.stat().st_size
        
        # Skip if output file exists, is newer than source, and overwrite is False
        if (not overwrite and output_file.exists() and 
            output_file.stat().st_mtime > source_file.stat().st_mtime):
            print(f"Skipping {source_file} (output file exists and is newer)")
            skipped_count += 1
            continue
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert the file
        print(f"Converting {source_file} to {output_file}")
        if convert_file(source_file, output_file, to_wav, overwrite):
            success_count += 1
            
            # Store file sizes for compression ratio calculation
            total_input_size += input_size
            total_output_size += output_file.stat().st_size
            
            # Delete original if requested
            if delete_original and output_file.exists():
                try:
                    source_file.unlink()
                    print(f"Deleted original file: {source_file}")
                except Exception as e:
                    print(f"Warning: Could not delete {source_file}: {str(e)}")
        else:
            # Check if it's a skip rather than an actual error
            if output_file.exists() and not overwrite:
                skipped_count += 1
            else:
                error_count += 1
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Format execution time
    if execution_time < 60:
        time_str = f"{execution_time:.2f} seconds"
    elif execution_time < 3600:
        minutes = int(execution_time // 60)
        seconds = execution_time % 60
        time_str = f"{minutes} minutes {seconds:.2f} seconds"
    else:
        hours = int(execution_time // 3600)
        minutes = int((execution_time % 3600) // 60)
        seconds = execution_time % 60
        time_str = f"{hours} hours {minutes} minutes {seconds:.2f} seconds"
    
    # Print summary
    print("\nConversion Summary:")
    print(f"  Converted: {success_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(source_files)}")
    print(f"  Execution time: {time_str}")
    
    # Print compression statistics if any files were converted
    if success_count > 0:
        ratio = total_output_size / total_input_size if total_input_size > 0 else 0
        space_saved = total_input_size - total_output_size
        space_saved_percent = (1 - ratio) * 100
        
        print("\nCompression Statistics:")
        print(f"  Total original size: {format_size(total_input_size)}")
        print(f"  Total converted size: {format_size(total_output_size)}")
        print(f"  Space {('saved' if space_saved > 0 else 'increased')}: {format_size(abs(space_saved))}")
        print(f"  Compression ratio: {ratio:.2f} ({space_saved_percent:.1f}% {('savings' if space_saved > 0 else 'increase')})")

def format_size(size_in_bytes):
    """Format file size in a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0 or unit == 'TB':
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0

def main():
    parser = argparse.ArgumentParser(description="Convert WAV files to FLAC (or vice-versa) using FFmpeg and preserving original audio data.")
    parser.add_argument("input_dir", nargs='?', help="Input directory containing files to convert")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively process subdirectories")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete original files after conversion")
    parser.add_argument("-w", "--to-wav", action="store_true", help="Convert FLAC to WAV instead of WAV to FLAC")
    parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    if not args.input_dir:
        parser.print_help()
        exit(1)
    
    # Check if ffmpeg is installed
    if not check_ffmpeg():
        sys.exit(1)
    
    # Perform the conversion
    process_directory(args.input_dir, args.recursive, args.to_wav, args.delete, args.overwrite)


if __name__ == "__main__":
    main()