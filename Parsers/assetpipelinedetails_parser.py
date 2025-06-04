import re
import streamlit as st

from datetime import datetime
from Utils import *

@st.cache_data
def parse_asset_pipeline_refresh_details(log_file):
    """Extract detailed breakdown of asset pipeline refresh operations."""
    # Pattern to match asset pipeline refresh entries with ID and time
    refresh_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Asset Pipeline Refresh \(id=([^)]+)\): Total: ([\d.]+) seconds - Initiated by (.*?)$'
    
    # Pattern for individual operations in the breakdown
    operation_pattern = r'^\t+([\w()]+): ([\d.]+)ms(?:\s+\(([\d.]+)ms without children\))?$'
    
    # Pattern for nested operations (additional indent level)
    nested_operation_pattern = r'^\t\t+([\w()]+): ([\d.]+)ms(?:\s+\(([\d.]+)ms without children\))?$'
    
    refresh_details = []
    
    # Handle both file path strings and file-like objects
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            content = file.readlines()
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        content = log_file.read().decode('utf-8', errors='ignore').splitlines()
    
    for i, line in enumerate(content):
        match = re.search(refresh_pattern, line)
        if match:
            has_timestamp = match.group(1) is not None
            timestamp_str = match.group(1) if has_timestamp else None
            refresh_id = match.group(2)
            total_time = float(match.group(3))
            initiator = match.group(4).strip()
            
            # Try to parse timestamp if available
            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                except:
                    pass
            
            # Collect all operations that are part of this refresh
            operations = []
            j = i + 1
            summary_data = {}
            
            # Check if there's a summary section
            if j < len(content) and "Summary:" in content[j]:
                j += 1
                # Parse summary lines
                while j < len(content) and content[j].strip() and content[j].startswith('\t\t'):
                    summary_line = content[j].strip()
                    if ':' in summary_line:
                        key, value = summary_line.split(':', 1)
                        summary_data[key.strip()] = value.strip()
                    j += 1
            
            # Parse operations
            while j < len(content) and content[j].strip() and content[j].startswith('\t'):
                op_line = content[j]
                op_match = re.search(operation_pattern, op_line)
                
                if op_match:
                    op_name = op_match.group(1)
                    op_time = float(op_match.group(2))
                    op_self_time = float(op_match.group(3)) if op_match.group(3) else op_time
                    
                    # Initialize the operation entry
                    operation = {
                        'name': op_name,
                        'time_ms': op_time,
                        'self_time_ms': op_self_time,
                        'nested_operations': []
                    }
                    
                    # Look for nested operations (next lines with additional indent)
                    k = j + 1
                    while k < len(content) and content[k].strip() and content[k].startswith('\t\t'):
                        nested_line = content[k]
                        nested_match = re.search(nested_operation_pattern, nested_line)
                        
                        if nested_match:
                            nested_name = nested_match.group(1)
                            nested_time = float(nested_match.group(2))
                            nested_self_time = float(nested_match.group(3)) if nested_match.group(3) else nested_time
                            
                            operation['nested_operations'].append({
                                'name': nested_name,
                                'time_ms': nested_time,
                                'self_time_ms': nested_self_time
                            })
                        
                        k += 1
                    
                    operations.append(operation)
                    j = k
                else:
                    j += 1
            
            # Add the detailed refresh entry
            refresh_details.append({
                'timestamp': timestamp,
                'timestamp_str': timestamp_str,
                'refresh_id': refresh_id,
                'total_time': total_time,
                'initiator': initiator,
                'summary': summary_data,
                'operations': operations
            })
    
    return refresh_details
