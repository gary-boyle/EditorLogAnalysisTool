import re
import streamlit as st
import pandas as pd

from Utils.data_helpers import extract_float
from Utils import *

@st.cache_data    
def parse_shader_log(log_file_path):
    content = read_log_content(log_file_path)
    
    # Split into individual shader compilation entries
    entries = re.split(r'(?=Compiling shader)', content)
    entries = [entry.strip() for entry in entries if entry.strip()]
    
    parsed_data = []
    
    for entry in entries:
        shader_data = {}
        
        # Extract shader name and pass
        shader_match = re.search(r'Compiling shader "(.*?)" pass "(.*?)" \((.*?)\)', entry)
        if shader_match:
            shader_data['shader_name'] = shader_match.group(1)
            shader_data['pass_name'] = shader_match.group(2)
            shader_data['pass_type'] = shader_match.group(3)
        
        # Extract variant counts
        variant_patterns = {
            'full_variants': r'Full variant space:\s+(\d+)',
            'after_filtering': r'After settings filtering:\s+(\d+)',
            'after_builtin_stripping': r'After built-in stripping:\s+(\d+)',
            'after_scriptable_stripping': r'After scriptable stripping:\s+(\d+)'
        }
        
        for key, pattern in variant_patterns.items():
            match = re.search(pattern, entry)
            shader_data[key] = int(match.group(1)) if match else None
        
        # Extract timing information
        shader_data['processed_seconds'] = extract_float(entry, r'Processed in ([\d.]+) seconds')
        
        # Extract compilation results
        finished_match = re.search(r'finished in ([\d.]+) seconds.*?compiled (\d+) variants \(([\d.]+)s CPU time\), skipped (\d+) variants', entry)
        if finished_match:
            shader_data['compilation_seconds'] = float(finished_match.group(1))
            shader_data['compiled_variants'] = int(finished_match.group(2))
            shader_data['compilation_cpu_time'] = float(finished_match.group(3))
            shader_data['skipped_variants'] = int(finished_match.group(4))
        
        # Extract cache hits
        local_cache = re.search(r'Local cache hits (\d+) \(([\d.]+)s CPU time\)', entry)
        if local_cache:
            shader_data['local_cache_hits'] = int(local_cache.group(1))
            shader_data['local_cache_cpu_time'] = float(local_cache.group(2))
            
        remote_cache = re.search(r'remote cache hits (\d+) \(([\d.]+)s CPU time\)', entry)
        if remote_cache:
            shader_data['remote_cache_hits'] = int(remote_cache.group(1))
            shader_data['remote_cache_cpu_time'] = float(remote_cache.group(2))
        
        # Extract serialization time
        shader_data['serialization_seconds'] = extract_float(entry, r'Prepared data for serialisation in ([\d.]+)s')
        
        parsed_data.append(shader_data)
    
    return pd.DataFrame(parsed_data) if parsed_data else pd.DataFrame()
