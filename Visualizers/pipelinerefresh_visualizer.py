import pandas as pd
import streamlit as st
import plotly.express as px

from Utils import *
from Parsers import *


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
        cumulative_time = 0

        # Use a reference start time (now)
        import datetime
        reference_time = datetime.datetime.now()

        # Assume operations are sequential for visualization purposes
        for op in refresh_entry['operations']:
            # Convert seconds to datetime objects
            start_time = reference_time + datetime.timedelta(seconds=cumulative_time)
            end_time = reference_time + datetime.timedelta(seconds=cumulative_time + op['time_ms']/1000)
            
            timeline_data.append({
                'Operation': op['name'],
                'start_time': start_time,
                'end_time': end_time,
                'duration_sec': op['time_ms'] / 1000,
                'Percentage': (op['time_ms'] / (refresh_entry['total_time'] * 1000)) * 100
            })
            
            # Update cumulative time for next operation
            cumulative_time += op['time_ms'] / 1000

        timeline_df = pd.DataFrame(timeline_data)

        fig = px.timeline(
            timeline_df,
            x_start='start_time',
            x_end='end_time',
            y='Operation',
            color='Percentage',
            labels={
                'Percentage': 'Percentage of Total Time'
            },
            height=600,
            color_continuous_scale='Viridis'
        )

        # Format x-axis to show only the time portion
        fig.update_xaxes(
            tickformat="%H:%M:%S",
            tickangle=0
        )

        fig.update_layout(
            xaxis_title="Time",
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
    

    
    # Raw data table
    with st.expander("View Asset Pipeline Refresh Raw Data"):
        st.dataframe(sorted_df[['timestamp_str', 'refresh_id', 'initiator', 'total_time']])

