import streamlit as st

from Parsers import *
from Reporting import *
from Utils import *
from Visualizers import *


if __name__ == "__main__":
    # For testing with sample data
    import sys
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        visualize_log_data(log_file)
    else:
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
            
        # Title and description
        st.title("Unity Build Log Analyzer")
        st.markdown("This tool analyzes Unity Editor log files to provide insights into build performance and other metrics.")
        
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
        current_log_file = st.file_uploader("Please Upload your Unity log file (Editor.log)", 
                                           type=["txt", "log"], 
                                           help=log_file_help,
                                           key="log_file_uploader")
        
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