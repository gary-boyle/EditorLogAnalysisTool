import re
import pandas as pd
import os
import json
from datetime import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def parse_shader_log(log_file_path):
    with open(log_file_path, 'r') as file:
        content = file.read()
    
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

def parse_asset_imports(log_file_path):
    # Updated regex pattern to make timestamp optional
    import_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Start importing (.*?) using .* \((.*?)\) -> .* in (\d+\.\d+) seconds'
    
    import_data = []
    
    with open(log_file_path, 'r') as file:
        content = file.read()
        
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

def parse_loading_times(log_file_path):
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
    
    with open(log_file_path, 'r') as file:
        content = file.read()
        
        # Find all loading entries
        loading_entries = re.finditer(loading_pattern, content)
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

def parse_build_report(log_file_path):
    # Updated pattern to make timestamp optional
    build_report_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Build Report'
    
    # Updated pattern to make timestamp optional
    category_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?(.*?)\s+(\d+\.?\d*)\s+(\w+)\s+(\d+\.?\d*)\%'
    
    # Updated pattern to make timestamp optional
    total_build_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Complete build size\s+(\d+\.?\d*)\s+(\w+)'
    
    build_data = []
    total_build_size = None
    total_build_unit = None
    
    with open(log_file_path, 'r') as file:
        content = file.read()
        
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

def parse_asset_pipeline_refresh(log_file_path):
    # Updated pattern to make timestamp optional
    refresh_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Asset Pipeline Refresh \(id=([^)]+)\): Total: ([\d.]+) seconds - Initiated by (.*?)$'
    
    refresh_data = []
    counter = 0
    
    with open(log_file_path, 'r') as file:
        content = file.read()
        
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

def parse_asset_pipeline_refresh_details(log_file_path):
    """Extract detailed breakdown of asset pipeline refresh operations."""
    # Pattern to match asset pipeline refresh entries with ID and time
    refresh_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Asset Pipeline Refresh \(id=([^)]+)\): Total: ([\d.]+) seconds - Initiated by (.*?)$'
    
    # Pattern for individual operations in the breakdown
    operation_pattern = r'^\t+([\w()]+): ([\d.]+)ms(?:\s+\(([\d.]+)ms without children\))?$'
    
    # Pattern for nested operations (additional indent level)
    nested_operation_pattern = r'^\t\t+([\w()]+): ([\d.]+)ms(?:\s+\(([\d.]+)ms without children\))?$'
    
    refresh_details = []
    
    with open(log_file_path, 'r') as file:
        content = file.readlines()
        
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

def parse_domain_reloads(log_file_path):
    """Extract domain reload information from log file."""
    # Pattern to match the beginning of a domain reload entry
    start_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?Mono: successfully reloaded assembly'
    
    # Pattern to match the domain reload time
    time_pattern = r'- Finished resetting the current domain, in ([\d.]+) seconds'
    
    # Pattern to match domain reload profiling header
    profiling_pattern = r'Domain Reload Profiling: (\d+)ms'
    
    domain_reloads = []
    counter = 0
    
    with open(log_file_path, 'r') as file:
        content = file.readlines()
        
        i = 0
        while i < len(content):
            line = content[i]
            
            # Look for the start of a domain reload entry
            start_match = re.search(start_pattern, line)
            if start_match:
                timestamp_str = start_match.group(1) if start_match.group(1) else f"DomainReload_{counter}"
                counter += 1
                
                # Parse timestamp if available
                timestamp = None
                if timestamp_str and not timestamp_str.startswith("DomainReload_"):
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    except:
                        pass
                
                # Look for the domain reset time in subsequent lines
                reset_time = None
                j = i + 1
                while j < len(content) and j < i + 10:  # Look ahead max 10 lines
                    time_match = re.search(time_pattern, content[j])
                    if time_match:
                        reset_time = float(time_match.group(1))
                        break
                    j += 1
                
                # Look for profiling header
                profiling_time = None
                profiling_start_line = None
                k = j + 1
                while k < len(content) and k < j + 10:  # Look ahead max 10 lines
                    prof_match = re.search(profiling_pattern, content[k])
                    if prof_match:
                        profiling_time = int(prof_match.group(1))
                        profiling_start_line = k
                        break
                    k += 1
                
                # Default position to continue from if no profiling data is found
                next_position = k + 1
                
                # If we found profiling data, parse the details
                operations = []
                if profiling_start_line is not None:
                    # Parse the profiling hierarchy
                    operation_stack = []
                    
                    l = profiling_start_line + 1
                    while l < len(content) and content[l].strip():
                        line = content[l]
                        
                        # Skip lines that don't contain profiling data
                        if not re.match(r'\t+', line):
                            break
                        
                        # Determine indent level (number of tabs)
                        indent = len(re.match(r'^\t+', line).group(0))
                        
                        # Extract operation name and time
                        parts = line.strip().split(' ')
                        if len(parts) >= 2 and parts[-1].endswith('ms)'):
                            op_name = ' '.join(parts[:-1])
                            op_time_str = parts[-1].strip('(ms)')
                            op_time = int(op_time_str) if op_time_str.isdigit() else float(op_time_str)
                            
                            # Create operation entry
                            operation = {
                                'name': op_name,
                                'time_ms': op_time,
                                'indent_level': indent,
                                'children': []
                            }
                            
                            # Handle the operation hierarchy
                            while operation_stack and operation_stack[-1]['indent_level'] >= indent:
                                operation_stack.pop()
                            
                            if operation_stack:
                                operation_stack[-1]['children'].append(operation)
                            else:
                                operations.append(operation)
                                
                            operation_stack.append(operation)
                            
                        l += 1
                    
                    # Update position to continue from
                    next_position = l
                
                # Create the domain reload entry
                domain_reload = {
                    'timestamp': timestamp,
                    'timestamp_str': timestamp_str,
                    'reset_time': reset_time,
                    'profiling_time_ms': profiling_time,
                    'operations': operations
                }
                
                domain_reloads.append(domain_reload)
                
                # Continue parsing from the next position
                i = next_position
            else:
                i += 1
    
    return domain_reloads

def parse_player_build_info(log_file_path):
    # Updated pattern to make timestamp optional
    build_info_pattern = r'(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|.*?\|)?##utp:(.*?)$'
    
    build_info_entries = []
    counter = 0
    
    with open(log_file_path, 'r') as file:
        content = file.read()
        
        # Find all player build info entries
        matches = re.finditer(build_info_pattern, content, re.MULTILINE)
        
        for match in matches:
            # Always extract timestamp from group 1 (which may be None if timestamp is missing)
            timestamp_str = match.group(1) if match.group(1) else f"Build_{counter}"
            
            # Always extract JSON data from the last group
            json_data = match.group(match.lastindex)  # This ensures we get the JSON data from the correct group
            
            if not json_data:
                # Skip if no JSON data was found
                continue
                
            # Try to parse the JSON data
            try:
                build_data = json.loads(json_data)
                
                # Check if this is a PlayerBuildInfo entry
                if build_data.get("type") == "PlayerBuildInfo":
                    # Get the build steps
                    steps = build_data.get("steps", [])
                    total_duration = build_data.get("duration", 0)
                    
                    # Try to parse timestamp if available
                    timestamp = None
                    if match.group(1):  # Only try to parse if we have a real timestamp
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                        except:
                            pass
                    
                    # Add the build info entry
                    build_info_entries.append({
                        'timestamp': timestamp,
                        'timestamp_str': timestamp_str,
                        'phase': build_data.get("phase", "Unknown"),
                        'version': build_data.get("version", "Unknown"),
                        'process_id': build_data.get("processId", "Unknown"),
                        'total_duration_ms': total_duration,
                        'total_duration_sec': total_duration / 1000,
                        'steps': steps
                    })
                    counter += 1
            except json.JSONDecodeError:
                # Skip invalid JSON
                continue
    
    return build_info_entries

