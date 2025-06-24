import streamlit as st
import sys
import argparse
import os
from datetime import datetime
from streamlit_chunk_file_uploader import uploader

from Parsers import *
from Reporting import *
from Utils import *
from Visualizers import *


if __name__ == "__main__":
    # Check if running with command line arguments
    if len(sys.argv) > 1:
        # Parse command line arguments
        args = data_helpers.parse_arguments()
        
        if os.path.exists(args.log_file):
            print(f"Analyzing log file: {args.log_file}")
            
            # Use default parsing options (all enabled)
            parsing_options = {
                'shader': True,
                'imports': True,
                'loading': True,
                'build_report': True,
                'pipeline': True, 
                'domain_reload': True,
                'player_build': True,
                'il2cpp': True,
                'tundra': True,
                'timestamp_gaps': True
            }
            
            # Parse the data (modified to return parsed data)
            parsed_data = visualize_log_data(args.log_file, parsing_options=parsing_options)
            
            # Determine output path for the PDF
            output_path = args.output
            if not output_path:
                # Get the input log file name and path
                log_dir = os.path.dirname(args.log_file)
                log_filename = os.path.basename(args.log_file)
                
                # Replace .log with .pdf or just append .pdf if no extension
                base_name, ext = os.path.splitext(log_filename)
                pdf_filename = f"{base_name}.pdf"
                
                output_path = os.path.join(log_dir, pdf_filename)
            
            # Generate the PDF report
            print(f"Generating PDF report...")
            pdf_buffer = generate_pdf_report(args.log_file, parsed_data)
            
            # Save the PDF to the specified path
            with open(output_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            print(f"PDF report saved to: {output_path}")
            
        else:
            print(f"Error: Log file not found - {args.log_file}")
            sys.exit(1)
    else:
        # Run in Streamlit web application mode
        st.set_page_config(layout="wide", page_title="Unity Build Log Analyzer")
        
        # Initialize session state for options if not already set
        if 'parse_options' not in st.session_state:
            st.session_state.parse_options = {
                'shader': True,
                'imports': True,
                'loading': True,
                'build_report': True,
                'pipeline': True, 
                'domain_reload': True,
                'player_build': True,
                'il2cpp': True,
                'tundra': True
            }

        # Initialize flag for preset change
        if 'preset_changed' not in st.session_state:
            st.session_state.preset_changed = False    
            
        # Title and description
        st.title("Unity Build Log Analyzer")
        st.markdown("This tool analyzes Unity Editor log files to provide insights into build performance and other metrics.")
        
        # Add preset dropdown at the top
        st.markdown("### Analysis Preset Selection")
        st.markdown("Select a preset to focus on a specific type of analysis:")
        
        # Define preset options
        preset_options = {
            "All Analysis Types": {
                'shader': True, 'imports': True, 'loading': True, 'build_report': True,
                'pipeline': True, 'domain_reload': True, 'player_build': True, 
                'il2cpp': True, 'tundra': True, 'timestamp_gaps': True
            },
            "Shader Analysis Only": {
                'shader': True, 'imports': False, 'loading': False, 'build_report': False,
                'pipeline': False, 'domain_reload': False, 'player_build': False,
                'il2cpp': False, 'tundra': False, 'timestamp_gaps': False
            },
            "Asset Imports Only": {
                'shader': False, 'imports': True, 'loading': False, 'build_report': False,
                'pipeline': False, 'domain_reload': False, 'player_build': False,
                'il2cpp': False, 'tundra': False, 'timestamp_gaps': False
            },
            "Loading Analysis Only": {
                'shader': False, 'imports': False, 'loading': True, 'build_report': False,
                'pipeline': False, 'domain_reload': False, 'player_build': False,
                'il2cpp': False, 'tundra': False, 'timestamp_gaps': False
            },
            "Build Report Only": {
                'shader': False, 'imports': False, 'loading': False, 'build_report': True,
                'pipeline': False, 'domain_reload': False, 'player_build': False,
                'il2cpp': False, 'tundra': False, 'timestamp_gaps': False
            },
            "Pipeline Refresh Analysis Only": {
                'shader': False, 'imports': False, 'loading': False, 'build_report': False,
                'pipeline': True, 'domain_reload': False, 'player_build': False,
                'il2cpp': False, 'tundra': False, 'timestamp_gaps': False
            },
            "Domain Reload Analysis Only": {
                'shader': False, 'imports': False, 'loading': False, 'build_report': False,
                'pipeline': False, 'domain_reload': True, 'player_build': False,
                'il2cpp': False, 'tundra': False, 'timestamp_gaps': False
            },
            "Player Build Analysis Only": {
                'shader': False, 'imports': False, 'loading': False, 'build_report': False,
                'pipeline': False, 'domain_reload': False, 'player_build': True,
                'il2cpp': False, 'tundra': False, 'timestamp_gaps': False
            },
            "IL2CPP Analysis Only": {
                'shader': False, 'imports': False, 'loading': False, 'build_report': False,
                'pipeline': False, 'domain_reload': False, 'player_build': False,
                'il2cpp': True, 'tundra': False, 'timestamp_gaps': False
            },
            "Timestamp Gaps Only": {
                'shader': False, 'imports': False, 'loading': False, 'build_report': False,
                'pipeline': False, 'domain_reload': False, 'player_build': False,
                'il2cpp': False, 'tundra': False, 'timestamp_gaps': True
            }
        }
        
        # Initialize session state for selected preset if it doesn't exist
        if 'selected_preset' not in st.session_state:
            st.session_state.selected_preset = "All Analysis Types"
        
         # Function to handle preset changes
        def on_preset_change():
            selected = st.session_state.preset_selector
            if selected != st.session_state.selected_preset:
                st.session_state.selected_preset = selected
                
                # Update parse options based on selected preset
                st.session_state.parse_options = preset_options[selected].copy()
                
                # Clear any previously parsed data when changing presets
                if 'parsed_data' in st.session_state:
                    del st.session_state.parsed_data
                
                # Set flag to indicate need for rerun
                st.session_state.preset_changed = True
        
        # Create the dropdown with on_change callback
        selected_preset = st.selectbox(
            "Analysis Preset",
            options=list(preset_options.keys()),
            index=list(preset_options.keys()).index(st.session_state.selected_preset),
            key="preset_selector",
            on_change=on_preset_change
        )
        
        # Check if preset changed and rerun if needed
        if st.session_state.preset_changed:
            st.session_state.preset_changed = False  # Reset the flag
            st.rerun()
        

        # First show parsing options
        with st.expander("Parsing Options (Customize what to analyze)", expanded=False):
            st.caption("Select which data to analyze (disable options to speed up processing for large logs)")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.session_state.parse_options['shader'] = st.checkbox(
                    "Shader Compilation", 
                    value=st.session_state.parse_options['shader'],
                    help="Parse shader compilation times and statistics"
                )
                
                st.session_state.parse_options['imports'] = st.checkbox(
                    "Asset Imports", 
                    value=st.session_state.parse_options['imports'],
                    help="Parse asset import timings"
                )
                
                st.session_state.parse_options['loading'] = st.checkbox(
                    "Project Loading Times", 
                    value=st.session_state.parse_options['loading'],
                    help="Parse Unity project loading times"
                )
            
            with col2:
                st.session_state.parse_options['build_report'] = st.checkbox(
                    "Build Report", 
                    value=st.session_state.parse_options['build_report'],
                    help="Parse build size reports"
                )
                
                st.session_state.parse_options['pipeline'] = st.checkbox(
                    "Asset Pipeline Refreshes", 
                    value=st.session_state.parse_options['pipeline'],
                    help="Parse asset pipeline refresh times"
                )
                
                st.session_state.parse_options['domain_reload'] = st.checkbox(
                    "Domain Reloads", 
                    value=st.session_state.parse_options['domain_reload'],
                    help="Parse domain reload data (can be slow for large logs)"
                )
            
            with col3:
                st.session_state.parse_options['player_build'] = st.checkbox(
                    "Player Build Performance", 
                    value=st.session_state.parse_options['player_build'],
                    help="Parse detailed player build performance data"
                )
                
                st.session_state.parse_options['il2cpp'] = st.checkbox(
                    "IL2CPP Processing", 
                    value=st.session_state.parse_options['il2cpp'],
                    help="Parse IL2CPP compilation data"
                )
                
                st.session_state.parse_options['tundra'] = st.checkbox(
                    "Tundra Build Info", 
                    value=st.session_state.parse_options['tundra'],
                    help="Parse Tundra build system information"
                )
                st.session_state.parse_options['timestamp_gaps'] = st.checkbox(
                        "Timestamp Gaps", 
                        value=st.session_state.parse_options.get('timestamp_gaps', True),
                        help="Analyze gaps between timestamps to detect frozen or unresponsive periods"
                )
                
        
        # Then show file uploader
        st.markdown("### Upload Log File")
        
        log_file_help = """
        Upload your Unity Editor.log file. You can find it at:
        
        **Windows:** %LOCALAPPDATA%\\Unity\\Editor\\Editor.log  
        %LOCALAPPDATA% typically resolves to C:\\Users\\[yourusername]\\AppData\\Local  
        So, the full path is usually something like C:\\Users\\[yourusername]\\AppData\\Local\\Unity\\Editor\\Editor.log
        
        **macOS:** ~/Library/Logs/Unity/Editor.log  
        You can also use the Console.app utility to find this log file.
        
        **Linux:** ~/.config/unity3d/Editor.log
        """
        
        # Track the uploaded file and its modification time
        current_log_file = uploader("Please Upload your Unity log file (Editor.log)", 
                                           type=["txt", "log"], 
                                           help=log_file_help,
                                           key="log_file_uploader",
                                           chunk_size=31)
        
        if current_log_file:
            # Get file details to detect changes
            file_details = {"filename": current_log_file.name, "size": current_log_file.size}
            file_identifier = f"{file_details['filename']}_{file_details['size']}"
            
            # If the file has changed, clear the cached data
            if 'previous_file_name' not in st.session_state or st.session_state.previous_file_name != file_identifier:
                st.session_state.previous_file_name = file_identifier
                # Clear the cached parsed data
                if 'parsed_data' in st.session_state:
                    del st.session_state.parsed_data
                st.info("New log file detected. Analyzing...")
            
            with st.spinner("Analyzing log file..."):
                # Instead of writing to a file, use a BytesIO object in memory
                import io
                log_contents = io.BytesIO(current_log_file.getvalue())
                
                # Modify your parsing functions to accept file-like objects instead of paths
                visualize_log_data(log_contents, parsing_options=st.session_state.parse_options)
        else:
            # Reset the previous file name when no file is uploaded
            st.session_state.previous_file_name = None
            # Clear cached data
            if 'parsed_data' in st.session_state:
                del st.session_state.parsed_data
            
            # Show instructions when no file is uploaded
            st.info("👆 Please upload a Unity Editor.log file to begin analysis.")
            
            # Add some helpful instructions
            with st.expander("How to use this tool"):
                st.markdown("""
                1. Select which data types you want to analyze using the checkboxes above
                2. Upload your Unity Editor.log file
                3. The tool will analyze the log and display visualizations
                
                **Tips:**
                - For large log files, disable data types you don't need to speed up analysis
                - Domain Reload parsing can be particularly intensive for large logs
                - Make sure timestamps are enabled in Unity for the most detailed analysis
                """)