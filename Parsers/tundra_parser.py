import re
import streamlit as st

from Utils import *

@st.cache_data
def parse_tundra_build_info(log_file):
    """Extract Tundra build information from the log file."""
    tundra_pattern = r'\*\*\* Tundra build success \((\d+\.\d+) seconds - (\d+:\d+:\d+)\), (\d+) items updated, (\d+) evaluated'
    
    tundra_info = []
    
    # Handle both file path strings and file-like objects
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            lines = file.readlines()
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        lines = log_file.read().decode('utf-8', errors='ignore').splitlines()
    
    for line in lines:
        match = re.search(tundra_pattern, line)
        if match:
            tundra_info.append({
                'build_time_seconds': float(match.group(1)),
                'build_time_formatted': match.group(2),
                'items_updated': int(match.group(3)),
                'items_evaluated': int(match.group(4))
            })
    
    return tundra_info
