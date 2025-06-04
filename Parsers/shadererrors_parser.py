import re
import streamlit as st

from Utils import *

@st.cache_data
def parse_shader_errors_warnings(log_file):
    """Extract shader errors and warnings from the log file."""
    error_pattern = r"Shader error in '([^']+)': (.*)"
    warning_pattern = r"Shader warning in '([^']+)': (.*)"
    
    shader_issues = {
        'errors': [],
        'warnings': []
    }
    
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
        # Check for shader errors
        error_match = re.search(error_pattern, line)
        if error_match:
            shader_issues['errors'].append({
                'shader_name': error_match.group(1),
                'message': error_match.group(2).strip()
            })
            continue
        
        # Check for shader warnings
        warning_match = re.search(warning_pattern, line)
        if warning_match:
            shader_issues['warnings'].append({
                'shader_name': warning_match.group(1),
                'message': warning_match.group(2).strip()
            })
    
    return shader_issues
