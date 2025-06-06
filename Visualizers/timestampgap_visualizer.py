import streamlit as st
import pandas as pd
import plotly.express as px

from Parsers import *

def visualize_timestamp_gaps(log_file_path):
    """
    Visualize areas in the log where there are significant time gaps between log entries.
    """
    st.header("Log Timestamp Gap Analysis")
    st.markdown("This analysis identifies periods of apparent inactivity in the log, which could indicate when Unity was frozen, processing intensive operations, or otherwise unresponsive.")
    
    # Allow user to set threshold
    col1, col2 = st.columns([2, 1])
    with col1:
        threshold_seconds = st.slider(
            "Minimum time gap to report (seconds)", 
            min_value=1, 
            max_value=300, 
            value=60, 
            step=1,
            help="Show log entries where the time between consecutive logged lines exceeds this threshold"
        )
    
    with col2:
        # Add a button to run the analysis
        analyze_button = st.button("Analyze Timestamp Gaps", key="analyze_gaps")
    
    # Run the analysis when the button is clicked
    if analyze_button:
        with st.spinner("Analyzing timestamp gaps in log file..."):
            # Import the parser function            
            gaps = parse_timestamp_gaps(log_file_path, threshold_seconds)
            
            if not gaps:
                st.info(f"No time gaps greater than {threshold_seconds} seconds were found in the log.")
                return
            
            # Display summary
            st.subheader(f"Found {len(gaps)} gaps exceeding {threshold_seconds} seconds")
            
            # Create an overview chart of gaps
            gap_chart_data = []
            for i, gap in enumerate(gaps):
                gap_chart_data.append({
                    'Gap #': i + 1,
                    'Start Time': gap['prev_timestamp'],
                    'Duration (s)': gap['time_diff_seconds']
                })
            
            gap_df = pd.DataFrame(gap_chart_data)
            
            # Create a bar chart of the gaps (now already sorted by duration)
            fig = px.bar(
                gap_df,
                x='Gap #', 
                y='Duration (s)',
                text='Duration (s)',
                color='Duration (s)',
                height=400,
                title="Duration of Detected Gaps (Sorted by Duration)"
            )
            fig.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
            st.plotly_chart(fig, use_container_width=True, key="timestamp_gaps_chart")
            
            # Create a table of gaps
            display_df = gap_df.copy()
            display_df['Start Time'] = display_df['Start Time'].dt.strftime('%H:%M:%S')
            display_df['Duration'] = display_df['Duration (s)'].apply(lambda x: f"{x:.2f}s")
            
            st.subheader("Gap Details")
            st.dataframe(display_df[['Gap #', 'Start Time', 'Duration']])
            
            # Display individual gaps with expandable details
            st.subheader("Gap Context")
            for i, gap in enumerate(gaps):
                with st.expander(f"Gap #{i+1}: {gap['time_diff_seconds']:.2f}s gap at {gap['prev_timestamp'].strftime('%H:%M:%S')}"):
                    # Display context lines before the gap
                    if gap['context_before']:
                        st.markdown("**Lines before gap:**")
                        context_text = "".join(gap['context_before'])
                        st.code(context_text.strip())
                    
                    
                        st.markdown(f"**Line after gap ({gap['current_timestamp'].strftime('%H:%M:%S.%f')[:-3]}):**")
                        st.code(gap['current_line'].strip())
                    
                    st.markdown(f"**Gap duration:** {gap['time_diff_seconds']:.2f} seconds")