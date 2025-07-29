import re
import pandas as pd

def parse_performance_report(log_file):
    """Parse Unity Performance Report entries from the log file."""
    performance_data = []
    
    # Regex pattern to match performance report entries
    pattern = re.compile(r'\[Performance\] (.*?)\s*:\s*(\d+) samples, Peak.\s*([\d.]+) (\w+) \((\d+\.\d+)x\), Avg.\s*([\d.]+) (\w+), Total. ([\d.]+) (\w+) \(([\d.]+)%\)')
    
    # Process content based on input type
    if isinstance(log_file, str):
        # It's a file path
        with open(log_file, 'r', errors='ignore') as file:
            process_lines(file, pattern, performance_data)
    else:
        # It's a file-like object (BytesIO)
        log_file.seek(0)
        content = log_file.read().decode('utf-8', errors='ignore')
        process_lines(content.splitlines(), pattern, performance_data)
                
    return pd.DataFrame(performance_data) if performance_data else pd.DataFrame()

def process_lines(lines, pattern, performance_data):
    """Process each line to extract performance data."""
    for line in lines:
        # Make sure line is a string
        if isinstance(line, bytes):
            line = line.decode('utf-8', errors='ignore')
            
        match = pattern.search(line)
        if match:
            operation = match.group(1)
            samples = int(match.group(2))
            peak_value = float(match.group(3))
            peak_unit = match.group(4)
            peak_factor = float(match.group(5))
            avg_value = float(match.group(6))
            avg_unit = match.group(7)
            total_value = float(match.group(8))
            total_unit = match.group(9)
            percentage = float(match.group(10))
            
            # Convert units to microseconds for consistent comparison
            peak_us = convert_to_microseconds(peak_value, peak_unit)
            avg_us = convert_to_microseconds(avg_value, avg_unit)
            total_us = convert_to_microseconds(total_value, total_unit)
            
            # Extract category and operation
            parts = operation.split(':', 1)
            if len(parts) > 1:
                category = parts[0].strip()
                operation_name = parts[1].strip()
            else:
                # Try to extract category in another way
                parts = operation.split('.', 1)
                if len(parts) > 1:
                    category = parts[0].strip()
                    operation_name = parts[1].strip()
                else:
                    category = "Other"
                    operation_name = operation.strip()
            
            performance_data.append({
                'operation': operation,
                'category': category,
                'operation_name': operation_name,
                'samples': samples,
                'peak_value': peak_value,
                'peak_unit': peak_unit,
                'peak_factor': peak_factor,
                'avg_value': avg_value,
                'avg_unit': avg_unit,
                'total_value': total_value,
                'total_unit': total_unit,
                'percentage': percentage,
                'peak_us': peak_us,
                'avg_us': avg_us,
                'total_us': total_us
            })

def convert_to_microseconds(value, unit):
    """Convert various time units to microseconds for consistent comparison."""
    if unit == 'ns':
        return value / 1000  # nanoseconds to microseconds
    elif unit == 'us':
        return value  # already in microseconds
    elif unit == 'ms':
        return value * 1000  # milliseconds to microseconds
    elif unit == 's':
        return value * 1000000  # seconds to microseconds
    else:
        return value  # unknown unit, return as is