def convert_to_mb(value, unit):
    """Convert a size value to MB"""
    unit = unit.lower()
    if unit == 'kb':
        return value / 1024
    elif unit == 'mb':
        return value
    elif unit == 'gb':
        return value * 1024
    elif unit == 'tb':
        return value * 1024 * 1024
    return value  # Default case

def extract_float(text, pattern):
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None

def format_time(seconds):
    """Format time in seconds to show both seconds and minutes."""
    if seconds is None or seconds < 0:
        return "N/A"
    minutes = seconds / 60
    return f"{seconds:.2f}s ({minutes:.1f} minutes)"

def visualize_shader_data(shader_df):
    st.header("Unity Shader Compilation Analytics")
    
    if shader_df.empty:
        st.warning("No shader compilation data found in the log.")
        return
    
    # Check if we have any essential shader compilation data
    has_compilation_data = 'compilation_seconds' in shader_df.columns or 'shader_name' in shader_df.columns
    
    if not has_compilation_data:
        st.warning("No shader compilation performance data found in the log.")
        return
    
    # Sort dataframe by compilation time in descending order if the column exists
    if 'compilation_seconds' in shader_df.columns:
        sorted_df = shader_df.sort_values('compilation_seconds', ascending=False)
    else:
        sorted_df = shader_df  # No sorting if column doesn't exist
        st.info("Compilation time data not found. Some visualizations will be limited.")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Shaders", len(shader_df))
    with col2:
        total_compilation_time = shader_df['compilation_seconds'].sum() if 'compilation_seconds' in shader_df.columns else "N/A"
        st.metric("Total Compilation Time", f"{total_compilation_time:.2f}s" if isinstance(total_compilation_time, (int, float)) else total_compilation_time)
    with col3:
        total_cpu_time = shader_df['compilation_cpu_time'].sum() if 'compilation_cpu_time' in shader_df.columns else "N/A"
        st.metric("Total CPU Time", f"{total_cpu_time:.2f}s" if isinstance(total_cpu_time, (int, float)) else total_cpu_time)
    with col4:
        total_variants = int(shader_df['compiled_variants'].sum()) if 'compiled_variants' in shader_df.columns else "N/A"
        st.metric("Total Variants Compiled", total_variants)
    
    # Only show visualization if we have compilation time and shader name data
    if 'compilation_seconds' in shader_df.columns and 'shader_name' in shader_df.columns:
        # Compilation time by shader
        st.subheader("Compilation Time by Shader")
        
        fig = px.bar(
            sorted_df,
            x='shader_name',
            y='compilation_seconds',
            color='pass_name' if 'pass_name' in sorted_df.columns else None,
            hover_data=['compiled_variants', 'compilation_cpu_time'] if all(col in sorted_df.columns for col in ['compiled_variants', 'compilation_cpu_time']) else None,
            labels={'compilation_seconds': 'Compilation Time (s)', 'shader_name': 'Shader Name'},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    elif 'shader_name' in shader_df.columns:
        st.info("Shader names found but compilation time data is missing.")
    
    # NEW: Add compilation time by pass name if available
    if 'pass_name' in shader_df.columns and 'compilation_seconds' in shader_df.columns and not shader_df['pass_name'].isna().all():
        st.subheader("Compilation Time by Pass Name")
        
        # Group by pass name and sum compilation times
        pass_name_times = shader_df.groupby('pass_name').agg(
            total_time=('compilation_seconds', 'sum'),
            avg_time=('compilation_seconds', 'mean'),
            count=('compilation_seconds', 'count'),
            total_variants=('compiled_variants', 'sum') if 'compiled_variants' in shader_df.columns else (None, None)
        ).reset_index().sort_values('total_time', ascending=False)
        
        # Create formatted columns for display
        pass_name_times['avg_time_formatted'] = pass_name_times['avg_time'].apply(lambda x: f"{x:.3f}s")
        pass_name_times['total_time_formatted'] = pass_name_times['total_time'].apply(lambda x: f"{x:.2f}s")
        
        # Bar chart of compilation time by pass name
        fig = px.bar(
            pass_name_times,
            x='pass_name',
            y='total_time',
            text=pass_name_times['count'],
            labels={'pass_name': 'Pass Name', 'total_time': 'Total Compilation Time (s)', 'count': 'Shader Count'},
            height=400,
            color='count'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Display the detailed table
        with st.expander("View Pass Name Compilation Details"):
            display_cols = ['pass_name', 'count', 'total_time_formatted', 'avg_time_formatted']
            if 'total_variants' in pass_name_times.columns and not pass_name_times['total_variants'].isna().all():
                display_cols.append('total_variants')
            st.dataframe(pass_name_times[display_cols])
    
    # Add compilation time by pass type if available
    if 'pass_type' in shader_df.columns and 'compilation_seconds' in shader_df.columns and not shader_df['pass_type'].isna().all():
        st.subheader("Compilation Time by Pass Type")
        
        # Group by pass type and sum compilation times
        pass_type_times = shader_df.groupby('pass_type').agg(
            total_time=('compilation_seconds', 'sum'),
            avg_time=('compilation_seconds', 'mean'),
            count=('compilation_seconds', 'count'),
            total_variants=('compiled_variants', 'sum') if 'compiled_variants' in shader_df.columns else (None, None)
        ).reset_index().sort_values('total_time', ascending=False)
        
        # Create a more detailed table
        pass_type_times['avg_time_formatted'] = pass_type_times['avg_time'].apply(lambda x: f"{x:.3f}s")
        pass_type_times['total_time_formatted'] = pass_type_times['total_time'].apply(lambda x: f"{x:.2f}s")
        
        # Bar chart of compilation time by pass type
        fig = px.bar(
            pass_type_times,
            x='pass_type',
            y='total_time',
            text=pass_type_times['count'],
            labels={'pass_type': 'Pass Type', 'total_time': 'Total Compilation Time (s)', 'count': 'Shader Count'},
            height=400,
            color='count'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Display the detailed table
        with st.expander("View Pass Type Compilation Details"):
            display_cols = ['pass_type', 'count', 'total_time_formatted', 'avg_time_formatted']
            if 'total_variants' in pass_type_times.columns and not pass_type_times['total_variants'].isna().all():
                display_cols.append('total_variants')
            st.dataframe(pass_type_times[display_cols])
    
    # Only show variant reduction if we have the necessary columns
    variant_columns = ['full_variants', 'after_filtering', 'after_builtin_stripping', 'after_scriptable_stripping']
    if 'shader_name' in shader_df.columns and any(col in shader_df.columns for col in variant_columns):
        available_variants = [col for col in variant_columns if col in shader_df.columns]
        
        if available_variants:
            # Variant reduction pipeline
            st.subheader("Shader Variant Reduction")
            variant_df = sorted_df.melt(
                id_vars=['shader_name', 'pass_name'] if 'pass_name' in sorted_df.columns else ['shader_name'],
                value_vars=available_variants,
                var_name='Pipeline Stage',
                value_name='Variant Count'
            )
            
            fig = px.line(
                variant_df,
                x='Pipeline Stage',
                y='Variant Count',
                color='shader_name',
                markers=True,
                line_shape='linear',
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Only show cache analysis if we have the necessary columns
    cache_columns = ['local_cache_hits', 'remote_cache_hits', 'compiled_variants']
    cpu_columns = ['local_cache_cpu_time', 'remote_cache_cpu_time', 'compilation_cpu_time']
    
    if any(col in shader_df.columns for col in cache_columns) or any(col in shader_df.columns for col in cpu_columns):
        # Cache effectiveness
        st.subheader("Cache Hit Analysis")
        col1, col2 = st.columns(2)
        
        if all(col in shader_df.columns for col in cache_columns):
            with col1:
                cache_data = {
                    'Category': ['Local Cache Hits', 'Remote Cache Hits', 'Compiled Variants'],
                    'Count': [
                        shader_df['local_cache_hits'].sum(),
                        shader_df['remote_cache_hits'].sum(),
                        shader_df['compiled_variants'].sum()
                    ]
                }
                fig = px.pie(cache_data, values='Count', names='Category')
                st.plotly_chart(fig, use_container_width=True)
        
        if all(col in shader_df.columns for col in cpu_columns):
            with col2:
                # CPU time distribution
                cpu_data = {
                    'Category': ['Local Cache CPU', 'Remote Cache CPU', 'Compilation CPU'],
                    'Time': [
                        shader_df['local_cache_cpu_time'].sum(),
                        shader_df['remote_cache_cpu_time'].sum(),
                        shader_df['compilation_cpu_time'].sum()
                    ]
                }
                fig = px.pie(cpu_data, values='Time', names='Category')
                st.plotly_chart(fig, use_container_width=True)
    
    # Raw data table with any data we have
    if not shader_df.empty:
        with st.expander("View Shader Compilation Raw Data"):
            st.dataframe(sorted_df)

def visualize_asset_imports(import_df):
    st.header("Unity Asset Import Analytics")
    
    if import_df.empty:
        st.warning("No asset import data found in the log.")
        return
    
    # Sort by import time descending
    sorted_df = import_df.sort_values('import_time_seconds', ascending=False)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Assets Imported", len(import_df))
    with col2:
        st.metric("Total Import Time", f"{import_df['import_time_seconds'].sum():.2f}s")
    with col3:
        st.metric("Average Import Time", f"{import_df['import_time_seconds'].mean():.4f}s")
    
    # Top slowest imports
    st.subheader("Top 10 Slowest Asset Imports")
    top_n = min(20, len(sorted_df))
    top_imports = sorted_df.head(top_n)
    
    fig = px.bar(
        top_imports,
        x='asset_name',
        y='import_time_seconds',
        color='importer_type',
        hover_data=['asset_path', 'file_extension'],
        labels={'import_time_seconds': 'Import Time (s)', 'asset_name': 'Asset Name'},
        height=500
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Import time by file extension
    if not sorted_df['file_extension'].empty:
        st.subheader("Import Time by File Type")
        ext_df = sorted_df.groupby('file_extension').agg(
            total_time=('import_time_seconds', 'sum'),
            count=('import_time_seconds', 'count'),
            avg_time=('import_time_seconds', 'mean')
        ).reset_index().sort_values('total_time', ascending=False)
        
        fig = px.bar(
            ext_df,
            x='file_extension',
            y='total_time',
            color='count',
            text='count',
            labels={
                'file_extension': 'File Extension', 
                'total_time': 'Total Import Time (s)',
                'count': 'Number of Files'
            },
            height=500
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    # Importer type distribution
    st.subheader("Assets by Importer Type")
    importer_counts = sorted_df['importer_type'].value_counts().reset_index()
    importer_counts.columns = ['Importer Type', 'Count']
    
    fig = px.pie(
        importer_counts, 
        values='Count', 
        names='Importer Type',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Distribution of import times
    st.subheader("Distribution of Import Times")
    fig = px.histogram(
        sorted_df,
        x='import_time_seconds',
        nbins=50,
        labels={'import_time_seconds': 'Import Time (s)'},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw data table
    with st.expander("View Asset Import Raw Data"):
        st.dataframe(sorted_df)

def visualize_loading_times(loading_df):
    st.header("Unity Project Loading Times")
    
    if loading_df.empty:
        st.warning("No project loading data found in the log.")
        return
    
    # If there are multiple loading entries, show a selector
    if len(loading_df) > 1:
        selected_index = st.selectbox(
            "Select loading entry:", 
            range(len(loading_df)), 
            format_func=lambda i: f"Entry {i+1}: {loading_df.iloc[i]['timestamp_str']}"
        )
        entry = loading_df.iloc[selected_index]
    else:
        entry = loading_df.iloc[0]
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Loading Time", f"{entry['total_loading_time']:.3f}s")
    with col2:
        st.metric("Project Init Time", f"{entry['project_init_time']:.3f}s")
    with col3:
        st.metric("Scene Opening Time", f"{entry['scene_opening_time']:.3f}s" if entry['scene_opening_time'] is not None else "N/A")
    
    # Create waterfall chart for project init breakdown
    st.subheader("Project Initialization Breakdown")
    
    # Prepare data for waterfall chart
    subcomponents = [
        'template_init', 'package_manager_init', 'asset_db_init',
        'global_illumination_init', 'assemblies_load',
        'unity_extensions_init', 'asset_db_refresh'
    ]
    
    subcomponent_names = {
        'template_init': 'Template Init',
        'package_manager_init': 'Package Manager Init',
        'asset_db_init': 'Asset Database Init',
        'global_illumination_init': 'Global Illumination Init',
        'assemblies_load': 'Assemblies Load',
        'unity_extensions_init': 'Unity Extensions Init',
        'asset_db_refresh': 'Asset Database Refresh'
    }
    
    # Filter out None values and create data for the chart
    chart_data = []
    for component in subcomponents:
        if entry[component] is not None and entry[component] > 0:
            chart_data.append({
                'Component': subcomponent_names.get(component, component),
                'Time': entry[component]
            })
    
    # Sort by time (descending)
    chart_df = pd.DataFrame(chart_data).sort_values('Time', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        chart_df,
        x='Component',
        y='Time',
        labels={'Time': 'Time (seconds)'},
        title="Component Initialization Times",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Pie chart showing time distribution
    st.subheader("Project Init Time Distribution")
    fig = px.pie(
        chart_df,
        values='Time',
        names='Component',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Stacked waterfall chart to visualize the breakdown of total time
    st.subheader("Loading Time Composition")
    
    # Calculate the "other" time that isn't accounted for in the subcomponents
    accounted_time = sum(entry[comp] for comp in subcomponents if entry[comp] is not None)
    other_init_time = entry['project_init_time'] - accounted_time if entry['project_init_time'] is not None else 0
    
    # Create data for the waterfall chart
    waterfall_data = [
        {'phase': 'Total Loading Time', 'time': entry['total_loading_time'], 'type': 'total'}
    ]
    
    # Add all components of project init time
    for component in subcomponents:
        if entry[component] is not None and entry[component] > 0:
            waterfall_data.append({
                'phase': subcomponent_names.get(component, component),
                'time': entry[component],
                'type': 'project_init'
            })
    
    # Add other init time if significant
    if other_init_time > 0.01:
        waterfall_data.append({
            'phase': 'Other Init',
            'time': other_init_time,
            'type': 'project_init'
        })
    
    # Add scene opening time
    if entry['scene_opening_time'] is not None:
        waterfall_data.append({
            'phase': 'Scene Opening',
            'time': entry['scene_opening_time'],
            'type': 'scene'
        })
    
    # Create a DataFrame for easier manipulation
    waterfall_df = pd.DataFrame(waterfall_data)
    
    # Get top components by time for the waterfall chart (limited to 10 to avoid clutter)
    top_components = waterfall_df[waterfall_df['type'] != 'total'].nlargest(10, 'time')
    
    # Create the waterfall chart
    fig = go.Figure(go.Waterfall(
        name="Loading Process",
        orientation="v",
        measure=["absolute"] + ["relative"] * len(top_components),
        x=[item['phase'] for item in [waterfall_data[0]] + top_components.to_dict('records')],
        y=[item['time'] for item in [waterfall_data[0]] + top_components.to_dict('records')],
        connector={"line":{"color":"rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title="Loading Time Waterfall Chart",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw data in a well-formatted table
    with st.expander("View Loading Time Details"):
        # Create a nicer display of the loading time details
        display_data = {
            "Total Loading Time": f"{entry['total_loading_time']:.3f}s",
            "Project Init Time": f"{entry['project_init_time']:.3f}s",
            "Scene Opening Time": f"{entry['scene_opening_time']:.3f}s" if entry['scene_opening_time'] is not None else "N/A"
        }
        
        # Add all subcomponents
        for comp in subcomponents:
            if entry[comp] is not None:
                display_data[subcomponent_names.get(comp, comp)] = f"{entry[comp]:.3f}s"
        
        # Calculate and display "other" time
        if other_init_time > 0.01:
            display_data["Other Init Time"] = f"{other_init_time:.3f}s"
        
        # Convert to DataFrame for easier display
        display_df = pd.DataFrame(list(display_data.items()), columns=["Metric", "Value"])
        st.table(display_df)

def visualize_build_report(build_df, total_size, total_unit):
    st.header("Unity Build Size Report")
    
    if build_df.empty:
        st.warning("No build report data found in the log.")
        return
    
    # Sort by size descending
    sorted_df = build_df.sort_values('size_in_mb', ascending=False)
    
    # Convert total size to readable format
    total_size_readable = f"{total_size} {total_unit}"
    
    # Calculate total user assets size
    user_assets_row = build_df[build_df['category'] == 'Total User Assets']
    if not user_assets_row.empty:
        user_assets_size = f"{user_assets_row.iloc[0]['size_value']} {user_assets_row.iloc[0]['size_unit']}"
    else:
        user_assets_size = "N/A"
    
    # Summary metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Complete Build Size", total_size_readable)
    with col2:
        st.metric("User Assets Size", user_assets_size)
    
    # Filter out summary rows for visualization
    categories_to_exclude = ['Total User Assets', 'Complete build size']
    vis_df = sorted_df[~sorted_df['category'].isin(categories_to_exclude)]
    
    # Bar chart showing asset sizes
    st.subheader("Asset Size by Category")
    fig = px.bar(
        vis_df,
        x='category',
        y='size_in_mb',
        text=vis_df.apply(lambda row: f"{row['size_value']} {row['size_unit']}", axis=1),
        labels={'category': 'Asset Category', 'size_in_mb': 'Size (MB)'},
        height=500,
        color='percentage'
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Pie chart showing percentage breakdown
    st.subheader("Asset Size Distribution")
    fig = px.pie(
        vis_df,
        values='percentage',
        names='category',
        height=500,
        hover_data=['size_value', 'size_unit']
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    
    # Treemap visualization
    st.subheader("Asset Size Treemap")
    fig = px.treemap(
        vis_df,
        path=['category'],
        values='size_in_mb',
        color='size_in_mb',
        hover_data=['size_value', 'size_unit', 'percentage'],
        color_continuous_scale='RdBu',
        height=500
    )
    fig.update_traces(textinfo="label+value+percent parent")
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw data in a well-formatted table
    with st.expander("View Build Report Details"):
        display_df = sorted_df.copy()
        display_df['size'] = display_df.apply(lambda row: f"{row['size_value']} {row['size_unit']}", axis=1)
        display_df['percentage'] = display_df['percentage'].apply(lambda x: f"{x}%")
        st.dataframe(display_df[['category', 'size', 'percentage']])

def visualize_pipeline_refreshes(refresh_df, log_file_path):
    st.header("Unity Asset Pipeline Refreshes")
    
    if refresh_df.empty:
        st.warning("No asset pipeline refresh data found in the log.")
        return
    
    # Sort by refresh time descending
    sorted_df = refresh_df.sort_values('total_time', ascending=False)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pipeline Refreshes", len(refresh_df))
    with col2:
        st.metric("Total Refresh Time", f"{refresh_df['total_time'].sum():.3f}s")
    with col3:
        st.metric("Average Refresh Time", f"{refresh_df['total_time'].mean():.4f}s")
    
    # Check if we have detailed refresh data
    refresh_details = []  # We'll fetch this when a specific refresh is selected
    
    # Top slowest refreshes
    st.subheader("Slowest Asset Pipeline Refreshes")
    top_n = min(20, len(sorted_df))
    top_refreshes = sorted_df.head(top_n)
    
    fig = px.bar(
        top_refreshes,
        x=top_refreshes.index,
        y='total_time',
        hover_data=['refresh_id', 'initiator'],
        labels={'total_time': 'Refresh Time (s)', 'index': 'Refresh #'},
        height=500,
        color='initiator'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Add option to view detailed breakdown for the selected refresh
    st.subheader("Detailed Refresh Analysis")
    
    # Let user select a refresh to analyze
    selected_refresh_idx = st.selectbox(
        "Select a refresh to analyze in detail:",
        range(len(sorted_df)),
        format_func=lambda i: f"Refresh #{i}: {sorted_df.iloc[i]['initiator']} ({sorted_df.iloc[i]['total_time']:.2f}s)"
    )
    
    if st.button("Analyze Selected Refresh"):
        with st.spinner("Analyzing asset pipeline refresh details..."):
            # Get the refresh ID of the selected refresh
            selected_refresh_id = sorted_df.iloc[selected_refresh_idx]['refresh_id']
            
            # Parse the detailed breakdown for all refreshes
            all_refresh_details = parse_asset_pipeline_refresh_details(log_file_path)
            
            # Find the details for the selected refresh
            selected_refresh_details = next((r for r in all_refresh_details if r['refresh_id'] == selected_refresh_id), None)
            
            if selected_refresh_details:
                visualize_refresh_details(selected_refresh_details)
            else:
                st.warning("Detailed breakdown not found for this refresh. The log may not contain detailed timing information.")
    
    # Time by initiator
    st.subheader("Refresh Time by Initiator")
    initiator_df = sorted_df.groupby('initiator').agg(
        total_time=('total_time', 'sum'),
        count=('total_time', 'count'),
        avg_time=('total_time', 'mean')
    ).reset_index().sort_values('total_time', ascending=False)
    
    fig = px.bar(
        initiator_df,
        x='initiator',
        y='total_time',
        color='count',
        text='count',
        labels={
            'initiator': 'Initiator', 
            'total_time': 'Total Refresh Time (s)',
            'count': 'Number of Refreshes'
        },
        height=500
    )
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Distribution of refresh times
    st.subheader("Distribution of Refresh Times")
    fig = px.histogram(
        sorted_df,
        x='total_time',
        nbins=30,
        labels={'total_time': 'Refresh Time (s)'},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Pie chart showing distribution by initiator
    st.subheader("Refresh Count by Initiator")
    initiator_counts = sorted_df['initiator'].value_counts().reset_index()
    initiator_counts.columns = ['Initiator', 'Count']
    
    fig = px.pie(
        initiator_counts, 
        values='Count', 
        names='Initiator',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw data table
    with st.expander("View Asset Pipeline Refresh Raw Data"):
        st.dataframe(sorted_df[['timestamp_str', 'refresh_id', 'initiator', 'total_time']])

def visualize_refresh_details(refresh_entry):
    st.header("Detailed Asset Pipeline Refresh Analysis")
    
    # Display metadata about the refresh operation
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Refresh Time", f"{refresh_entry['total_time']:.2f}s")
    with col2:
        st.metric("Initiator", refresh_entry['initiator'])
    
    # Display summary if available
    if refresh_entry['summary']:
        with st.expander("Refresh Summary", expanded=True):
            for key, value in refresh_entry['summary'].items():
                st.write(f"**{key}:** {value}")
    
    # Create a dataframe of top-level operations
    operations = []
    for op in refresh_entry['operations']:
        operations.append({
            'Operation': op['name'],
            'Time (ms)': op['time_ms'],
            'Time (s)': op['time_ms'] / 1000,
            'Self Time (ms)': op['self_time_ms'],
            'Self Time (s)': op['self_time_ms'] / 1000,
            'Children Time (ms)': op['time_ms'] - op['self_time_ms'],
            'Children Time (s)': (op['time_ms'] - op['self_time_ms']) / 1000,
            'Percentage': (op['time_ms'] / (refresh_entry['total_time'] * 1000)) * 100
        })
    
    op_df = pd.DataFrame(operations)
    
    if not op_df.empty:
        # Sort by time (descending)
        op_df = op_df.sort_values('Time (ms)', ascending=False)
        
        # Display top operations bar chart
        st.subheader("Top Operations by Time")
        
        fig = px.bar(
            op_df.head(10),
            y='Operation',
            x='Time (s)',
            orientation='h',
            text=op_df.head(10)['Percentage'].apply(lambda x: f"{x:.1f}%"),
            labels={'Time (s)': 'Time (seconds)'},
            height=500,
            color='Percentage',
            color_continuous_scale='Viridis'
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Display self vs children time stacked bar chart
        st.subheader("Self Time vs. Children Time")
        
        # Prepare data for stacked bar chart
        stack_data = []
        for op in op_df.head(10).to_dict('records'):
            stack_data.append({
                'Operation': op['Operation'],
                'Time (s)': op['Self Time (s)'],
                'Type': 'Self Time'
            })
            if op['Children Time (s)'] > 0:
                stack_data.append({
                    'Operation': op['Operation'],
                    'Time (s)': op['Children Time (s)'],
                    'Type': 'Children Time'
                })
        
        stack_df = pd.DataFrame(stack_data)
        
        fig = px.bar(
            stack_df,
            x='Time (s)',
            y='Operation',
            color='Type',
            barmode='stack',
            orientation='h',
            height=500,
            labels={'Time (s)': 'Time (seconds)'},
            color_discrete_map={'Self Time': '#636EFA', 'Children Time': '#EF553B'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show timeline visualization
        st.subheader("Operation Timeline")
        
        # Create a dataframe for timeline visualization
        timeline_data = []
        total_time = 0
        
        # Assume operations are sequential for visualization purposes
        for op in refresh_entry['operations']:
            timeline_data.append({
                'Operation': op['name'],
                'Start': total_time / 1000,
                'End': (total_time + op['time_ms']) / 1000,
                'Duration': op['time_ms'] / 1000,
                'Percentage': (op['time_ms'] / (refresh_entry['total_time'] * 1000)) * 100
            })
            total_time += op['time_ms']
        
        timeline_df = pd.DataFrame(timeline_data)
        
        fig = px.timeline(
            timeline_df,
            x_start='Start',
            x_end='End',
            y='Operation',
            color='Percentage',
            labels={
                'Start': 'Time (s)',
                'End': 'Time (s)',
                'Percentage': 'Percentage of Total Time'
            },
            height=600,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            xaxis_title="Time (seconds)",
            yaxis_title="Operation"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display nested operations for the longest operation
        longest_op = op_df.iloc[0]
        longest_op_name = longest_op['Operation']
        
        longest_op_data = next((op for op in refresh_entry['operations'] if op['name'] == longest_op_name), None)
        
        if longest_op_data and longest_op_data['nested_operations']:
            st.subheader(f"Breakdown of '{longest_op_name}' Operation")
            
            nested_ops = []
            for nested_op in longest_op_data['nested_operations']:
                nested_ops.append({
                    'Operation': nested_op['name'],
                    'Time (ms)': nested_op['time_ms'],
                    'Time (s)': nested_op['time_ms'] / 1000,
                    'Self Time (ms)': nested_op['self_time_ms'],
                    'Self Time (s)': nested_op['self_time_ms'] / 1000,
                    'Percentage': (nested_op['time_ms'] / longest_op_data['time_ms']) * 100
                })
            
            nested_df = pd.DataFrame(nested_ops).sort_values('Time (ms)', ascending=False)
            
            fig = px.bar(
                nested_df,
                y='Operation',
                x='Time (s)',
                orientation='h',
                text=nested_df['Percentage'].apply(lambda x: f"{x:.1f}%"),
                labels={'Time (s)': 'Time (seconds)'},
                height=400,
                color='Percentage',
                color_continuous_scale='Inferno'
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        # Raw data in a well-formatted table
        with st.expander("View All Operations Data"):
            st.dataframe(op_df.style.format({
                'Time (s)': '{:.3f}',
                'Self Time (s)': '{:.3f}',
                'Children Time (s)': '{:.3f}',
                'Percentage': '{:.2f}%'
            }))

def visualize_player_build_info(build_info_entries):
    st.header("Unity Player Build Performance")
    
    if not build_info_entries:
        st.warning("No player build information found in the log.")
        return
    
    # If there are multiple build entries, show a selector
    if len(build_info_entries) > 1:
        selected_index = st.selectbox(
            "Select build entry:", 
            range(len(build_info_entries)), 
            format_func=lambda i: f"Build {i+1}: {build_info_entries[i]['timestamp_str']}"
        )
        build_info = build_info_entries[selected_index]
    else:
        build_info = build_info_entries[0]
    
    # Summary metrics
    total_duration_sec = build_info['total_duration_sec']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Build Time", format_time(total_duration_sec))
    with col2:
        st.metric("Build Phase", build_info['phase'])
    with col3:
        st.metric("Build Steps", len(build_info['steps']))
    
    # Create dataframe from steps
    steps_data = []
    for step in build_info['steps']:
        duration_ms = step.get('duration', 0)
        description = step.get('description', 'Unknown')
        duration_sec = duration_ms / 1000  # Convert to seconds
        percentage = (duration_ms / build_info['total_duration_ms']) * 100
        
        steps_data.append({
            'description': description,
            'duration_ms': duration_ms,
            'duration_sec': duration_sec,
            'percentage': percentage
        })
    
    steps_df = pd.DataFrame(steps_data)
    
    if steps_df.empty:
        st.warning("No build step data available.")
        return
    
    # Sort by duration (descending)
    sorted_steps_df = steps_df.sort_values('duration_ms', ascending=False)
    
    # Bar chart of build steps by duration
    st.subheader("Build Steps by Duration")
    
    fig = px.bar(
        sorted_steps_df,
        y='description',
        x='duration_sec',
        orientation='h',
        text=sorted_steps_df.apply(lambda row: f"{row['percentage']:.1f}%", axis=1),
        labels={'description': 'Build Step', 'duration_sec': 'Duration (seconds)'},
        height=600,
        color='percentage'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Pie chart of build step percentages
    st.subheader("Build Time Distribution")
    
    # Filter to top steps to avoid cluttering the pie chart
    top_steps = sorted_steps_df.head(10).copy()
    
    # Calculate percentage for clarity in the pie chart
    top_steps['percentage_formatted'] = top_steps['percentage'].apply(lambda x: f"{x:.1f}%")
    
    fig = px.pie(
        top_steps,
        values='duration_ms',
        names='description',
        height=500,
        hover_data=['duration_sec', 'percentage_formatted']
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    
    # Timeline visualization
    st.subheader("Build Timeline")
    
    # Check if we have enough data points for a timeline
    if len(steps_df) < 2:
        st.info("At least two build steps are needed to create a timeline visualization.")
    else:
        # Create a proper timeline dataframe with start and end times
        cumulative_time = 0
        timeline_data = []
        
        # Fix: Ensure steps are in original order and properly formatted
        for i, step in enumerate(build_info['steps']):
            # Get step data with proper fallbacks
            description = step.get('description', f"Step {i+1}")
            # Make sure description is not empty
            if not description or description.strip() == "":
                description = f"Step {i+1}"
                
            duration_ms = float(step.get('duration', 0))  # Ensure it's a float
            duration_sec = duration_ms / 1000
            
            # Skip steps with zero duration to avoid timeline issues
            if duration_sec <= 0:
                continue
                
            start_time = cumulative_time
            end_time = cumulative_time + duration_sec
            
            timeline_data.append({
                'description': description,
                'start_time': start_time,
                'end_time': end_time,
                'duration_sec': duration_sec
            })
            
            # Update cumulative time for next step
            cumulative_time = end_time
        
        timeline_df = pd.DataFrame(timeline_data)
        
        # If we still have timeline data after filtering
        if not timeline_df.empty:
            fig = px.timeline(
                timeline_df,
                x_start='start_time',
                x_end='end_time',
                y='description',
                color='duration_sec',
                labels={
                    'start_time': 'Time (seconds)',
                    'end_time': 'Time (seconds)',
                    'duration_sec': 'Duration (seconds)'
                },
                height=600
            )
            
            # Improve the layout
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                xaxis_title="Time (seconds)",
                yaxis_title="Build Step"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not create timeline: no valid duration data in build steps.")
    
    # Raw data in a well-formatted table
    with st.expander("View Build Step Details"):
        display_df = sorted_steps_df.copy()
        display_df['duration'] = display_df['duration_sec'].apply(lambda x: f"{x:.3f}s")
        display_df['percentage'] = display_df['percentage'].apply(lambda x: f"{x:.2f}%")
        st.dataframe(display_df[['description', 'duration', 'percentage']])

def visualize_domain_reloads(log_file_path):
    st.header("Unity Domain Reload Analysis")
    
    # Parse domain reload entries
    domain_reloads = parse_domain_reloads(log_file_path)
    
    if not domain_reloads:
        st.warning("No domain reload data found in the log.")
        return
    
    # Create summary metrics - ensure we handle None values
    total_time = sum((reload.get('reset_time', 0) or 0) for reload in domain_reloads)
    avg_time = total_time / len(domain_reloads) if domain_reloads else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Domain Reloads", len(domain_reloads))
    with col2:
        st.metric("Total Reload Time", f"{total_time:.2f}s")
    with col3:
        st.metric("Average Reload Time", f"{avg_time:.2f}s")
    
    # Create a basic overview of all domain reloads
    reload_data = []
    for i, reload in enumerate(domain_reloads):
        reload_data.append({
            'index': i,
            'timestamp': reload.get('timestamp_str', f"Reload {i}"),
            'reset_time': reload.get('reset_time', 0) or 0,  # Handle None values
            'profiling_time_ms': reload.get('profiling_time_ms', 0) or 0  # Handle None values
        })
    
    reload_df = pd.DataFrame(reload_data)
    
    # Bar chart of domain reload times
    st.subheader("Domain Reload Times")
    
    fig = px.bar(
        reload_df,
        x='index',
        y='reset_time',
        labels={'reset_time': 'Reset Time (seconds)', 'index': 'Domain Reload #'},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Add option to select a specific domain reload
    st.subheader("Detailed Domain Reload Analysis")
    
    selected_reload_idx = st.selectbox(
        "Select a domain reload to analyze in detail:",
        range(len(domain_reloads)),
        format_func=lambda i: f"Reload #{i}: {domain_reloads[i].get('timestamp_str')} ({domain_reloads[i].get('reset_time', 0) or 0:.2f}s)"
    )
    
    if st.button("Analyze Selected Domain Reload"):
        with st.spinner("Analyzing domain reload details..."):
            # Visualize the selected domain reload
            visualize_domain_reload_details(domain_reloads[selected_reload_idx])

def visualize_domain_reload_details(reload_entry):
    st.header("Domain Reload Analysis")
    
    # Handle None values
    reset_time = reload_entry.get('reset_time', 0) or 0
    profiling_time_ms = reload_entry.get('profiling_time_ms', 0) or 0
    
    # Display summary metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Domain Reload Time", format_time(reset_time))
    with col2:
        st.metric("Profiling Time", format_time(profiling_time_ms / 1000))
    
    # Flatten the operations hierarchy for visualization
    def flatten_operations(operations, parent=""):
        flat_ops = []
        for op in operations:
            full_name = f"{parent}/{op['name']}" if parent else op['name']
            flat_ops.append({
                'name': full_name,
                'time_ms': op['time_ms'],
                'indent_level': op['indent_level']
            })
            flat_ops.extend(flatten_operations(op.get('children', []), full_name))
        return flat_ops
    
    flat_operations = flatten_operations(reload_entry.get('operations', []))
    
    # Create a DataFrame for operations
    if flat_operations:
        op_df = pd.DataFrame(flat_operations)
        
        # Add time in seconds
        op_df['time_s'] = op_df['time_ms'] / 1000
        
        # Add percentage of total time
        total_time_ms = reload_entry.get('profiling_time_ms', 0)
        op_df['percentage'] = op_df['time_ms'] / total_time_ms * 100 if total_time_ms > 0 else 0
        
        # Sort by time for the bar chart
        sorted_op_df = op_df.sort_values('time_ms', ascending=False).head(15)
        
        # Bar chart of top operations
        st.subheader("Top Operations by Time")
        
        fig = px.bar(
            sorted_op_df,
            y='name',
            x='time_s',
            orientation='h',
            text=sorted_op_df['percentage'].apply(lambda x: f"{x:.1f}%"),
            labels={'time_s': 'Time (seconds)', 'name': 'Operation'},
            height=600,
            color='percentage',
            color_continuous_scale='Viridis'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(yaxis_tickangle=0)
        st.plotly_chart(fig, use_container_width=True)
        
        # NEW: Create an icicle plot for hierarchical visualization (replacing sunburst)
        st.subheader("Domain Reload Operation Hierarchy")
        
        # Prepare data by extracting the hierarchical structure
        def prepare_hierarchy_data(operations, parent_path=""):
            data = []
            for i, op in enumerate(operations):
                op_path = f"{parent_path}/{op['name']}" if parent_path else op['name']
                # Split the path into components
                path_parts = op_path.split('/')
                
                data.append({
                    'id': op_path,
                    'operation': op['name'],
                    'time_ms': op['time_ms'],
                    'time_s': op['time_ms'] / 1000,
                    'percentage': (op['time_ms'] / total_time_ms * 100) if total_time_ms > 0 else 0,
                    'depth': len(path_parts),
                    'parent': '/'.join(path_parts[:-1]) if len(path_parts) > 1 else "",
                    'path': path_parts
                })
                
                # Add children
                if op.get('children'):
                    data.extend(prepare_hierarchy_data(op.get('children', []), op_path))
                    
            return data
            
        hierarchy_data = prepare_hierarchy_data(reload_entry.get('operations', []))
        
        if hierarchy_data:
            # Convert to DataFrame
            hierarchy_df = pd.DataFrame(hierarchy_data)
            
            # Create path columns for hierarchy
            max_depth = hierarchy_df['depth'].max()
            
            # Pad paths to have consistent length
            for i in range(max_depth):
                hierarchy_df[f'level_{i}'] = hierarchy_df['path'].apply(
                    lambda x: x[i] if i < len(x) else None
                )
            
            # Create list of level columns for the path parameter
            level_cols = [f'level_{i}' for i in range(max_depth)]
            
            # Create icicle plot
            fig = px.icicle(
                hierarchy_df,
                path=level_cols,
                values='time_ms',
                color='time_ms',
                color_continuous_scale='RdBu',
                height=700,
                hover_data=['time_s', 'percentage'],
                labels={
                    'time_ms': 'Time (ms)',
                    'time_s': 'Time (s)',
                    'percentage': 'Percentage'
                }
            )
            
            fig.update_traces(
                texttemplate="<b>%{label}</b><br>%{value:.1f}ms<br>%{customdata[1]:.1f}%",
                hovertemplate="<b>%{label}</b><br>Time: %{customdata[0]:.3f}s<br>Percentage: %{customdata[1]:.2f}%"
            )
            
            fig.update_layout(margin=dict(t=30, l=25, r=25, b=25))
            st.plotly_chart(fig, use_container_width=True)
            
            # Alternative flame graph style visualization using px.sunburst with maxdepth
            st.subheader("Domain Reload Flame Graph")
            fig = px.sunburst(
                hierarchy_df,
                path=level_cols,
                values='time_ms',
                color='percentage',
                color_continuous_scale='Viridis',
                height=600,
                maxdepth=3,  # Limit initial depth for better visibility
                hover_data=['time_s', 'percentage'],
                branchvalues='total'
            )
            
            fig.update_traces(
                textinfo="label+percent entry",
                hovertemplate="<b>%{label}</b><br>Time: %{customdata[0]:.3f}s<br>Percentage: %{customdata[1]:.2f}%"
            )
            
            fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
            st.plotly_chart(fig, use_container_width=True)
        
        # Raw data table
        #with st.expander("View Raw Operation Data"):
        #    display_df = op_df.copy()
        #    display_df['time'] = display_df['time_ms'].apply(lambda x: f"{x:.2f}ms")
        #    display_df['percentage'] = display_df['percentage'].apply(lambda x: f"{x:.2f}%")
        #    st.dataframe(display_df[['name', 'time', 'percentage']].sort_values('time_ms', ascending=False))

def check_log_data_completeness(log_file_path, shader_df, import_df, loading_df, build_df, refresh_df, player_build_info, unity_version):
    """Check which data elements are present or missing in the log file."""
    issues = []
    
    # Check if Unity version is available
    if unity_version is None:
        issues.append("❗ Unity version information not found in the log.")
    
    # Check for timestamp information
    has_timestamps = True
    
    # Check if any dataframes have timestamp data
    if not shader_df.empty and ('timestamp' not in shader_df.columns or shader_df['timestamp'].isna().all()):
        has_timestamps = False
    if not import_df.empty and ('timestamp' not in import_df.columns or import_df['timestamp'].isna().all()):
        has_timestamps = False
    if not loading_df.empty and ('timestamp' not in loading_df.columns or loading_df['timestamp'].isna().all()):
        has_timestamps = False
    if not refresh_df.empty and ('timestamp' not in refresh_df.columns or refresh_df['timestamp'].isna().all()):
        has_timestamps = False
    if player_build_info and all(entry.get('timestamp') is None for entry in player_build_info):
        has_timestamps = False
    
    if not has_timestamps:
        issues.append("❗ Timestamp information is missing or incomplete. Time-based analysis may be limited. \n You can enable TimeStamps in Unity Editor -> Preferences -> General -> Timestamp Editor log entries ❗")
    
    # Check for shader compilation data
    if shader_df.empty:
        issues.append("❗ No shader compilation data found.  Looks like no shaders were compiled in this Editor session. ❗")
    elif 'compilation_seconds' not in shader_df.columns:
        issues.append("❗ Shader compilation time data is missing. Shader performance analysis will be limited. ❗")
    
    # Check for asset import data
    if import_df.empty:
        issues.append("❗ No asset import data found.  Looks like no assets were imported in this Editor session ❗")
    
    # Check for project loading data
    if loading_df.empty:
        issues.append("❗ No project loading time data found.  This is very unusual ❗")
    
    # Check for build report data
    if build_df.empty:
        issues.append("❗ No build report data found.  Looks like this Editor session didn't complete a Build ❗")
    
    # Check for asset pipeline refresh data
    if refresh_df.empty:
        issues.append("❗ No asset pipeline refresh data found.  Looks like the Asset Pipeline was never refreshed in this Editor Session ❗")
    
    # Check for player build info
    if not player_build_info:
        issues.append("❗ No player build performance data found.  Looks like this Editor session didn't complete a Build ❗")
    
    return issues

def extract_unity_version(log_file_path):
    """Extract Unity version info from the log file."""
    version_pattern = r"Version is '([^']+)'"
    
    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                if "Built from" in line and "Version is" in line:
                    match = re.search(version_pattern, line)
                    if match:
                        return match.group(1)
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    return None

def visualize_log_data(log_file_path):
    # Extract Unity version first
    unity_version = extract_unity_version(log_file_path)
    
    st.title("Unity Build Log Analysis")
    
    # Display Unity version if available
    if unity_version:
        st.subheader(f"Unity Version: {unity_version}")
    
    # Parse all types of data
    shader_df = parse_shader_log(log_file_path)
    import_df = parse_asset_imports(log_file_path)
    loading_df = parse_loading_times(log_file_path)
    build_df, total_build_size, total_build_unit = parse_build_report(log_file_path)
    refresh_df = parse_asset_pipeline_refresh(log_file_path)
    player_build_info = parse_player_build_info(log_file_path)
    
    # Check if domain reload data exists (just a quick check to decide if we need a tab)
    has_domain_reloads = False
    domain_reloads = []
    with open(log_file_path, 'r') as file:
        for line in file:
            if "Domain Reload Profiling:" in line:
                has_domain_reloads = True
                domain_reloads = parse_domain_reloads(log_file_path)
                break
    
    # Check data completeness and show summary
    issues = check_log_data_completeness(log_file_path, shader_df, import_df, loading_df, build_df, refresh_df, player_build_info, unity_version)
    
    if issues:
        with st.expander("⚠️ Log Analysis Summary - Click to expand ⚠️", expanded=True):
            for issue in issues:
                st.write(issue)
            st.write("The analysis will proceed with available data.")
        st.markdown("---")
    else:
        st.success("✅ All data types were found in the log file. ✅ ")
        st.markdown("---")
    
    # Create a summary section with timing metrics from all tabs
    st.subheader("📊 Performance Summary 📊")
    col1, col2, col3 = st.columns(3)

    # Player Build time
    with col1:
        total_build_time = None
        if player_build_info:
            total_build_time = sum(entry.get('total_duration_sec', 0) for entry in player_build_info)
        st.metric("Total Build Time", format_time(total_build_time))

    # Project Loading time
    with col2:
        total_loading_time = None
        if not loading_df.empty and 'total_loading_time' in loading_df.columns:
            total_loading_time = loading_df['total_loading_time'].sum()
        st.metric("Total Loading Time", format_time(total_loading_time))

    # Domain Reloads time
    with col3:
        total_reload_time = None
        if domain_reloads:
            total_reload_time = sum((reload.get('reset_time', 0) or 0) for reload in domain_reloads)
        st.metric("Total Domain Reload Time", format_time(total_reload_time))

    col1, col2, col3 = st.columns(3)

    # Asset Pipeline Refresh time
    with col1:
        total_refresh_time = None
        if not refresh_df.empty and 'total_time' in refresh_df.columns:
            total_refresh_time = refresh_df['total_time'].sum()
        st.metric("Total Pipeline Refresh Time", format_time(total_refresh_time))

    # Asset Import time
    with col2:
        total_import_time = None
        if not import_df.empty and 'import_time_seconds' in import_df.columns:
            total_import_time = import_df['import_time_seconds'].sum()
        st.metric("Total Asset Import Time", format_time(total_import_time))

    # Shader Compilation time
    with col3:
        total_shader_time = None
        if not shader_df.empty and 'compilation_seconds' in shader_df.columns:
            total_shader_time = shader_df['compilation_seconds'].sum()
        st.metric("Total Shader Compilation Time", format_time(total_shader_time))
    
    # Calculate session duration if timestamps are available
    all_timestamps = []
    
    # Collect timestamps from all dataframes
    if not shader_df.empty and 'timestamp' in shader_df.columns:
        all_timestamps.extend(ts for ts in shader_df['timestamp'] if pd.notna(ts))
    if not import_df.empty and 'timestamp' in import_df.columns:
        all_timestamps.extend(ts for ts in import_df['timestamp'] if pd.notna(ts))
    if not loading_df.empty and 'timestamp' in loading_df.columns:
        all_timestamps.extend(ts for ts in loading_df['timestamp'] if pd.notna(ts))
    if not refresh_df.empty and 'timestamp' in refresh_df.columns:
        all_timestamps.extend(ts for ts in refresh_df['timestamp'] if pd.notna(ts))
    if player_build_info:
        all_timestamps.extend(entry.get('timestamp') for entry in player_build_info if entry.get('timestamp'))
    if domain_reloads:
        all_timestamps.extend(reload.get('timestamp') for reload in domain_reloads if reload.get('timestamp'))
    
    # If we have timestamps, calculate and display session duration
    if all_timestamps:
        first_timestamp = min(all_timestamps)
        last_timestamp = max(all_timestamps)
        session_duration = (last_timestamp - first_timestamp).total_seconds()
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Editor Session Duration", format_time(session_duration))

    
    st.markdown("---")
    
    # Check which data types we have available
    has_build_info = bool(player_build_info)
    has_build_report = not build_df.empty
    has_loading_data = not loading_df.empty
    has_refresh_data = not refresh_df.empty
    has_import_data = not import_df.empty
    has_shader_data = not shader_df.empty and ('compilation_seconds' in shader_df.columns or 'shader_name' in shader_df.columns)
    
    # Create tabs for different visualizations
    tab_titles = []
    if has_build_info:
        tab_titles.append("Player Build Performance")
    if has_build_report:
        tab_titles.append("Build Report")
    if has_loading_data:
        tab_titles.append("Project Loading")
    if has_domain_reloads:
        tab_titles.append("Domain Reloads")
    if has_refresh_data:
        tab_titles.append("Asset Pipeline Refreshes")
    if has_import_data:
        tab_titles.append("Asset Imports")
    if has_shader_data:
        tab_titles.append("Shader Compilation")
    
    # If we don't have any data, show a message
    if not tab_titles:
        st.error("No actionable Unity build data found in the log file.")
        return
    
    # Create the tabs
    tabs = st.tabs(tab_titles)
    
    # Populate tabs based on available data
    tab_index = 0
    
    if has_build_info:
        with tabs[tab_index]:
            visualize_player_build_info(player_build_info)
        tab_index += 1
    
    if has_build_report:
        with tabs[tab_index]:
            visualize_build_report(build_df, total_build_size, total_build_unit)
        tab_index += 1
        
    if has_loading_data:
        with tabs[tab_index]:
            visualize_loading_times(loading_df)
        tab_index += 1
    
    if has_domain_reloads:
        with tabs[tab_index]:
            visualize_domain_reloads(log_file_path)
        tab_index += 1
    
    if has_refresh_data:
        with tabs[tab_index]:
            visualize_pipeline_refreshes(refresh_df, log_file_path)  # Pass log_file_path
        tab_index += 1
    
    if has_import_data:
        with tabs[tab_index]:
            visualize_asset_imports(import_df)
        tab_index += 1
    
    if has_shader_data:
        with tabs[tab_index]:
            visualize_shader_data(shader_df)

if __name__ == "__main__":
    # For testing with sample data
    import sys
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        st.set_page_config(layout="wide", page_title="Unity Build Log Analyzer")
        
        # File upload with tooltip explaining where to find the log file
        log_file_help = """
        Upload your Unity Editor.log file. You can find it at:
        
        **Windows:** %LOCALAPPDATA%\\Unity\\Editor\\Editor.log  
        %LOCALAPPDATA% typically resolves to C:\\Users\\[yourusername]\\AppData\\Local  
        So, the full path is usually something like C:\\Users\\[yourusername]\\AppData\\Local\\Unity\\Editor\\Editor.log
        
        **macOS:** ~/Library/Logs/Unity/Editor.log  
        You can also use the Console.app utility to find this log file.
        
        **Linux:** ~/.config/unity3d/Editor.log
        """
        
        log_file = st.file_uploader("Please Upload your Unity log file (Editor.log)", type=["txt", "log"], help=log_file_help)
        if not log_file:
            st.stop()
    
    if isinstance(log_file, str):
        visualize_log_data(log_file)
    else:
        # Handle uploaded file
        with open("temp_log.txt", "wb") as f:
            f.write(log_file.getvalue())
        visualize_log_data("temp_log.txt")