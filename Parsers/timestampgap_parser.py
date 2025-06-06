from datetime import datetime
import io 
import re

def parse_timestamp_gaps(log_file_path, threshold_seconds=60):
    """
    Extract lines from the log file where time between consecutive logged lines exceeds threshold_seconds.
    
    Args:
        log_file_path: Path to the log file OR a BytesIO object
        threshold_seconds: Minimum time gap to report (in seconds)
        
    Returns:
        List of dictionaries with information about gaps
    """
    # Regular expression to match timestamps at the beginning of lines
    timestamp_pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\|'
    
    gaps = []
    prev_timestamp = None
    prev_line = None
    line_number = 0
    
    # Keep a buffer of recent lines for context (5 = 4 context lines + current line)
    context_buffer = []
    
    # Handle both file paths and BytesIO objects
    if isinstance(log_file_path, (io.BytesIO, io.StringIO)):
        # It's an in-memory file object
        if isinstance(log_file_path, io.BytesIO):
            # Convert bytes to string
            content = log_file_path.getvalue().decode('utf-8', errors='ignore')
            file_lines = content.splitlines()
        else:
            # It's already a StringIO
            file_lines = log_file_path.getvalue().splitlines()
            
        for i, line in enumerate(file_lines):
            line_number = i + 1
            line_with_nl = line + "\n"  # Add newline character back
            
            # Maintain a rolling buffer of the last 5 lines (4 context + current)
            if len(context_buffer) >= 5:
                context_buffer.pop(0)
            context_buffer.append(line_with_nl)
            
            # Check if this line has a timestamp
            match = re.match(timestamp_pattern, line)
            if match:
                # Process timestamp logic
                timestamp_str = match.group(1)
                try:
                    current_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                    
                    # If we have a previous timestamp, check the gap
                    if prev_timestamp:
                        time_diff = (current_timestamp - prev_timestamp).total_seconds()
                        
                        if time_diff >= threshold_seconds:
                            gaps.append({
                                'prev_timestamp': prev_timestamp,
                                'current_timestamp': current_timestamp,
                                'time_diff_seconds': time_diff,
                                'prev_line': prev_line,
                                'current_line': line_with_nl,
                                'prev_line_number': line_number - 1,
                                'current_line_number': line_number,
                                'context_before': context_buffer[:-1] if len(context_buffer) > 1 else []  # All lines except current
                            })
                    
                    # Update for next iteration
                    prev_timestamp = current_timestamp
                    prev_line = line_with_nl
                except ValueError:
                    # If timestamp parsing fails, just continue
                    pass
    else:
        # It's a file path
        try:
            with open(log_file_path, 'r', errors='ignore') as file:
                for i, line in enumerate(file):
                    line_number = i + 1
                    
                    # Maintain a rolling buffer of the last 5 lines (4 context + current)
                    if len(context_buffer) >= 5:
                        context_buffer.pop(0)
                    context_buffer.append(line)
                    
                    # Check if this line has a timestamp
                    match = re.match(timestamp_pattern, line)
                    if match:
                        timestamp_str = match.group(1)
                        
                        try:
                            current_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                            
                            # If we have a previous timestamp, check the gap
                            if prev_timestamp:
                                time_diff = (current_timestamp - prev_timestamp).total_seconds()
                                
                                if time_diff >= threshold_seconds:
                                    gaps.append({
                                        'prev_timestamp': prev_timestamp,
                                        'current_timestamp': current_timestamp,
                                        'time_diff_seconds': time_diff,
                                        'prev_line': prev_line,
                                        'current_line': line,
                                        'prev_line_number': line_number - 1,
                                        'current_line_number': line_number,
                                        'context_before': context_buffer[:-1] if len(context_buffer) > 1 else []  # All lines except current
                                    })
                            
                            # Update for next iteration
                            prev_timestamp = current_timestamp
                            prev_line = line
                        except ValueError:
                            # If timestamp parsing fails, just continue
                            pass
        except Exception as e:
            print(f"Error opening log file: {e}")
    
    # Sort gaps by duration (largest first)
    return sorted(gaps, key=lambda x: x['time_diff_seconds'], reverse=True)