import re
import streamlit as st
from datetime import datetime

from Utils import *

@st.cache_data
def parse_domain_reloads(log_file):
    """Extract domain reload information from log file with proper timing extraction."""
    domain_reloads = []
    
    # Pattern to match domain reload profiling headers
    profiling_header = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Domain Reload Profiling: (\d+)ms'
    
    # Additional patterns for domain reload time (as backup)
    time_patterns = [
        r'Domain Reload completed in ([\d.]+) seconds',
        r'Finished resetting the current domain, in ([\d.]+) seconds',
        r'Reload completed in ([\d.]+)s'
    ]
    
    # Handle both file path strings and file-like objects
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            content = file.readlines()
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        content = log_file.read().decode('utf-8', errors='ignore').splitlines()
    
    i = 0
    while i < len(content):
        line = content[i]
        
        # Look for profiling header
        profiling_match = re.search(profiling_header, line)
        if profiling_match:
            timestamp_str = profiling_match.group(1) if profiling_match.group(1) else None
            profiling_time_ms = int(profiling_match.group(2))
            
            # Use the profiling time as the reset time (converting from ms to seconds)
            reset_time = profiling_time_ms / 1000.0
            
            # Parse timestamp if available
            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                except:
                    pass
            
            # Initialize domain reload entry
            reload_entry = {
                'timestamp': timestamp,
                'timestamp_str': timestamp_str if timestamp_str else f"Reload_{len(domain_reloads)}",
                'reset_time': reset_time,  # Use profiling time as default
                'profiling_time_ms': profiling_time_ms,
                'operations': []
            }
            
            # Look back for more specific domain reload time
            for j in range(i-1, max(0, i-20), -1):
                for pattern in time_patterns:
                    time_match = re.search(pattern, content[j])
                    if time_match:
                        try:
                            # Override with more specific time if found
                            reload_entry['reset_time'] = float(time_match.group(1))
                            break
                        except:
                            pass
                if time_match:
                    break
            
            # Parse operations with proper hierarchy
            operations = []
            op_stack = []
            
            # Move to next line after header
            j = i + 1
            while j < len(content) and j < i + 100:  # limit to 100 lines after header
                op_line = content[j].rstrip()
                
                # Check if we've reached the end of the profiling block
                if not op_line or not op_line.startswith('\t'):
                    break
                
                # Parse the operation line
                indent_level = len(re.match(r'^\t+', op_line).group(0))
                op_match = re.search(r'^\t+(.+?) \((\d+)ms\)$', op_line)
                
                if op_match:
                    name = op_match.group(1)
                    time_ms = int(op_match.group(2))
                    
                    op_entry = {
                        'name': name,
                        'time_ms': time_ms,
                        'indent_level': indent_level,
                        'children': []
                    }
                    
                    # Handle the hierarchy
                    while op_stack and op_stack[-1]['indent_level'] >= indent_level:
                        op_stack.pop()
                    
                    if op_stack:
                        op_stack[-1]['children'].append(op_entry)
                    else:
                        operations.append(op_entry)
                    
                    op_stack.append(op_entry)
                
                j += 1
            
            # Store operations and add to domain reloads
            reload_entry['operations'] = operations
            domain_reloads.append(reload_entry)
            
            # Continue parsing from after the operations block
            i = j
        else:
            i += 1
                
    # If we didn't find any domain reloads with the profiling header,
    # look for fallback patterns
    if not domain_reloads:
        # Join the content for simpler pattern matching
        full_content = '\n'.join(content)
        
        # Try each time pattern
        for pattern in time_patterns:
            complete_pattern = f'(?:(\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}\\.\\d+Z)\\|.*?\\|)?{pattern}'
            simple_reloads = re.finditer(complete_pattern, full_content)
            
            for idx, match in enumerate(simple_reloads):
                timestamp_str = match.group(1) if match.group(1) else None
                reset_time = float(match.group(2))
                
                # Parse timestamp if available
                timestamp = None
                if timestamp_str:
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    except:
                        pass
                
                domain_reloads.append({
                    'timestamp': timestamp,
                    'timestamp_str': timestamp_str if timestamp_str else f"Reload_{idx}",
                    'reset_time': reset_time,
                    'profiling_time_ms': reset_time * 1000,  # Convert seconds to ms
                    'operations': []
                })
    
    return domain_reloads
