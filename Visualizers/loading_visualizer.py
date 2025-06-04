import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from Utils import *

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
