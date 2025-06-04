import re
import os
import pandas as pd
import streamlit as st

from datetime import datetime
from Utils import *

@st.cache_data
def parse_asset_imports(log_file):
    """Extract asset import data from the log file."""
    # Updated regex pattern to make timestamp optional
    import_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Start importing (.*?) using .* \((.*?)\) -> .* in (\d+\.\d+) seconds'
    
    import_data = []
    
    # Handle both file path strings and file-like objects
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            content = file.read()
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        content = log_file.read().decode('utf-8', errors='ignore')
    
    # Find all import entries
    matches = re.finditer(import_pattern, content)
    
    for match in matches:
        timestamp_str = match.group(1) if match.lastindex >= 1 and match.group(1) else None
        # Adjust group indices based on whether timestamp was captured
        group_offset = 0 if timestamp_str is None else 0
        asset_path = match.group(2)
        importer_type = match.group(3)
        import_time = float(match.group(4))
        
        # Get file extension
        _, file_extension = os.path.splitext(asset_path)
        file_extension = file_extension.lower()
        
        # Try to parse timestamp if available
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except:
                pass
            
        import_data.append({
            'timestamp': timestamp,
            'timestamp_str': timestamp_str,
            'asset_path': asset_path,
            'asset_name': os.path.basename(asset_path),
            'file_extension': file_extension,
            'importer_type': importer_type,
            'import_time_seconds': import_time
        })
    
    return pd.DataFrame(import_data) if import_data else pd.DataFrame()
