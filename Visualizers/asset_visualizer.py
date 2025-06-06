import streamlit as st
import plotly.express as px
import pandas as pd

from Utils import *

def visualize_asset_imports(import_df, worker_stats_df=None):
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
        if 'timestamp' in sorted_df.columns and sorted_df['timestamp'].notna().any():
            # Calculate total time using timestamps
            min_time = sorted_df['timestamp'].min()
            max_time = sorted_df['timestamp'].max()
            total_time = (max_time - min_time).total_seconds()
            st.metric("Total Processing Time", f"{total_time:.2f}s")
        else:
            st.metric("Total Import Time", f"{sorted_df['import_time_seconds'].sum():.2f}s")
    with col3:
        st.metric("Average Import Time", f"{sorted_df['import_time_seconds'].mean():.4f}s")
    
    # Top slowest imports
    st.subheader("Top 10 Slowest Asset Imports")
    top_n = min(20, len(sorted_df))
    top_imports = sorted_df.head(top_n)
    
    fig = px.bar(
        top_imports,
        x='asset_name',
        y='import_time_seconds',
        color='importer_type',
        hover_data=['asset_path', 'file_extension', 'worker_id'],
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
    
    # Worker thread analysis (if available)
    if hasattr(import_df, 'worker_stats'):
        worker_stats_df = import_df.worker_stats
        st.header("Worker Thread Analysis")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Number of Worker Threads", len(worker_stats_df))
        
        with col2:
            total_cpu_time = worker_stats_df['total_time'].sum() if len(worker_stats_df) > 0 else 0
            st.metric("Total CPU Time", f"{total_cpu_time:.2f}s", 
                    help="Combined processing time across all worker threads")
        
        with col3:
            if len(worker_stats_df) > 0:
                effective_time = total_cpu_time / len(worker_stats_df)
                st.metric("Effective Processing Time", f"{effective_time:.2f}s", 
                        help="Estimated wall-clock time (Total CPU Time ÷ Number of Workers). " +
                            "This approximates the actual time spent importing assets when using multithreading.")
        
        # Main Thread vs Worker Threads comparison
        st.subheader("Main Thread vs Worker Threads Time Comparison")
        
        # Calculate time spent on main thread vs worker threads
        main_thread_imports = import_df[import_df['worker_id'].isna()]
        worker_thread_imports = import_df[import_df['worker_id'].notna()]
        
        main_thread_time = main_thread_imports['import_time_seconds'].sum() if not main_thread_imports.empty else 0
        worker_threads_time = worker_thread_imports['import_time_seconds'].sum() if not worker_thread_imports.empty else 0
        
        # Create comparison dataframe
        thread_comparison = pd.DataFrame([
            {"Thread Type": "Main Thread", "Import Time (s)": main_thread_time, "Number of Imports": len(main_thread_imports)},
            {"Thread Type": "Worker Threads", "Import Time (s)": worker_threads_time, "Number of Imports": len(worker_thread_imports)}
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Time comparison chart
            fig = px.bar(
                thread_comparison,
                x="Thread Type",
                y="Import Time (s)",
                color="Thread Type",
                text="Import Time (s)",
                labels={"Import Time (s)": "Total Import Time (seconds)"},
                height=400
            )
            fig.update_traces(texttemplate='%{text:.2f}s', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Import count comparison
            fig = px.bar(
                thread_comparison,
                x="Thread Type",
                y="Number of Imports",
                color="Thread Type",
                text="Number of Imports",
                labels={"Number of Imports": "Number of Assets Imported"},
                height=400
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        # Worker thread utilization
        st.subheader("Worker Thread Utilization")
        fig = px.bar(
            worker_stats_df.sort_values('worker_id'),
            x='worker_id',
            y='total_time',
            color='imports',
            text='imports',
            labels={
                'worker_id': 'Worker Thread ID', 
                'total_time': 'Total Processing Time (s)', 
                'imports': 'Number of Imports'
            },
            height=400
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Import distribution across worker threads
        st.subheader("Asset Imports by Worker Thread")
        if 'worker_id' in import_df.columns and not worker_thread_imports.empty:
            worker_import_counts = worker_thread_imports['worker_id'].value_counts().reset_index()
            worker_import_counts.columns = ['Worker Thread', 'Number of Imports']
            
            fig = px.pie(
                worker_import_counts,
                values='Number of Imports',
                names='Worker Thread',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display efficiency calculation
            if main_thread_time > 0 and worker_threads_time > 0:
                efficiency = (worker_threads_time / (main_thread_time + worker_threads_time)) * 100
                st.info(f"**Parallelization Efficiency**: {efficiency:.1f}% of import work is parallelized through worker threads.", 
                    icon="ℹ️")
            
    if worker_stats_df is not None and not worker_stats_df.empty:
        with st.expander("View Worker Thread Stats"):
            st.dataframe(worker_stats_df)