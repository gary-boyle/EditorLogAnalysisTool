import re
import streamlit as st
import pandas as pd

from Utils import *

@st.cache_data
def parse_build_report(log_file):
    """Parse Unity build report data from log file."""
    # Updated pattern to make timestamp optional
    build_report_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Build Report'
    
    # Updated pattern to make timestamp optional
    category_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?(.*?)\s+(\d+\.?\d*)\s+(\w+)\s+(\d+\.?\d*)\%'
    
    # Updated pattern to make timestamp optional
    total_build_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Complete build size\s+(\d+\.?\d*)\s+(\w+)'
    
    build_data = []
    total_build_size = None
    total_build_unit = None
    
    # Handle both file path strings and file-like objects
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            content = file.read()
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        content = log_file.read().decode('utf-8', errors='ignore')
    
    # Find the build report section
    build_report_match = re.search(build_report_pattern, content)
    if not build_report_match:
        return pd.DataFrame(), None, None
    
    # Extract the portion of the log containing the build report
    report_start = build_report_match.start()
    report_end = min(len(content), report_start + 2000)  # Enough lines to capture the report
    report_content = content[report_start:report_end]
    
    # Find all asset category entries
    category_matches = re.finditer(category_pattern, report_content)
    
    for match in category_matches:
        timestamp_str = match.group(1) if match.lastindex >= 5 and match.group(1) else None
        group_offset = 0 if timestamp_str is None else 0
        category = match.group(2).strip()
        size_value = float(match.group(3))
        size_unit = match.group(4)
        percentage = float(match.group(5))
        
        # Convert all sizes to MB for consistent comparison
        size_in_mb = convert_to_mb(size_value, size_unit)
        
        build_data.append({
            'timestamp_str': timestamp_str if timestamp_str else "N/A",
            'category': category,
            'size_value': size_value,
            'size_unit': size_unit,
            'size_in_mb': size_in_mb,
            'percentage': percentage
        })
    
    # Extract total build size
    total_match = re.search(total_build_pattern, report_content)
    if total_match:
        group_count = len(total_match.groups())
        if group_count >= 3 and total_match.group(1):  # With timestamp
            total_build_size = float(total_match.group(2))
            total_build_unit = total_match.group(3)
        else:  # Without timestamp
            total_build_size = float(total_match.group(1) if group_count == 2 else total_match.group(2))
            total_build_unit = total_match.group(2) if group_count == 2 else total_match.group(3)
    
    return pd.DataFrame(build_data) if build_data else pd.DataFrame(), total_build_size, total_build_unit
