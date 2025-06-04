import re
import json
import streamlit as st

from datetime import datetime
from Utils import *

@st.cache_data
def parse_player_build_info(log_file):
    """Extract player build information from log file."""
    # Updated pattern to make timestamp optional
    build_info_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?##utp:(.*?)$'
    
    build_info_entries = []
    counter = 0
    
    # Handle both file path strings and file-like objects
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            content = file.read()
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        content = log_file.read().decode('utf-8', errors='ignore')
    
    # Find all player build info entries
    matches = re.finditer(build_info_pattern, content, re.MULTILINE)
    
    for match in matches:
        # Always extract timestamp from group 1 (which may be None if timestamp is missing)
        timestamp_str = match.group(1) if match.group(1) else f"Build_{counter}"
        
        # Always extract JSON data from the last group
        json_data = match.group(match.lastindex)  # This ensures we get the JSON data from the correct group
        
        if not json_data:
            # Skip if no JSON data was found
            continue
            
        # Try to parse the JSON data
        try:
            build_data = json.loads(json_data)
            
            # Check if this is a PlayerBuildInfo entry
            if build_data.get("type") == "PlayerBuildInfo":
                # Get the build steps
                steps = build_data.get("steps", [])
                total_duration = build_data.get("duration", 0)
                
                # Try to parse timestamp if available
                timestamp = None
                if match.group(1):  # Only try to parse if we have a real timestamp
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    except:
                        pass
                
                # Add the build info entry
                build_info_entries.append({
                    'timestamp': timestamp,
                    'timestamp_str': timestamp_str,
                    'phase': build_data.get("phase", "Unknown"),
                    'version': build_data.get("version", "Unknown"),
                    'process_id': build_data.get("processId", "Unknown"),
                    'total_duration_ms': total_duration,
                    'total_duration_sec': total_duration / 1000,
                    'steps': steps
                })
                counter += 1
        except json.JSONDecodeError:
            # Skip invalid JSON
            continue
    
    return build_info_entries
