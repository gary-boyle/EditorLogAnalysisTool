import re
import streamlit as st

from Utils import *

@st.cache_data
def parse_il2cpp_processing(log_file):
    """Extract IL2CPP processing data from the log file."""
    # Patterns for IL2CPP entries
    patterns = [
        # EILPP format 1
        (r'\s+- EILPP\s*:\s*([\w\.]+)\s*:\s*:\s*(\d+)ms\s*\(~(\d+)ms\)',
         lambda m: {'assembly': m.group(1), 'total_time_ms': int(m.group(2)), 'self_time_ms': int(m.group(3))}),
        
        # EILPP format 2 - subprocess
        (r'\s+- EILPP\s*:\s*([\w\.]+)\s*:\s*([\w]+):\s*(\d+)ms',
         lambda m: {'is_subprocess': True, 'assembly': m.group(1), 'process': m.group(2), 'time_ms': int(m.group(3))}),
        
        # ILPostProcess format - [index/total time] or [time]
        (r'\[\s*(?:\d+/\d+\s+)?(\d+)s\]\s+ILPostProcess\s+(.*\.dll)',
         lambda m: {'assembly': extract_assembly_name(m.group(2)), 'total_time_ms': int(m.group(1)) * 1000, 'self_time_ms': int(m.group(1)) * 1000, 'process': 'ILPostProcess'})
    ]
    
    def extract_assembly_name(path):
        """Extract assembly name from file path."""
        match = re.search(r'[/\\]?([\w\.]+)\.dll', path)
        return match.group(1) if match else path
    
    il2cpp_data = []
    current_assembly = None
    assembly_steps = []
    
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
        # Try to match each pattern
        for pattern, handler in patterns:
            match = re.search(pattern, line)
            if match:
                result = handler(match)
                
                # Handle subprocess entries
                if result.get('is_subprocess', False):
                    if current_assembly and current_assembly['assembly'] == result['assembly']:
                        assembly_steps.append({
                            'assembly': result['assembly'],
                            'process': result['process'],
                            'time_ms': result['time_ms']
                        })
                    break
                
                # Handle main entries (save previous if exists)
                if current_assembly:
                    il2cpp_data.append({
                        'assembly': current_assembly['assembly'],
                        'total_time_ms': current_assembly['total_time_ms'],
                        'self_time_ms': current_assembly.get('self_time_ms', current_assembly['total_time_ms']),
                        'steps': assembly_steps
                    })
                
                # If this is an ILPostProcess entry, add it directly
                if result.get('process') == 'ILPostProcess':
                    il2cpp_data.append({
                        'assembly': result['assembly'],
                        'total_time_ms': result['total_time_ms'],
                        'self_time_ms': result['self_time_ms'],
                        'process': 'ILPostProcess',
                        'steps': []
                    })
                    current_assembly = None
                    assembly_steps = []
                else:
                    # Start a new assembly
                    current_assembly = result
                    assembly_steps = []
                break
    
    # Add the last assembly if exists
    if current_assembly:
        il2cpp_data.append({
            'assembly': current_assembly['assembly'],
            'total_time_ms': current_assembly['total_time_ms'],
            'self_time_ms': current_assembly.get('self_time_ms', current_assembly['total_time_ms']),
            'steps': assembly_steps
        })
    
    return il2cpp_data
