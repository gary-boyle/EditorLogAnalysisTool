import streamlit as st
import plotly.express as px

from Utils import *

def visualize_asset_imports(import_df):
    st.header("Unity Asset Import Analytics")
    
    if import_df.empty:
        st.warning("No asset import data found in the log.")
        return
    
    # Sort by import time descending
    sorted_df = import_df.sort_values('import_time_seconds', ascending=False)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Assets Imported", len(import_df))
    with col2:
        st.metric("Total Import Time", f"{import_df['import_time_seconds'].sum():.2f}s")
    with col3:
        st.metric("Average Import Time", f"{import_df['import_time_seconds'].mean():.4f}s")
    
    # Top slowest imports
    st.subheader("Top 10 Slowest Asset Imports")
    top_n = min(20, len(sorted_df))
    top_imports = sorted_df.head(top_n)
    
    fig = px.bar(
        top_imports,
        x='asset_name',
        y='import_time_seconds',
        color='importer_type',
        hover_data=['asset_path', 'file_extension'],
        labels={'import_time_seconds': 'Import Time (s)', 'asset_name': 'Asset Name'},
        height=500
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Import time by file extension
    if not sorted_df['file_extension'].empty:
        st.subheader("Import Time by File Type")
        ext_df = sorted_df.groupby('file_extension').agg(
            total_time=('import_time_seconds', 'sum'),
            count=('import_time_seconds', 'count'),
            avg_time=('import_time_seconds', 'mean')
        ).reset_index().sort_values('total_time', ascending=False)
        
        fig = px.bar(
            ext_df,
            x='file_extension',
            y='total_time',
            color='count',
            text='count',
            labels={
                'file_extension': 'File Extension', 
                'total_time': 'Total Import Time (s)',
                'count': 'Number of Files'
            },
            height=500
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    # Importer type distribution
    st.subheader("Assets by Importer Type")
    importer_counts = sorted_df['importer_type'].value_counts().reset_index()
    importer_counts.columns = ['Importer Type', 'Count']
    
    fig = px.pie(
        importer_counts, 
        values='Count', 
        names='Importer Type',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Distribution of import times
    st.subheader("Distribution of Import Times")
    fig = px.histogram(
        sorted_df,
        x='import_time_seconds',
        nbins=50,
        labels={'import_time_seconds': 'Import Time (s)'},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw data table
    with st.expander("View Asset Import Raw Data"):
        st.dataframe(sorted_df)
