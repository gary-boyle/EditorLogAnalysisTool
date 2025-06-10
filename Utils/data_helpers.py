import base64
import re
import io
import argparse
import os

def convert_to_mb(value, unit):
    """Convert a size value to MB"""
    unit = unit.lower()
    if unit == 'kb':
        return value / 1024
    elif unit == 'mb':
        return value
    elif unit == 'gb':
        return value * 1024
    elif unit == 'tb':
        return value * 1024 * 1024
    return value  # Default case

def extract_float(text, pattern):
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None

def format_time(seconds):
    """Format time in seconds to show both seconds and minutes."""
    if seconds is None or seconds < 0:
        return "N/A"
    minutes = seconds / 60
    return f"{seconds:.2f}s ({minutes:.1f} minutes)"

def get_download_link(buffer, filename):
    """Generate a link to download the specified file."""
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download {filename}</a>'    
   
def read_log_content(log_file):
    """Read content from either a file path or a file-like object."""
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            return file.read()
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        return log_file.read().decode('utf-8', errors='ignore')

def check_log_data_completeness(log_file_path, shader_df, import_df, loading_df, build_df, refresh_df, player_build_info, unity_version):
    """Check which data elements are present or missing in the log file."""
    issues = []
    
    # Check if Unity version is available
    if unity_version is None:
        issues.append("❗ Unity version information not found in the log.")
    
    # Check for timestamp information
    has_timestamps = True
    
    # Check if any dataframes have timestamp data
    if not shader_df.empty and ('timestamp' not in shader_df.columns or shader_df['timestamp'].isna().all()):
        has_timestamps = False
    if not import_df.empty and ('timestamp' not in import_df.columns or import_df['timestamp'].isna().all()):
        has_timestamps = False
    if not loading_df.empty and ('timestamp' not in loading_df.columns or loading_df['timestamp'].isna().all()):
        has_timestamps = False
    if not refresh_df.empty and ('timestamp' not in refresh_df.columns or refresh_df['timestamp'].isna().all()):
        has_timestamps = False
    if player_build_info and all(entry.get('timestamp') is None for entry in player_build_info):
        has_timestamps = False
    
    if not has_timestamps:
        issues.append("❗ Timestamp information is missing or incomplete. Time-based analysis may be limited. \n You can enable TimeStamps in Unity Editor -> Preferences -> General -> Timestamp Editor log entries ❗")
    
    # Check for shader compilation data
    if shader_df.empty:
        issues.append("❗ No shader compilation data found.  Looks like no shaders were compiled in this Editor session. ❗")
    elif 'compilation_seconds' not in shader_df.columns:
        issues.append("❗ Shader compilation time data is missing. Shader performance analysis will be limited. ❗")
    
    # Check for asset import data
    if import_df.empty:
        issues.append("❗ No asset import data found.  Looks like no assets were imported in this Editor session ❗")
    
    # Check for project loading data
    if loading_df.empty:
        issues.append("❗ No project loading time data found.  This is very unusual ❗")
    
    # Check for build report data
    if build_df.empty:
        issues.append("❗ No build report data found.  Looks like this Editor session didn't complete a Build ❗")
    
    # Check for asset pipeline refresh data
    if refresh_df.empty:
        issues.append("❗ No asset pipeline refresh data found.  Looks like the Asset Pipeline was never refreshed in this Editor Session ❗")
    
    # Check for player build info
    if not player_build_info:
        issues.append("❗ No player build performance data found.  Looks like this Editor session didn't complete a Build ❗")
    
    return issues

def extract_unity_version(log_file_path):
    """
    Extract Unity version info from the log file.
    Works with both file paths and file-like objects (BytesIO/StringIO).
    """
    version_pattern = r"Version is ['\"]([^'\"]+)['\"]"
    
    try:
        # Handle both file paths and BytesIO/StringIO objects
        if isinstance(log_file_path, (io.BytesIO, io.StringIO)):
            # Reset position to start of file
            log_file_path.seek(0)
            
            if isinstance(log_file_path, io.BytesIO):
                # Convert bytes to string
                content = log_file_path.getvalue().decode('utf-8', errors='ignore')
                lines = content.splitlines()
            else:
                # It's already a StringIO
                lines = log_file_path.getvalue().splitlines()
                
            for line in lines:
                if "Built from" in line and "Version is" in line:
                    match = re.search(version_pattern, line)
                    if match:
                        return match.group(1)
        else:
            # It's a file path
            with open(log_file_path, 'r', errors='ignore') as file:
                for line in file:
                    if "Built from" in line and "Version is" in line:
                        match = re.search(version_pattern, line)
                        if match:
                            return match.group(1)
                            
    except Exception as e:
        print(f"Error extracting Unity version: {e}")
    
    # Try again with a more relaxed pattern if initial search fails
    try:
        if isinstance(log_file_path, (io.BytesIO, io.StringIO)):
            log_file_path.seek(0)
            content = log_file_path.read().decode('utf-8', errors='ignore') if isinstance(log_file_path, io.BytesIO) else log_file_path.read()
            
            # Look for any line with Unity version pattern
            broader_pattern = r"\d{4}\.\d+\.\d+[fb]\d+"
            match = re.search(broader_pattern, content)
            if match:
                return match.group(0)
        else:
            with open(log_file_path, 'r', errors='ignore') as file:
                content = file.read()
                broader_pattern = r"\d{4}\.\d+\.\d+[fb]\d+"
                match = re.search(broader_pattern, content)
                if match:
                    return match.group(0)
    except Exception as e:
        print(f"Error in secondary Unity version extraction: {e}")
    
    return None


def parse_arguments():
    parser = argparse.ArgumentParser(description="Unity Build Log Analyzer")
    
    # Main log file argument (required)
    parser.add_argument("log_file", help="Path to Unity Editor log file", type=str)
    
    # Output path for PDF report (optional)
    parser.add_argument("--output", "-o", help="Output path for PDF report (optional)", type=str)
    
    args = parser.parse_args()
    
    # Normalize paths to handle any platform-specific issues
    args.log_file = os.path.normpath(args.log_file)
    if args.output:
        args.output = os.path.normpath(args.output)
    
    return args