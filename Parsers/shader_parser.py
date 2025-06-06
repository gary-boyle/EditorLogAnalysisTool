import re
import streamlit as st
import pandas as pd

from Utils.data_helpers import extract_float
from Utils import *

@st.cache_data    
def parse_shader_log(log_file_path):
    content = read_log_content(log_file_path)
    
    # Split into individual shader compilation entries - improve the pattern
    entries = re.split(r'(?=.*?Compiling (shader|compute shader))', content)
    entries = [entry.strip() for entry in entries if entry.strip() and 'Compiling' in entry]
    
    # Debug count
    print(f"Found {len(entries)} shader compilation entries")
    
    parsed_data = []
    entries_with_name_no_time = 0
    
    for i, entry in enumerate(entries):
        shader_data = {}
        
        # More flexible patterns that can handle timestamps and thread IDs
        shader_match = re.search(r'Compiling shader\s+"(.*?)"\s+pass\s+"(.*?)"\s+\((.*?)\)', entry)
        compute_shader_match = re.search(r'Compiling compute shader\s+"(.*?)"', entry)
        
        if shader_match:
            shader_data['shader_name'] = shader_match.group(1)
            shader_data['pass_name'] = shader_match.group(2)
            shader_data['pass_type'] = shader_match.group(3)
            shader_data['shader_type'] = 'regular'
        elif compute_shader_match:
            shader_data['shader_name'] = compute_shader_match.group(1)
            shader_data['pass_name'] = "Compute"
            shader_data['pass_type'] = "compute"
            shader_data['shader_type'] = 'compute'
        else:
            # If we can't find the shader details with the stricter regex, try a more lenient approach
            if 'Compiling shader' in entry:
                # Try to extract just the shader name, which should be in quotes after "Compiling shader"
                lenient_match = re.search(r'Compiling shader\s+"([^"]+)"', entry)
                if lenient_match:
                    shader_data['shader_name'] = lenient_match.group(1)
                    # Try to extract pass name and type with a more lenient pattern
                    pass_match = re.search(r'pass\s+"([^"]+)"\s+\((\w+)\)', entry)
                    if pass_match:
                        shader_data['pass_name'] = pass_match.group(1)
                        shader_data['pass_type'] = pass_match.group(2)
                    else:
                        shader_data['pass_name'] = "Unknown"
                        shader_data['pass_type'] = "unknown"
                    shader_data['shader_type'] = 'regular'
                else:
                    continue  # Skip if we still can't identify
            elif 'Compiling compute shader' in entry:
                # Try to extract just the compute shader name, which should be in quotes after "Compiling compute shader"
                lenient_match = re.search(r'Compiling compute shader\s+"([^"]+)"', entry)
                if lenient_match:
                    shader_data['shader_name'] = lenient_match.group(1)
                    shader_data['pass_name'] = "Compute"
                    shader_data['pass_type'] = "compute"
                    shader_data['shader_type'] = 'compute'
                else:
                    continue  # Skip if we still can't identify
            else:
                continue  # Skip if we can't identify the shader
        
        # Extract variant counts - only applies to regular shaders
        if shader_data.get('shader_type') == 'regular':
            variant_patterns = {
                'full_variants': r'Full variant space:\s+(\d+)',
                'after_filtering': r'After settings filtering:\s+(\d+)',
                'after_builtin_stripping': r'After built-in stripping:\s+(\d+)',
                'after_scriptable_stripping': r'After scriptable stripping:\s+(\d+)'
            }
            
            for key, pattern in variant_patterns.items():
                match = re.search(pattern, entry)
                shader_data[key] = int(match.group(1)) if match else None
            
            # Extract timing information for regular shaders
            shader_data['processed_seconds'] = extract_float(entry, r'Processed in ([\d.]+) seconds')
            
            # Extract compilation results for regular shaders - more flexible pattern
            finished_match = re.search(r'finished in ([\d.]+) seconds\..*?compiled (\d+) variants', entry, re.DOTALL | re.IGNORECASE)
            
            # More detailed match if the first one succeeds
            if finished_match:
                shader_data['compilation_seconds'] = float(finished_match.group(1))
                shader_data['compiled_variants'] = int(finished_match.group(2))
                
                # Try to extract cache hits and CPU time
                local_cache_hits = re.search(r'Local cache hits (\d+)', entry)
                shader_data['local_cache_hits'] = int(local_cache_hits.group(1)) if local_cache_hits else 0
                
                local_cache_cpu = re.search(r'Local cache hits \d+ \(([\d.]+)s CPU time\)', entry)
                shader_data['local_cache_cpu_time'] = float(local_cache_cpu.group(1)) if local_cache_cpu else 0.0
                
                remote_cache_hits = re.search(r'remote cache hits (\d+)', entry)
                shader_data['remote_cache_hits'] = int(remote_cache_hits.group(1)) if remote_cache_hits else 0
                
                remote_cache_cpu = re.search(r'remote cache hits \d+ \(([\d.]+)s CPU time\)', entry)
                shader_data['remote_cache_cpu_time'] = float(remote_cache_cpu.group(1)) if remote_cache_cpu else 0.0
                
                compilation_cpu = re.search(r'compiled \d+ variants \(([\d.]+)s CPU time\)', entry)
                shader_data['compilation_cpu_time'] = float(compilation_cpu.group(1)) if compilation_cpu else 0.0
                
                skipped = re.search(r'skipped (\d+) variants', entry)
                shader_data['skipped_variants'] = int(skipped.group(1)) if skipped else 0
            
            # If we didn't find the compilation time but have other data, log it for debugging
            if 'shader_name' in shader_data and 'compilation_seconds' not in shader_data:
                entries_with_name_no_time += 1
            
            # Extract serialization time
            shader_data['serialization_seconds'] = extract_float(entry, r'Prepared data for serialisation in ([\d.]+)s')
            
            # Calculate total time for regular shaders
            processed_time = shader_data.get('processed_seconds', 0) or 0
            compilation_time = shader_data.get('compilation_seconds', 0) or 0
            serialization_time = shader_data.get('serialization_seconds', 0) or 0
            shader_data['total_seconds'] = processed_time + compilation_time + serialization_time
        
        # Handle compute shaders separately
        elif shader_data.get('shader_type') == 'compute':
            # Get variants left after stripping for compute shaders - more flexible
            variants_left_match = re.search(r'finished in [\d.]+? seconds\. (\d+) of (\d+) variants left', entry)
            if variants_left_match:
                shader_data['after_scriptable_stripping'] = int(variants_left_match.group(1))
                shader_data['full_variants'] = int(variants_left_match.group(2))
                
            # Get the time for stripping - more flexible
            stripping_time_match = re.search(r'starting stripping.*?finished in ([\d.]+) seconds', entry, re.DOTALL)
            if stripping_time_match:
                shader_data['stripping_seconds'] = float(stripping_time_match.group(1))
                
            # Find the compilation info for compute shaders - more flexible
            compute_compile_match = re.search(r'starting compilation.*?finished in ([\d.]+) seconds\..*?Local cache hits (\d+)', entry, re.DOTALL)
            if compute_compile_match:
                shader_data['compilation_seconds'] = float(compute_compile_match.group(1))
                shader_data['local_cache_hits'] = int(compute_compile_match.group(2))
                
                # Try to extract more info
                remote_cache_hits = re.search(r'remote cache hits (\d+)', entry)
                shader_data['remote_cache_hits'] = int(remote_cache_hits.group(1)) if remote_cache_hits else 0
                
                compiled_variants = re.search(r'compiled (\d+) variants', entry)
                shader_data['compiled_variants'] = int(compiled_variants.group(1)) if compiled_variants else 0
                
                shader_data['skipped_variants'] = 0
            
            # Alternative pattern for simpler compute shader entries
            if 'compilation_seconds' not in shader_data:
                simple_finished_match = re.search(r'finished in ([\d.]+) seconds', entry)
                if simple_finished_match:
                    shader_data['compilation_seconds'] = float(simple_finished_match.group(1))
            
            # If we didn't find the compilation time but have other data, log it for debugging
            if 'shader_name' in shader_data and 'compilation_seconds' not in shader_data:
                entries_with_name_no_time += 1
            
            # Extract serialization time (applies to both types)
            shader_data['serialization_seconds'] = extract_float(entry, r'Prepared data for serialisation in ([\d.]+)s')
            
            # Calculate total time for compute shaders
            stripping_time = shader_data.get('stripping_seconds', 0) or 0
            compilation_time = shader_data.get('compilation_seconds', 0) or 0
            serialization_time = shader_data.get('serialization_seconds', 0) or 0
            shader_data['total_seconds'] = stripping_time + compilation_time + serialization_time
        
        parsed_data.append(shader_data)
    
    print(f"Found {entries_with_name_no_time} entries with shader name but no compilation time")
    
    # For debugging, let's add a field showing which entries were missing compilation time
    df = pd.DataFrame(parsed_data) if parsed_data else pd.DataFrame()
    if not df.empty:
        df['has_compilation_time'] = ~df['compilation_seconds'].isna()
        
        # Check for any entries with missing compilation times
        if df[~df['has_compilation_time']].shape[0] > 0:
            print(f"Entries with missing compilation time:")
            for _, row in df[~df['has_compilation_time']].iterrows():
                print(f"- {row['shader_name']}, type: {row.get('shader_type')}")
    
    return df
