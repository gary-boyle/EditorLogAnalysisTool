import re
import os
import pandas as pd
import streamlit as st

from datetime import datetime
from Utils import *

@st.cache_data
def parse_asset_imports(log_file):
    """Extract asset import data from the log file - optimized version."""
    import_data = []
    worker_data = {}
    worker_stats = {}
    
    # Precompile regex patterns for speed
    standard_pattern = re.compile(r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Start importing (.*?) using .* \((.*?)\) -> .* in (\d+\.\d+) seconds')
    worker_start_pattern = re.compile(r'\[Worker(\d+)\] Start importing (.*?) using')
    worker_importer_pattern = re.compile(r'\((.*?Importer)\)')
    worker_end_pattern = re.compile(r'\[Worker(\d+)\]  -> \(artifact id: \'.*?\'\) in (\d+\.\d+) seconds')
    
    # Process content based on input type
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            process_lines(file, standard_pattern, worker_start_pattern, worker_importer_pattern, 
                         worker_end_pattern, import_data, worker_data, worker_stats)
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        content = log_file.read().decode('utf-8', errors='ignore')
        lines = content.splitlines()
        process_lines(lines, standard_pattern, worker_start_pattern, worker_importer_pattern, 
                     worker_end_pattern, import_data, worker_data, worker_stats)

    # Create DataFrame
    df = pd.DataFrame(import_data) if import_data else pd.DataFrame()
    
    # Parse timestamps if they exist
    if not df.empty and 'timestamp_str' in df.columns and df['timestamp_str'].notna().any():
        df['timestamp'] = pd.to_datetime(df['timestamp_str'], format='%Y-%m-%dT%H:%M:%S.%fZ', errors='coerce')
    
    # Create worker stats dataframe and attach it as an attribute
    if worker_stats:
        worker_stats_df = pd.DataFrame([
            {'worker_id': k, 'imports': v['imports'], 'total_time': v['total_time']}
            for k, v in worker_stats.items()
        ])
        df.worker_stats = worker_stats_df
    
    return df

def process_lines(lines, standard_pattern, worker_start_pattern, worker_importer_pattern, 
                 worker_end_pattern, import_data, worker_data, worker_stats):
    """Process each line of the log file."""
    for line in lines:
        # Make sure line is a string
        if isinstance(line, bytes):
            line = line.decode('utf-8', errors='ignore')
            
        # Check for standard format (most common, so check first)
        match = standard_pattern.search(line)
        if match:
            timestamp_str = match.group(1)
            asset_path = match.group(2)
            importer_type = match.group(3)
            import_time = float(match.group(4))
            
            _, file_extension = os.path.splitext(asset_path)
            
            import_data.append({
                'timestamp_str': timestamp_str,
                'asset_path': asset_path,
                'asset_name': os.path.basename(asset_path),
                'file_extension': file_extension.lower(),
                'importer_type': importer_type,
                'import_time_seconds': import_time,
                'worker_id': None
            })
            continue
        
        # Check for worker start
        start_match = worker_start_pattern.search(line)
        if start_match:
            worker_id = start_match.group(1)
            asset_path = start_match.group(2)
            
            # Extract importer from this line
            importer_match = worker_importer_pattern.search(line)
            importer_type = importer_match.group(1) if importer_match else "UnknownImporter"
            
            # Store in worker data with a unique key based on asset path
            if worker_id not in worker_data:
                worker_data[worker_id] = []
            
            worker_data[worker_id].append({
                'asset_path': asset_path,
                'importer_type': importer_type
            })
            continue
        
        # Check for worker end
        end_match = worker_end_pattern.search(line)
        if end_match:
            worker_id = end_match.group(1)
            import_time = float(end_match.group(2))
            
            # Find corresponding start entry
            if worker_id in worker_data and worker_data[worker_id]:
                start_info = worker_data[worker_id].pop(0)  # Get earliest entry for this worker
                asset_path = start_info['asset_path']
                
                # Update worker stats
                if worker_id not in worker_stats:
                    worker_stats[worker_id] = {'imports': 0, 'total_time': 0}
                worker_stats[worker_id]['imports'] += 1
                worker_stats[worker_id]['total_time'] += import_time
                
                _, file_extension = os.path.splitext(asset_path)
                
                import_data.append({
                    'timestamp_str': None,
                    'asset_path': asset_path,
                    'asset_name': os.path.basename(asset_path),
                    'file_extension': file_extension.lower(),
                    'importer_type': start_info['importer_type'],
                    'import_time_seconds': import_time,
                    'worker_id': worker_id
                })