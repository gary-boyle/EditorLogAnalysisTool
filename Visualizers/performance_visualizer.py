import streamlit as st
import plotly.express as px
import pandas as pd

def visualize_performance_report(performance_df):
    """Visualize Unity Performance Report data."""
    st.header("Unity Performance Report Analysis")
    
    if performance_df.empty:
        st.warning("No performance report data found in the log.")
        return
    
    # Summary metrics
    total_operations = len(performance_df)
    total_samples = performance_df['samples'].sum() if 'samples' in performance_df.columns else 0
    max_percentage = performance_df['percentage'].max() if 'percentage' in performance_df.columns else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Operations", total_operations)
    with col2:
        st.metric("Total Samples", total_samples)
    with col3:
        st.metric("Max Time Percentage", f"{max_percentage:.2f}%")
    
    # Category breakdown
    st.subheader("Performance by Category")
    if 'category' in performance_df.columns:
        category_df = performance_df.groupby('category').agg(
            total_time_us=('total_us', 'sum'),
            operation_count=('operation', 'count'),
            sample_count=('samples', 'sum')
        ).reset_index().sort_values('total_time_us', ascending=False)
        
        # Convert total time to seconds for better readability
        category_df['total_time_s'] = category_df['total_time_us'] / 1000000
        
        fig = px.bar(
            category_df,
            x='category',
            y='total_time_s',
            color='operation_count',
            text='operation_count',
            hover_data=['sample_count'],
            labels={
                'category': 'Category', 
                'total_time_s': 'Total Time (s)',
                'operation_count': 'Number of Operations',
                'sample_count': 'Total Samples'
            },
            height=500
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    # Top slowest operations
    st.subheader("Top 20 Slowest Operations (by Total Time)")
    sorted_df = performance_df.sort_values('total_us', ascending=False)
    top_n = min(20, len(sorted_df))
    top_operations = sorted_df.head(top_n).copy()
    
    # Convert to seconds for better readability
    top_operations['total_s'] = top_operations['total_us'] / 1000000
    top_operations['avg_s'] = top_operations['avg_us'] / 1000000
    top_operations['peak_s'] = top_operations['peak_us'] / 1000000
    
    fig = px.bar(
        top_operations,
        x='operation',
        y='total_s',
        color='samples',
        hover_data=['avg_s', 'peak_s', 'percentage'],
        labels={
            'operation': 'Operation',
            'total_s': 'Total Time (s)',
            'samples': 'Number of Samples',
            'avg_s': 'Average Time (s)',
            'peak_s': 'Peak Time (s)',
            'percentage': 'Percentage of Total Time'
        },
        height=600
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Operations with highest peak times
    st.subheader("Top 10 Operations with Highest Peak Times")
    peak_sorted = performance_df.sort_values('peak_us', ascending=False).head(10)
    peak_sorted['peak_s'] = peak_sorted['peak_us'] / 1000000
    
    fig = px.bar(
        peak_sorted,
        x='operation',
        y='peak_s',
        color='peak_factor',
        hover_data=['samples', 'avg_value', 'avg_unit'],
        labels={
            'operation': 'Operation',
            'peak_s': 'Peak Time (s)',
            'peak_factor': 'Peak Factor (x)',
            'samples': 'Number of Samples',
            'avg_value': 'Average Value',
            'avg_unit': 'Average Unit'
        },
        height=500
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # High peak factor operations
    st.subheader("Top 10 Operations with Highest Peak Factor")
    factor_sorted = performance_df.sort_values('peak_factor', ascending=False).head(10)
    
    fig = px.bar(
        factor_sorted,
        x='operation',
        y='peak_factor',
        color='samples',
        hover_data=['peak_value', 'peak_unit', 'avg_value', 'avg_unit'],
        labels={
            'operation': 'Operation',
            'peak_factor': 'Peak Factor (x)',
            'samples': 'Number of Samples'
        },
        height=500
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed data table
    with st.expander("View All Performance Report Data"):
        # Create a more readable version of the dataframe for display
        display_df = performance_df[['operation', 'category', 'samples', 'avg_value', 'avg_unit', 
                                    'peak_value', 'peak_unit', 'peak_factor', 
                                    'total_value', 'total_unit', 'percentage']].copy()
        st.dataframe(display_df)
