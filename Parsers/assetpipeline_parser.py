import re
import pandas as pd
import streamlit as st

from datetime import datetime
from Utils import *

@st.cache_data
def parse_asset_pipeline_refresh(log_file):
    """Extract asset pipeline refresh information from log file."""
    # Updated pattern to make timestamp optional
    refresh_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Asset Pipeline Refresh \(id=([^)]+)\): Total: ([\d.]+) seconds - Initiated by (.*?)$'
    
    refresh_data = []
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
    
    # Find all refresh entries
    matches = re.finditer(refresh_pattern, content, re.MULTILINE)
    
    for match in matches:
        has_timestamp = match.lastindex >= 4 and match.group(1)
        timestamp_str = match.group(1) if has_timestamp else f"Refresh_{counter}"
        group_offset = 0 if has_timestamp else -1
        
        refresh_id = match.group(2)
        total_time = float(match.group(3))
        initiator = match.group(4).strip()
        
        # Try to parse timestamp if available
        timestamp = None
        if has_timestamp:
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except:
                pass
            
        refresh_data.append({
            'timestamp': timestamp,
            'timestamp_str': timestamp_str,
            'refresh_id': refresh_id,
            'total_time': total_time,
            'initiator': initiator
        })
        counter += 1
    
    return pd.DataFrame(refresh_data) if refresh_data else pd.DataFrame()
