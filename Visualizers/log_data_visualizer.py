import pandas as pd
import time 
import streamlit as st
import plotly.express as px

from datetime import datetime
from datetime import datetime
from Utils.ui_helpers import show_progress_checklist, show_big_spinner
from Utils.data_helpers import extract_unity_version

from Parsers import *
from Utils import *
from Reporting import *

from .asset_visualizer import visualize_asset_imports
from .build_visualizer import visualize_player_build_info, visualize_build_report, enhance_build_info_with_tundra
from .domainreload_visualizer import visualize_domain_reloads
from .il2cpp_visualizer import visualize_il2cpp_data
from .loading_visualizer import visualize_loading_times
from .pipelinerefresh_visualizer import visualize_pipeline_refreshes
from .shader_visualizer import visualize_shader_data

def visualize_log_data(log_file_path, parsing_options=None):
    # Use default options (all enabled) if none provided
    if parsing_options is None:
        parsing_options = {
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
    
    # Check if we already have parsed data in the session state
    if 'parsed_data' not in st.session_state:
        # Start overall timing
        start_time_overall = time.time()
        
        # Create a dictionary to store timing results
        section_times = {}
        
        # Show progress checklist during initial parsing
        update_progress, progress_container = show_progress_checklist(parsing_options)
        
        # Extract Unity version first
        update_progress(message="Reading Unity version...")
        unity_version = extract_unity_version(log_file_path)
        
        # Parse all data types
        shader_df = pd.DataFrame()
        shader_issues = {}
        if parsing_options['shader']:
            update_progress(message="Parsing shader errors and warnings...")
            start_time = time.time()
            shader_issues = parse_shader_errors_warnings(log_file_path)
            section_times["Parse Shader Issues"] = time.time() - start_time
            update_progress("Shader Issues", "Shader errors and warnings parsed")
            
            update_progress(message="Parsing shader compilation data...")
            start_time = time.time()
            shader_df = parse_shader_log(log_file_path)
            section_times["Parse Shader Log"] = time.time() - start_time
            update_progress("Shader Compilation Data", "Shader compilation data parsed")
    
        # Parse selected data types with timing and update progress
        shader_df = pd.DataFrame()
        if parsing_options['shader']:
            update_progress(message="Parsing shader compilation data...")
            start_time = time.time()
            shader_df = parse_shader_log(log_file_path)
            section_times["Parse Shader Log"] = time.time() - start_time
            update_progress("Shader Compilation Data", "Shader compilation data parsed")
        

        #shader_df = pd.DataFrame()
        shader_issues = {}
        if parsing_options['shader']:
            update_progress(message="Parsing shader errors and warnings...")
            start_time = time.time()
            shader_issues = parse_shader_errors_warnings(log_file_path)
            section_times["Parse Shader Issues"] = time.time() - start_time
            update_progress("Shader Issues", "Shader errors and warnings parsed")
        
        
        import_df = pd.DataFrame()
        if parsing_options['imports']:
            update_progress(message="Parsing asset import data...")
            start_time = time.time()
            import_df = parse_asset_imports(log_file_path)
            section_times["Parse Asset Imports"] = time.time() - start_time
            update_progress("Asset Import Data", "Asset import data parsed")
        
        # Continue with the same pattern for all other parsing steps...
        loading_df = pd.DataFrame()
        if parsing_options['loading']:
            update_progress(message="Parsing project loading times...")
            start_time = time.time()
            loading_df = parse_loading_times(log_file_path)
            section_times["Parse Loading Times"] = time.time() - start_time
            update_progress("Project Loading Times", "Project loading times parsed")
        
        build_df, total_build_size, total_build_unit = pd.DataFrame(), None, None
        if parsing_options['build_report']:
            update_progress(message="Parsing build report data...")
            start_time = time.time()
            build_df, total_build_size, total_build_unit = parse_build_report(log_file_path)
            section_times["Parse Build Report"] = time.time() - start_time
            update_progress("Build Report Data", "Build Report Data parsed")
        
        refresh_df = pd.DataFrame()
        if parsing_options['pipeline']:
            update_progress(message="Parsing asset pipeline refresh data...")
            start_time = time.time()
            refresh_df = parse_asset_pipeline_refresh(log_file_path)
            section_times["Parse Asset Pipeline Refresh"] = time.time() - start_time
            update_progress("Asset Pipeline Refresh Data", "Asset Pipeline Refresh Data parsed")

        player_build_info = []
        if parsing_options['player_build']:
            update_progress(message="Parsing player build information...")
            start_time = time.time()
            player_build_info = parse_player_build_info(log_file_path)
            section_times["Parse Player Build Info"] = time.time() - start_time
            update_progress("Player Build Information", "Player Build Information parsed")

        il2cpp_data = []
        if parsing_options['il2cpp']:
            update_progress(message="Parsing IL2CPP processing data...")
            start_time = time.time()
            il2cpp_data = parse_il2cpp_processing(log_file_path)
            section_times["Parse IL2CPP Processing"] = time.time() - start_time
            update_progress("IL2CPP Processing Data", "IL2CPP Processing Data parsed")

        # Parse Tundra build info
        tundra_info = []
        if parsing_options['tundra']:
            update_progress(message="Parsing Tundra build data...")
            start_time = time.time()
            tundra_info = parse_tundra_build_info(log_file_path)
            section_times["Parse Tundra Build Info"] = time.time() - start_time
            update_progress("Tundra Build Information", "Tundra Build Information parsed")

        domain_reloads = []
        has_domain_reloads = False
        if parsing_options['domain_reload']:
            update_progress(message="Parsing domain reload data...")
            start_time = time.time()
            domain_reloads = parse_domain_reloads(log_file_path)
            section_times["Parse Domain Reloads"] = time.time() - start_time
            update_progress("Domain Reload Data", "Domain Reload Data parsed")

        overall_time = time.time() - start_time_overall
        section_times["Total Processing Time"] = overall_time

        # Store all parsed data in the session state
        st.session_state.parsed_data = {
            'shader_df': shader_df,
            'shader_issues': shader_issues,
            'import_df': import_df,
            'loading_df': loading_df,
            'build_df': build_df,
            'total_build_size': total_build_size,
            'total_build_unit': total_build_unit,
            'refresh_df': refresh_df,
            'player_build_info': player_build_info,
            'il2cpp_data': il2cpp_data,
            'domain_reloads': domain_reloads,
            'has_domain_reloads': has_domain_reloads,
            'tundra_info': tundra_info,  
            'unity_version': unity_version,
            'section_times': section_times,
            'overall_time': overall_time
        }
        
        # Update progress message before closing the progress container
        update_progress(message="Preparing visualization...")
        progress_container.empty()
    else:
            # If data is already parsed, retrieve it from session state
            shader_df = st.session_state.parsed_data['shader_df']
            shader_issues = st.session_state.parsed_data['shader_issues']
            import_df = st.session_state.parsed_data['import_df']
            loading_df = st.session_state.parsed_data['loading_df']
            build_df = st.session_state.parsed_data['build_df']
            total_build_size = st.session_state.parsed_data['total_build_size']
            total_build_unit = st.session_state.parsed_data['total_build_unit']
            refresh_df = st.session_state.parsed_data['refresh_df']
            player_build_info = st.session_state.parsed_data['player_build_info']
            il2cpp_data = st.session_state.parsed_data['il2cpp_data']
            domain_reloads = st.session_state.parsed_data['domain_reloads']
            has_domain_reloads = st.session_state.parsed_data['has_domain_reloads']
            unity_version = st.session_state.parsed_data['unity_version']
            tundra_info = st.session_state.parsed_data['tundra_info']  # Retrieve tundra_info here
            section_times = st.session_state.parsed_data['section_times']
            overall_time = st.session_state.parsed_data['overall_time']
            


    # Check data completeness and show summary
    issues = check_log_data_completeness(log_file_path, shader_df, import_df, loading_df, build_df, refresh_df, player_build_info, unity_version)
    
    if issues:
        with st.expander("⚠️ Log Analysis Summary - Click to expand ⚠️", expanded=True):
            for issue in issues:
                st.write(issue)
            st.write("The analysis will proceed with available data.")
    else:
        st.success("✅ All data types were found in the log file. ✅ ")

    

    # Create a row with processing time summary and PDF export button side by side
    col1, col2 = st.columns([3, 1])

    # Put the processing time summary expander in the first column
    with col1:
        with st.expander("🕒 Processing Time Summary", expanded=False):
            # Create a dataframe for the timing data
            timing_data = []
            for section, execution_time in section_times.items():
                timing_data.append({
                    "Section": section,
                    "Execution Time (s)": round(execution_time, 3),
                    "Percentage": round((execution_time / overall_time) * 100, 1) if section != "Total Processing Time" else 100
                })
            
            timing_df = pd.DataFrame(timing_data)
            
            # Split into parsing and visualization sections
            parsing_df = timing_df[timing_df["Section"].str.startswith("Parse")]
            visualization_df = timing_df[timing_df["Section"].str.startswith("Visualize")]
            
            # Display in columns
            col1a, col2a = st.columns(2)
            
            with col1a:
                st.subheader("Parsing Times")
                parsing_fig = px.bar(
                    parsing_df,
                    y="Section",
                    x="Execution Time (s)",
                    text="Execution Time (s)",
                    color="Percentage",
                    orientation="h",
                    height=400
                )
                parsing_fig.update_traces(texttemplate="%{text:.3f}s", textposition="outside")
                st.plotly_chart(parsing_fig, use_container_width=True)
            
            with col2a:
                st.subheader("Visualization Times")
                viz_fig = px.bar(
                    visualization_df,
                    y="Section",
                    x="Execution Time (s)",
                    text="Execution Time (s)",
                    color="Percentage",
                    orientation="h",
                    height=400
                )
                viz_fig.update_traces(texttemplate="%{text:.3f}s", textposition="outside")
                st.plotly_chart(viz_fig, use_container_width=True)
            
            # Display the total time as a metric
            st.metric("Total Log Analysis Time", f"{overall_time:.2f} seconds")

    # Put the PDF export button in the second column, vertically centered
    with col2:
        if st.button("Generate PDF", key="pdf_button"):
            with st.spinner("Generating PDF report..."):
                # Collect all parsed data
                parsing_data = {
                    'shader_df': shader_df,
                    'import_df': import_df,
                    'loading_df': loading_df,
                    'build_df': build_df,
                    'refresh_df': refresh_df,
                    'player_build_info': player_build_info,
                    'il2cpp_data': il2cpp_data,
                    'domain_reloads': domain_reloads,
                    'unity_version': unity_version,
                    'total_build_size': total_build_size,
                    'total_build_unit': total_build_unit
                }
                
                # Generate the PDF
                pdf_buffer = generate_pdf_report(log_file_path, parsing_data)
                
                # Get filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"unity_log_analysis_{timestamp}.pdf"
                
                # Provide download link
                st.markdown(get_download_link(pdf_buffer, filename), unsafe_allow_html=True)
                st.success("PDF report generated!")
                

    # Create a summary section with timing metrics from all tabs
    st.subheader("📊 Performance Summary 📊")
    
    # Create a two-column layout
    left_col, right_col = st.columns([3, 2])

    # Put all metrics in the left column
    with left_col:
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

    # Put the pie chart in the right column
    with right_col:
        # Create pie chart data
        time_categories = []
        time_values = []

        if total_build_time is not None and total_build_time > 0:
            time_categories.append('Build Time')
            time_values.append(total_build_time)

        if total_loading_time is not None and total_loading_time > 0:
            time_categories.append('Loading Time')
            time_values.append(total_loading_time)

        if total_reload_time is not None and total_reload_time > 0:
            time_categories.append('Domain Reload Time')
            time_values.append(total_reload_time)

        if total_refresh_time is not None and total_refresh_time > 0:
            time_categories.append('Pipeline Refresh Time')
            time_values.append(total_refresh_time)

        if total_import_time is not None and total_import_time > 0:
            time_categories.append('Asset Import Time')
            time_values.append(total_import_time)

        if total_shader_time is not None and total_shader_time > 0:
            time_categories.append('Shader Compilation Time')
            time_values.append(total_shader_time)

        if time_categories and time_values:
            time_data = pd.DataFrame({
                'Category': time_categories,
                'Time': time_values
            })
            st.subheader("Time Distribution")
            fig = px.pie(
                time_data, 
                values='Time', 
                names='Category',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Calculate overall execution time
    #overall_time = time.time() - start_time_overall
    section_times["Total Processing Time"] = overall_time
    
    
    # Check which data types we have available
    has_build_info = bool(player_build_info)
    has_build_report = not build_df.empty
    has_loading_data = not loading_df.empty
    has_refresh_data = not refresh_df.empty
    has_import_data = not import_df.empty
    has_shader_data = not shader_df.empty and ('compilation_seconds' in shader_df.columns or 'shader_name' in shader_df.columns)
    has_il2cpp_data = bool(il2cpp_data)
    has_tundra_info = bool(tundra_info)
    has_domain_reloads = len(domain_reloads) > 0

    # Enhance build info with Tundra data if available
    if has_tundra_info and player_build_info:
        enhance_build_info_with_tundra(player_build_info, tundra_info)
        
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
    if has_il2cpp_data:
        tab_titles.append("IL2CPP Processing")
    
    # Initialize active tab in session state if it doesn't exist
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 0
    
    # If we don't have any data, show a message
    if not tab_titles:
        st.error("No actionable Unity build data found in the log file.")
        return
    
    # Create the tabs and track which one is clicked
    tabs = st.tabs(tab_titles)
    
    # Populate tabs based on available data
    tab_index = 0

    if has_build_info:
        with tabs[tab_index]:
            if "active_tab" not in st.session_state or st.session_state.active_tab != tab_index:
                st.session_state.active_tab = tab_index
            if st.session_state.active_tab == tab_index:
                update_spinner, spinner_container = show_big_spinner("Processing Player Build Information...")
                start_time = time.time()
                visualize_player_build_info(player_build_info)
                section_times["Visualize Player Build Info"] = time.time() - start_time
                spinner_container.empty()
        tab_index += 1

    if has_build_report:
        with tabs[tab_index]:
            if "active_tab" not in st.session_state or st.session_state.active_tab != tab_index:
                st.session_state.active_tab = tab_index
            if st.session_state.active_tab == tab_index:
                update_spinner, spinner_container = show_big_spinner("Analyzing Build Report...")
                start_time = time.time()
                visualize_build_report(build_df, total_build_size, total_build_unit)
                section_times["Visualize Build Report"] = time.time() - start_time
                spinner_container.empty()
        tab_index += 1
        
    if has_loading_data:
        with tabs[tab_index]:
            if "active_tab" not in st.session_state or st.session_state.active_tab != tab_index:
                st.session_state.active_tab = tab_index
            if st.session_state.active_tab == tab_index:
                update_spinner, spinner_container = show_big_spinner("Analyzing Project Loading Times...")
                start_time = time.time()
                visualize_loading_times(loading_df)
                section_times["Visualize Loading Times"] = time.time() - start_time
                spinner_container.empty()
        tab_index += 1

    if has_domain_reloads:
        with tabs[tab_index]:
            if "active_tab" not in st.session_state or st.session_state.active_tab != tab_index:
                st.session_state.active_tab = tab_index
            if st.session_state.active_tab == tab_index:
                update_spinner, spinner_container = show_big_spinner("Analyzing Domain Reloads...")
                start_time = time.time()
                visualize_domain_reloads(log_file_path)
                section_times["Visualize Domain Reloads"] = time.time() - start_time
                spinner_container.empty()
        tab_index += 1

    if has_refresh_data:
        with tabs[tab_index]:
            if "active_tab" not in st.session_state or st.session_state.active_tab != tab_index:
                st.session_state.active_tab = tab_index
            if st.session_state.active_tab == tab_index:
                update_spinner, spinner_container = show_big_spinner("Analyzing Asset Pipeline Refreshes...")
                start_time = time.time()
                visualize_pipeline_refreshes(refresh_df, log_file_path)
                section_times["Visualize Pipeline Refreshes"] = time.time() - start_time
                spinner_container.empty()
        tab_index += 1

    if has_import_data:
        with tabs[tab_index]:
            if "active_tab" not in st.session_state or st.session_state.active_tab != tab_index:
                st.session_state.active_tab = tab_index
            if st.session_state.active_tab == tab_index:
                update_spinner, spinner_container = show_big_spinner("Analyzing Asset Imports...")
                start_time = time.time()
                visualize_asset_imports(import_df)
                section_times["Visualize Asset Imports"] = time.time() - start_time
                spinner_container.empty()
        tab_index += 1

    if has_shader_data:
        with tabs[tab_index]:
            if "active_tab" not in st.session_state or st.session_state.active_tab != tab_index:
                st.session_state.active_tab = tab_index
            if st.session_state.active_tab == tab_index:
                update_spinner, spinner_container = show_big_spinner("Analyzing Shader Compilation Data...")
                start_time = time.time()
                visualize_shader_data(shader_df, shader_issues)
                section_times["Visualize Shader Data"] = time.time() - start_time
                spinner_container.empty()
        tab_index += 1
        
    if has_il2cpp_data:
        with tabs[tab_index]:
            if "active_tab" not in st.session_state or st.session_state.active_tab != tab_index:
                st.session_state.active_tab = tab_index
            if st.session_state.active_tab == tab_index:
                update_spinner, spinner_container = show_big_spinner("Analyzing IL2CPP Processing...")
                start_time = time.time()
                visualize_il2cpp_data(il2cpp_data)
                section_times["Visualize IL2CPP Data"] = time.time() - start_time
                spinner_container.empty()
