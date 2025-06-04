import pandas as pd
import streamlit as st
import plotly.express as px

from Utils import *

def visualize_il2cpp_data(il2cpp_data):
    
    st.header("IL2CPP Processing Analysis")
    
    if not il2cpp_data:
        st.warning("No IL2CPP processing data found in the log.")
        
        # Add debug information to help troubleshoot
        with st.expander("Debug Information"):
            st.write("""
            IL2CPP data is typically found in patterns like:
            
            ```
            - EILPP : Unity.Transforms.Hybrid : : 153ms (~152ms)
              - EILPP : Unity.Transforms.Hybrid : WriteAssembly: 1ms
            ```
            
            or
            
            ```
            [ 896/1250  2s] ILPostProcess Library/Bee/artifacts/1900b0aPDevDbg.dag/post-processed/Unity.Physics.dll
            ```
            
            Please check if your log file contains these patterns.
            """)
        return
    
    # Calculate summary metrics
    total_assemblies = len(il2cpp_data)
    total_time_ms = sum(entry['total_time_ms'] for entry in il2cpp_data)
    total_time_sec = total_time_ms / 1000
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Assemblies Processed", total_assemblies)
    with col2:
        st.metric("Total Processing Time", f"{total_time_sec:.2f}s")
    with col3:
        st.metric("Average Time per Assembly", f"{total_time_sec / total_assemblies:.2f}s" if total_assemblies > 0 else "N/A")
    
    # Sort assemblies by processing time
    sorted_data = sorted(il2cpp_data, key=lambda x: x['total_time_ms'], reverse=True)
    
    # Create DataFrame for the assemblies
    assembly_data = []
    for entry in sorted_data:
        assembly_data.append({
            'Assembly': entry['assembly'],
            'Total Time (ms)': entry['total_time_ms'],
            'Self Time (ms)': entry.get('self_time_ms', entry['total_time_ms']),
            'Steps': len(entry.get('steps', [])),
            'Overhead (ms)': entry['total_time_ms'] - sum(step['time_ms'] for step in entry.get('steps', []))
        })
    
    assembly_df = pd.DataFrame(assembly_data)
    
    # Show bar chart of top assemblies by processing time
    st.subheader("Top Assemblies by IL2CPP Processing Time")
    
    # Take top 15 assemblies for the chart
    top_assemblies_df = assembly_df.head(15).copy()
    top_assemblies_df['Total Time (s)'] = top_assemblies_df['Total Time (ms)'] / 1000
    
    fig = px.bar(
        top_assemblies_df,
        x='Assembly',
        y='Total Time (s)',
        text='Total Time (s)',
        height=500,
        color='Total Time (s)',
        labels={'Total Time (s)': 'Processing Time (seconds)'}
    )
    fig.update_traces(texttemplate='%{text:.2f}s', textposition='outside')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed breakdown of an assembly if selected
    st.subheader("Assembly Processing Details")
    
    # Let user select an assembly to see detailed steps
    selected_assembly = st.selectbox(
        "Select an assembly to see detailed processing steps:",
        [entry['assembly'] for entry in sorted_data],
        format_func=lambda x: f"{x} ({next(entry['total_time_ms'] for entry in sorted_data if entry['assembly'] == x):.0f}ms)"
    )
    
    # Find the selected assembly data
    selected_data = next((entry for entry in sorted_data if entry['assembly'] == selected_assembly), None)
    
    if selected_data:
        # Calculate step data
        steps = selected_data.get('steps', [])
        
        if steps:
            step_data = []
            for step in steps:
                step_data.append({
                    'Process': step['process'],
                    'Time (ms)': step['time_ms'],
                    'Percentage': (step['time_ms'] / selected_data['total_time_ms']) * 100
                })
            
            step_df = pd.DataFrame(step_data)
            
            # Create pie chart of processing steps
            fig = px.pie(
                step_df,
                values='Time (ms)',
                names='Process',
                title=f"{selected_assembly} Processing Steps",
                height=400
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
            # Show step data table
            st.write("### Processing Steps")
            step_df['Percentage'] = step_df['Percentage'].apply(lambda x: f"{x:.2f}%")
            step_df['Time'] = step_df['Time (ms)'].apply(lambda x: f"{x}ms")
            st.dataframe(step_df[['Process', 'Time', 'Percentage']])
        else:
            st.info(f"No detailed processing steps available for {selected_assembly}")
        
        # Show total time and self time
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Time", f"{selected_data['total_time_ms']}ms")
        with col2:
            st.metric("Self Time", f"{selected_data.get('self_time_ms', selected_data['total_time_ms'])}ms")
    
    # Show all assembly data in a table
    st.subheader("All IL2CPP Processing Data")
    with st.expander("Show Raw Assembly Data"):
        display_df = assembly_df.copy()
        display_df['Total Time'] = display_df['Total Time (ms)'].apply(lambda x: f"{x}ms")
        display_df['Self Time'] = display_df['Self Time (ms)'].apply(lambda x: f"{x}ms")
        st.dataframe(display_df[['Assembly', 'Total Time', 'Self Time', 'Steps']])
