
import pandas as pd
import streamlit as st
import plotly.express as px

from Utils import *

def display_shader_issues(shader_issues):
    """Display shader errors and warnings in an organized way."""
    st.subheader("Shader Issues")
    
    # Display errors
    if shader_issues.get('errors'):
        with st.expander(f"⛔ Shader Errors ({len(shader_issues['errors'])})", expanded=len(shader_issues['errors']) > 0):
            for error in shader_issues['errors']:
                st.markdown(f"**{error['shader_name']}**: {error['message']}")
                st.markdown("---")
    
    # Display warnings
    if shader_issues.get('warnings'):
        with st.expander(f"⚠️ Shader Warnings ({len(shader_issues['warnings'])})", expanded=len(shader_issues['warnings']) > 0):
            for warning in shader_issues['warnings']:
                st.markdown(f"**{warning['shader_name']}**: {warning['message']}")
                st.markdown("---")

def visualize_shader_data(shader_df, shader_issues=None):
    st.header("Unity Shader Compilation Analytics")
    
    if shader_df.empty:
        st.warning("No shader compilation data found in the log.")
        
        # Still show errors/warnings if available
        if shader_issues and (shader_issues.get('errors') or shader_issues.get('warnings')):
            st.warning("No shader compilation performance data found, but shader issues were detected.")
            display_shader_issues(shader_issues)
        return
    
    # Check if we have any essential shader compilation data
    has_compilation_data = 'total_seconds' in shader_df.columns or 'shader_name' in shader_df.columns
    
    if not has_compilation_data:
        st.warning("No shader compilation performance data found in the log.")
        return
    
    # Sort dataframe by total time in descending order if the column exists
    if 'total_seconds' in shader_df.columns:
        sorted_df = shader_df.sort_values('total_seconds', ascending=False)
    else:
        sorted_df = shader_df  # No sorting if column doesn't exist
        st.info("Total processing time data not found. Some visualizations will be limited.")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Shaders", len(shader_df))
    with col2:
        total_time = shader_df['total_seconds'].sum() if 'total_seconds' in shader_df.columns else "N/A"
        st.metric("Total Processing Time", f"{total_time:.2f}s" if isinstance(total_time, (int, float)) else total_time)
    with col3:
        total_cpu_time = shader_df['compilation_cpu_time'].sum() if 'compilation_cpu_time' in shader_df.columns else "N/A"
        st.metric("Total CPU Time", f"{total_cpu_time:.2f}s" if isinstance(total_cpu_time, (int, float)) else total_cpu_time)
    with col4:
        total_variants = int(shader_df['compiled_variants'].sum()) if 'compiled_variants' in shader_df.columns else "N/A"
        st.metric("Total Variants Compiled", total_variants)
    
    # Only show visualization if we have total time and shader name data
    if 'total_seconds' in shader_df.columns and 'shader_name' in shader_df.columns:
        # Total processing time by shader
        st.subheader("Total Processing Time by Shader")
        
        fig = px.bar(
            sorted_df,
            x='shader_name',
            y='total_seconds',
            color='pass_name' if 'pass_name' in sorted_df.columns else None,
            hover_data=['compiled_variants', 'compilation_cpu_time'] if all(col in sorted_df.columns for col in ['compiled_variants', 'compilation_cpu_time']) else None,
            labels={'total_seconds': 'Total Processing Time (s)', 'shader_name': 'Shader Name'},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    elif 'shader_name' in shader_df.columns:
        st.info("Shader names found but processing time data is missing.")
    
    # Show top shaders by variant count after scriptable stripping
    if 'after_scriptable_stripping' in shader_df.columns and not shader_df['after_scriptable_stripping'].isna().all():
        st.subheader("Top Shaders with Most Variants After Stripping")
        
        # Sort by variants after scriptable stripping
        variant_sorted_df = shader_df.sort_values('after_scriptable_stripping', ascending=False)
        top_variants_df = variant_sorted_df.head(10)
        
        # Create a bar chart for variant counts
        fig = px.bar(
            top_variants_df,
            x='shader_name',
            y='after_scriptable_stripping',
            color='pass_name' if 'pass_name' in top_variants_df.columns else None,
            labels={
                'shader_name': 'Shader Name', 
                'after_scriptable_stripping': 'Remaining Variants After Stripping'
            },
            title="Top 10 Shaders by Final Variant Count After Stripping",
            height=500,
            text='after_scriptable_stripping'  # Show the exact variant count on bars
        )
        
        # Improve the layout
        fig.update_layout(
            xaxis={'categoryorder': 'total descending'},
            xaxis_tickangle=-45
        )
        
        # Format text on bars
        fig.update_traces(
            texttemplate='%{text:,}',  # Format with commas for thousands
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Also show the data in a table format for more details
        with st.expander("View Top Shader Variant Details"):
            display_cols = ['shader_name']
            if 'pass_name' in top_variants_df.columns:
                display_cols.append('pass_name')
            if 'pass_type' in top_variants_df.columns:
                display_cols.append('pass_type')
            
            display_cols.extend(['after_scriptable_stripping'])
            
            # Add percentage of total variants column
            if 'after_scriptable_stripping' in top_variants_df.columns:
                total_variants = shader_df['after_scriptable_stripping'].sum()
                top_variants_df['percentage_of_total'] = (
                    top_variants_df['after_scriptable_stripping'] / total_variants * 100
                ).round(2)
                display_cols.append('percentage_of_total')
                
            # Add other useful columns for comparison if available
            if 'full_variants' in top_variants_df.columns:
                display_cols.append('full_variants')
                
                # Calculate total reduction percentage from full to final
                top_variants_df['total_reduction_pct'] = (
                    (top_variants_df['full_variants'] - top_variants_df['after_scriptable_stripping']) / 
                    top_variants_df['full_variants'] * 100
                ).round(2)
                display_cols.append('total_reduction_pct')
            
            # Add compiled variants if available
            if 'compiled_variants' in top_variants_df.columns:
                display_cols.append('compiled_variants')
            
            # Format the display table
            display_df = top_variants_df[display_cols].copy()
            
            # Rename columns for display
            column_map = {
                'after_scriptable_stripping': 'Final Variants After Stripping',
                'percentage_of_total': 'Percentage of Total Variants (%)',
                'full_variants': 'Potential Variants Before Stripping',
                'total_reduction_pct': 'Total Reduction (%)',
                'compiled_variants': 'Actually Compiled Variants'
            }
            display_df = display_df.rename(columns=column_map)
            
            st.dataframe(display_df)

        # Add a stacked bar chart showing the stripping process for these top 10 shaders
        if all(col in shader_df.columns for col in ['full_variants', 'after_filtering', 'after_builtin_stripping', 'after_scriptable_stripping']):
            st.subheader("Variant Reduction Pipeline for Top Shaders")
            
            # Create a dataframe for the stripping stages
            stages_df = pd.DataFrame()
            
            for _, row in top_variants_df.iterrows():
                shader_name = row['shader_name']
                
                stages_df = pd.concat([stages_df, pd.DataFrame({
                    'Shader': shader_name,
                    'Stage': ['Full Variants', 'After Filtering', 'After Built-in Stripping', 'After Scriptable Stripping'],
                    'Variants': [
                        row['full_variants'],
                        row['after_filtering'],
                        row['after_builtin_stripping'],
                        row['after_scriptable_stripping']
                    ]
                })])
            
            # Create the stacked bar chart
            fig = px.line(
                stages_df,
                x='Stage',
                y='Variants',
                color='Shader',
                markers=True,
                title="Variant Reduction Through Pipeline Stages",
                height=500
            )
            
            # Add log scale option
            use_log_scale = st.checkbox("Use logarithmic scale for variants", value=True)
            if use_log_scale:
                fig.update_layout(yaxis_type="log")
                
                fig.update_layout(
                    yaxis=dict(
                        showexponent='all',
                        exponentformat='e',
                        dtick=1  # Creates tick marks for each power of 10
                    )
                )
            
            st.plotly_chart(fig, use_container_width=True)

    # Time distribution between shader types
    if 'shader_type' in shader_df.columns and 'total_seconds' in shader_df.columns:
        st.subheader("Time Distribution Analysis")
        
        # Create columns for different visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Group by shader type 
            type_times = shader_df.groupby('shader_type').agg(
                total_time=('total_seconds', 'sum'),
                count=('shader_name', 'count')
            ).reset_index()
            
            fig = px.pie(
                type_times, 
                values='total_time', 
                names='shader_type',
                title="Processing Time by Shader Type",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Regular shaders time components
            if 'processed_seconds' in shader_df.columns:
                regular_shaders = shader_df[shader_df['shader_type'] == 'regular']
                
                if not regular_shaders.empty:
                    processed_time = regular_shaders['processed_seconds'].sum()
                    compilation_time = regular_shaders['compilation_seconds'].sum() if 'compilation_seconds' in regular_shaders.columns else 0
                    serialization_time = regular_shaders['serialization_seconds'].sum() if 'serialization_seconds' in regular_shaders.columns else 0
                    
                    time_components = pd.DataFrame({
                        'Component': ['Processing', 'Compilation', 'Serialization'],
                        'Time': [processed_time, compilation_time, serialization_time]
                    })
                    
                    fig = px.pie(
                        time_components, 
                        values='Time', 
                        names='Component',
                        title="Regular Shader Time Distribution",
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)

    # Add processing time by pass name if available
    if 'pass_name' in shader_df.columns and 'total_seconds' in shader_df.columns and not shader_df['pass_name'].isna().all():
        st.subheader("Processing Time by Pass Name")
        
        # Group by pass name and sum processing times
        pass_name_times = shader_df.groupby('pass_name').agg(
            total_time=('total_seconds', 'sum'),
            avg_time=('total_seconds', 'mean'),
            count=('total_seconds', 'count'),
            total_variants=('compiled_variants', 'sum') if 'compiled_variants' in shader_df.columns else (None, None)
        ).reset_index().sort_values('total_time', ascending=False)
        
        # Create formatted columns for display
        pass_name_times['avg_time_formatted'] = pass_name_times['avg_time'].apply(lambda x: f"{x:.3f}s")
        pass_name_times['total_time_formatted'] = pass_name_times['total_time'].apply(lambda x: f"{x:.2f}s")
        
        # Bar chart of processing time by pass name
        fig = px.bar(
            pass_name_times,
            x='pass_name',
            y='total_time',
            text=pass_name_times['count'],
            labels={'pass_name': 'Pass Name', 'total_time': 'Total Processing Time (s)', 'count': 'Shader Count'},
            height=400,
            color='count'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Display the detailed table
        with st.expander("View Pass Name Processing Details"):
            display_cols = ['pass_name', 'count', 'total_time_formatted', 'avg_time_formatted']
            if 'total_variants' in pass_name_times.columns and not pass_name_times['total_variants'].isna().all():
                display_cols.append('total_variants')
            st.dataframe(pass_name_times[display_cols])
    
    # Add processing time by pass type if available
    if 'pass_type' in shader_df.columns and 'total_seconds' in shader_df.columns and not shader_df['pass_type'].isna().all():
        st.subheader("Processing Time by Pass Type")
        
        # Group by pass type and sum processing times
        pass_type_times = shader_df.groupby('pass_type').agg(
            total_time=('total_seconds', 'sum'),
            avg_time=('total_seconds', 'mean'),
            count=('total_seconds', 'count'),
            total_variants=('compiled_variants', 'sum') if 'compiled_variants' in shader_df.columns else (None, None)
        ).reset_index().sort_values('total_time', ascending=False)
        
        # Create a more detailed table
        pass_type_times['avg_time_formatted'] = pass_type_times['avg_time'].apply(lambda x: f"{x:.3f}s")
        pass_type_times['total_time_formatted'] = pass_type_times['total_time'].apply(lambda x: f"{x:.2f}s")
        
        # Bar chart of processing time by pass type
        fig = px.bar(
            pass_type_times,
            x='pass_type',
            y='total_time',
            text=pass_type_times['count'],
            labels={'pass_type': 'Pass Type', 'total_time': 'Total Processing Time (s)', 'count': 'Shader Count'},
            height=400,
            color='count'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Display the detailed table
        with st.expander("View Pass Type Processing Details"):
            display_cols = ['pass_type', 'count', 'total_time_formatted', 'avg_time_formatted']
            if 'total_variants' in pass_type_times.columns and not pass_type_times['total_variants'].isna().all():
                display_cols.append('total_variants')
            st.dataframe(pass_type_times[display_cols])
    
    # Only show variant reduction if we have the necessary columns
    variant_columns = ['full_variants', 'after_filtering', 'after_builtin_stripping', 'after_scriptable_stripping']
    if 'shader_name' in shader_df.columns and any(col in shader_df.columns for col in variant_columns):
        available_variants = [col for col in variant_columns if col in shader_df.columns]
        
        if available_variants:
            # Variant reduction pipeline
            st.subheader("Shader Variant Reduction")
            
            # Add log scale toggle
            use_log_scale_variants = st.checkbox("Use logarithmic scale for variant counts", value=True)
            
            variant_df = sorted_df.melt(
                id_vars=['shader_name', 'pass_name'] if 'pass_name' in sorted_df.columns else ['shader_name'],
                value_vars=available_variants,
                var_name='Pipeline Stage',
                value_name='Variant Count'
            )
            
            fig = px.line(
                variant_df,
                x='Pipeline Stage',
                y='Variant Count',
                color='shader_name',
                markers=True,
                line_shape='linear',
                height=500
            )
            
            # Apply log scale if selected
            if use_log_scale_variants:
                fig.update_layout(yaxis_type="log")
                
                fig.update_layout(
                    yaxis=dict(
                        showexponent='all',
                        exponentformat='e',
                        dtick=1  # Creates tick marks for each power of 10
                    )
                )
                
            st.plotly_chart(fig, use_container_width=True)
    
    # Only show cache analysis if we have the necessary columns
    cache_columns = ['local_cache_hits', 'remote_cache_hits', 'compiled_variants']
    cpu_columns = ['local_cache_cpu_time', 'remote_cache_cpu_time', 'compilation_cpu_time']
    
    if any(col in shader_df.columns for col in cache_columns) or any(col in shader_df.columns for col in cpu_columns):
        # Cache effectiveness
        st.subheader("Cache Hit Analysis")
        col1, col2 = st.columns(2)
        
        if all(col in shader_df.columns for col in cache_columns):
            with col1:
                cache_data = {
                    'Category': ['Local Cache Hits', 'Remote Cache Hits', 'Compiled Variants'],
                    'Count': [
                        shader_df['local_cache_hits'].sum(),
                        shader_df['remote_cache_hits'].sum(),
                        shader_df['compiled_variants'].sum()
                    ]
                }
                fig = px.pie(cache_data, values='Count', names='Category')
                st.plotly_chart(fig, use_container_width=True)
        
        if all(col in shader_df.columns for col in cpu_columns):
            with col2:
                # CPU time distribution
                cpu_data = {
                    'Category': ['Local Cache CPU', 'Remote Cache CPU', 'Compilation CPU'],
                    'Time': [
                        shader_df['local_cache_cpu_time'].sum(),
                        shader_df['remote_cache_cpu_time'].sum(),
                        shader_df['compilation_cpu_time'].sum()
                    ]
                }
                fig = px.pie(cpu_data, values='Time', names='Category')
                st.plotly_chart(fig, use_container_width=True)
    # List of shaders with local cache hits
    if 'local_cache_hits' in shader_df.columns:
        st.subheader("Shaders with Local Cache Hits")
        shaders_with_cache_hits = shader_df[shader_df['local_cache_hits'] > 0].sort_values('local_cache_hits', ascending=False)
        
        if not shaders_with_cache_hits.empty:
            display_df = shaders_with_cache_hits.copy()
            display_df['local_cache_hits_formatted'] = display_df['local_cache_hits'].apply(lambda x: f"{x} hits")
            
            columns_to_display = ['shader_name']
            if 'pass_name' in display_df.columns:
                columns_to_display.append('pass_name')
            columns_to_display.append('local_cache_hits_formatted')
            
            st.dataframe(display_df[columns_to_display])
        else:
            st.info("No local cache hits were found for any shaders.")
    
    if shader_issues and (shader_issues.get('errors') or shader_issues.get('warnings')):
        display_shader_issues(shader_issues)
           
    # Raw data table with any data we have
    if not shader_df.empty:
        with st.expander("View Shader Compilation Raw Data"):
            st.dataframe(sorted_df)
