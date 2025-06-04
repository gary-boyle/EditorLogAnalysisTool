import re
import pandas as pd
import streamlit as st

from datetime import datetime
from Utils import *

@st.cache_data
def parse_loading_times(log_file):
    """Parse Unity project loading time data from log file."""
    # Updated pattern to make timestamp optional
    loading_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?\[Project\] Loading completed in ([\d.]+) seconds'
    
    # Pattern to match project init time
    project_init_pattern = r'Project init time:\s+([\d.]+) seconds'
    
    # Pattern for scene opening time
    scene_opening_pattern = r'Scene opening time:\s+([\d.]+) seconds'
    
    # Patterns for sub-component times
    subcomponent_patterns = {
        'template_init': r'Template init time:\s+([\d.]+) seconds',
        'package_manager_init': r'Package Manager init time:\s+([\d.]+) seconds',
        'asset_db_init': r'Asset Database init time:\s+([\d.]+) seconds',
        'global_illumination_init': r'Global illumination init time:\s+([\d.]+) seconds',
        'assemblies_load': r'Assemblies load time:\s+([\d.]+) seconds',
        'unity_extensions_init': r'Unity extensions init time:\s+([\d.]+) seconds',
        'asset_db_refresh': r'Asset Database refresh time:\s+([\d.]+) seconds',
    }
    
    # Find all the loading entries (there might be multiple in a log)
    loading_data = []
    
    # Handle both file path strings and file-like objects
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            content = file.read()
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        content = log_file.read().decode('utf-8', errors='ignore')
    
    # Find all loading entries
    loading_entries = re.finditer(loading_pattern, content, re.MULTILINE)
    counter = 0
    
    for entry_match in loading_entries:
        timestamp_str = entry_match.group(1) if entry_match.lastindex >= 2 and entry_match.group(1) else f"Entry_{counter}"
        group_offset = 0 if timestamp_str.startswith("Entry_") else 0
        total_loading_time = float(entry_match.group(2))
        
        # Extract the block of text for this loading entry
        entry_start = max(0, entry_match.start() - 100)  # Include some context before
        entry_end = min(len(content), entry_match.end() + 1000)  # Include sufficient lines after
        entry_block = content[entry_start:entry_end]
        
        # Extract project init time
        project_init_match = re.search(project_init_pattern, entry_block)
        project_init_time = float(project_init_match.group(1)) if project_init_match else None
        
        # Extract scene opening time
        scene_opening_match = re.search(scene_opening_pattern, entry_block)
        scene_opening_time = float(scene_opening_match.group(1)) if scene_opening_match else None
        
        # Extract all sub-component times
        subcomponent_times = {}
        for key, pattern in subcomponent_patterns.items():
            match = re.search(pattern, entry_block)
            subcomponent_times[key] = float(match.group(1)) if match else None
        
        # Try to parse timestamp if it's a real timestamp
        timestamp = None
        if not timestamp_str.startswith("Entry_"):
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except:
                pass
        
        # Compile all data
        entry_data = {
            'timestamp': timestamp,
            'timestamp_str': timestamp_str,
            'total_loading_time': total_loading_time,
            'project_init_time': project_init_time,
            'scene_opening_time': scene_opening_time,
            **subcomponent_times
        }
        
        loading_data.append(entry_data)
        counter += 1
    
    return pd.DataFrame(loading_data) if loading_data else pd.DataFrame()
