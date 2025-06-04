import streamlit as st
import plotly.express as px
import pandas as pd

from Utils import *

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
        
        # Use a reference start time (now)
        import datetime
        reference_time = datetime.datetime.now()
        
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
                
            # Convert seconds to datetime objects
            start_time = reference_time + datetime.timedelta(seconds=cumulative_time)
            end_time = reference_time + datetime.timedelta(seconds=cumulative_time + duration_sec)
            
            timeline_data.append({
                'description': description,
                'start_time': start_time,
                'end_time': end_time,
                'duration_sec': duration_sec
            })
            
            # Update cumulative time for next step
            cumulative_time += duration_sec
        
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
                    'duration_sec': 'Duration (seconds)'
                },
                height=600
            )
            
            # Improve the layout
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Build Step"
            )
            
            # Format x-axis to show only the time portion
            fig.update_xaxes(
                tickformat="%H:%M:%S",
                tickangle=0
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not create timeline: no valid duration data in build steps.")

    # Show Tundra build information if available
    if 'tundra_info' in build_info and build_info['tundra_info']:
        st.subheader("🏗 Tundra Build Information")
        tundra_data = build_info['tundra_info']
        
        for i, tundra in enumerate(tundra_data):
            with st.container():
                if i > 0:
                    st.markdown("---")
                    
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Build Time", f"{tundra['build_time_seconds']:.2f}s")
                with col2:
                    st.metric("Items Updated", f"{tundra['items_updated']}")
                with col3:
                    st.metric("Items Evaluated", f"{tundra['items_evaluated']}")
                
                # Calculate and display update ratio
                if tundra['items_evaluated'] > 0:
                    update_ratio = (tundra['items_updated'] / tundra['items_evaluated']) * 100
                    st.progress(update_ratio / 100)
                    st.text(f"Update Ratio: {update_ratio:.1f}% ({tundra['items_updated']} of {tundra['items_evaluated']} items needed updating)")

    # Raw data in a well-formatted table
    with st.expander("View Build Step Details"):
        display_df = sorted_steps_df.copy()
        display_df['duration'] = display_df['duration_sec'].apply(lambda x: f"{x:.3f}s")
        display_df['percentage'] = display_df['percentage'].apply(lambda x: f"{x:.2f}%")
        st.dataframe(display_df[['description', 'duration', 'percentage']])

def enhance_build_info_with_tundra(player_build_info, tundra_info):
    """Update player build info with Tundra build information if available."""
    if tundra_info and player_build_info:
        # Add Tundra info to player build info
        for build in player_build_info:
            build['tundra_info'] = tundra_info
        return True
    return False
