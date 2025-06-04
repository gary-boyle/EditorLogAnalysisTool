import pandas as pd
import streamlit as st
import plotly.express as px

from Utils import *
from Parsers import *

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
    
    # Store the selected reload index in session state to preserve it during reruns
    if 'selected_reload_idx' not in st.session_state:
        st.session_state.selected_reload_idx = 0
    
    selected_reload_idx = st.selectbox(
        "Select a domain reload to analyze in detail:",
        range(len(domain_reloads)),
        index=st.session_state.selected_reload_idx,
        format_func=lambda i: f"Reload #{i}: {domain_reloads[i].get('timestamp_str')} ({domain_reloads[i].get('reset_time', 0) or 0:.2f}s)"
    )
    
    # Update the session state
    st.session_state.selected_reload_idx = selected_reload_idx
    
    # Create key for the button to prevent id conflicts
    button_key = f"analyze_domain_reload_{selected_reload_idx}"
    
    if st.button("Analyze Selected Domain Reload", key=button_key):
        # Store the current tab index in session state
        # Find which tab this is (Domain Reloads)
        tab_titles = []
        if 'player_build_info' in st.session_state.parsed_data and st.session_state.parsed_data['player_build_info']:
            tab_titles.append("Player Build Performance")
        if 'build_df' in st.session_state.parsed_data and not st.session_state.parsed_data['build_df'].empty:
            tab_titles.append("Build Report")
        if 'loading_df' in st.session_state.parsed_data and not st.session_state.parsed_data['loading_df'].empty:
            tab_titles.append("Project Loading")
        if 'domain_reloads' in st.session_state.parsed_data and st.session_state.parsed_data['domain_reloads']:
            tab_titles.append("Domain Reloads")
            # Set the active tab to Domain Reloads
            st.session_state.active_tab = tab_titles.index("Domain Reloads")
        
        with st.spinner("Analyzing domain reload details..."):
            # Visualize the selected domain reload
            visualize_domain_reload_details(domain_reloads[selected_reload_idx])

def visualize_domain_reload_details(reload_entry):
    st.header("Domain Reload Analysis")
    
    # Debug information 
    with st.expander("Debug: Raw Domain Reload Data", expanded=False):
        st.json(reload_entry)
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Domain Reload Time", f"{reload_entry.get('reset_time', 0):.2f}s")
    with col2:
        st.metric("Profiling Time", f"{reload_entry.get('profiling_time_ms', 0) / 1000:.2f}s")
    with col3:
        # Display the total time in a more human-readable format
        total_time = reload_entry.get('reset_time', 0)
        if total_time > 60:
            minutes = int(total_time // 60)
            seconds = total_time % 60
            st.metric("In Minutes", f"{minutes}m {seconds:.1f}s")
    
    # Check if we have operations data
    operations = reload_entry.get('operations', [])
    
    if not operations:
        st.warning("No detailed operations data found for this domain reload.")
        st.info("""
            This log may not contain detailed profiling information. To enable detailed domain reload profiling:
            
            1. In Unity, open the Editor Log window (Window > General > Console)
            2. Click on the Console window dropdown menu and select "Open Editor Log"
            3. In the Developer Console dropdown menu, enable "Development Build" and "Deep Profiling" options
            4. Trigger a domain reload by making a code change
            5. Check the log file for detailed profiling information
        """)
        return
    
    # Process operations for visualization
    # Flatten the hierarchy for a table view first
    flat_ops = []
    
    def process_operation(op, depth=0):
        name = ("  " * depth) + op['name']  # Add indentation to name
        flat_ops.append({
            'name': name,
            'raw_name': op['name'],
            'time_ms': op['time_ms'],
            'time_s': op['time_ms'] / 1000,
            'depth': depth
        })
        
        for child in op.get('children', []):
            process_operation(child, depth + 1)
    
    # Process all top-level operations
    for op in operations:
        process_operation(op)
    
    # Create a DataFrame
    if flat_ops:
        op_df = pd.DataFrame(flat_ops)
        
        # Calculate percentage
        total_ms = reload_entry.get('profiling_time_ms', op_df['time_ms'].sum())
        if total_ms > 0:
            op_df['percentage'] = op_df['time_ms'] / total_ms * 100
        else:
            op_df['percentage'] = 0
        
        # Sort by time for the top operations view (ignoring hierarchy)
        top_ops = op_df.sort_values('time_ms', ascending=False).head(15).copy()
        
        # Bar chart of top operations
        st.subheader("Top Operations by Time")
        
        try:
            fig = px.bar(
                top_ops,
                y='raw_name',
                x='time_s',
                orientation='h',
                text=top_ops['percentage'].apply(lambda x: f"{x:.1f}%"),
                labels={'time_s': 'Time (seconds)', 'raw_name': 'Operation'},
                height=600,
                color='percentage',
                color_continuous_scale='Viridis'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(yaxis_tickangle=0)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating visualization: {str(e)}")
            st.write("Error details:", e)
        
        # Show the hierarchical view
        st.subheader("Hierarchical Operations View")
        
        # Display as a formatted table to preserve hierarchy
        st.dataframe(
            op_df[['name', 'time_ms', 'percentage']].rename(
                columns={'name': 'Operation', 'time_ms': 'Time (ms)', 'percentage': '% of Total'}
            ).style.format({
                'Time (ms)': '{:.0f}',
                '% of Total': '{:.1f}%'
            })
        )
        
        # Add sunburst chart for hierarchical visualization
        st.subheader("Operations Hierarchy")
        
        # Create hierarchical data for sunburst
        try:
            # We need to prepare a different structure for the sunburst
            sunburst_data = []
            
            def build_path(op, path=""):
                current_path = path + "/" + op['name'] if path else op['name']
                sunburst_data.append({
                    'path': current_path,
                    'time_ms': op['time_ms'],
                    'name': op['name']
                })
                
                for child in op.get('children', []):
                    build_path(child, current_path)
            
            # Process all top-level operations
            for op in operations:
                build_path(op)
            
            if sunburst_data:
                # Create a DataFrame for the sunburst
                sb_df = pd.DataFrame(sunburst_data)
                
                # Add an ID column
                sb_df['id'] = sb_df['path']
                
                # Add a parent column
                sb_df['parent'] = sb_df['path'].apply(
                    lambda p: "/".join(p.split("/")[:-1]) if "/" in p else ""
                )
                
                fig = px.sunburst(
                    sb_df,
                    ids='id',
                    names='name',
                    parents='parent',
                    values='time_ms',
                    color='time_ms',
                    color_continuous_scale='RdBu',
                    height=700
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not create hierarchy visualization: {str(e)}")
    else:
        st.warning("No valid operations data found for visualization.")
