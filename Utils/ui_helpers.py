import streamlit as st

def show_big_spinner(message="Processing..."):
    """Display a large, centered spinner with custom message that can be updated."""
    # Create a container for the spinner
    spinner_container = st.empty()
    
    # Function to update the spinner message
    def update_spinner(new_message):
        spinner_html = f"""
        <style>
        .big-spinner-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: rgba(255, 255, 255, 0.8);
            z-index: 1000;
        }}
        .big-spinner-text {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #0066cc;
            text-align: center;
        }}
        .big-spinner-status {{
            font-size: 16px;
            margin-bottom: 20px;
            color: #666;
            text-align: center;
        }}
        .big-spinner {{
            border: 12px solid #f3f3f3;
            border-top: 12px solid #0066cc;
            border-radius: 50%;
            width: 100px;
            height: 100px;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        <div class="big-spinner-container">
            <div class="big-spinner-text">Parsing Unity Log File</div>
            <div class="big-spinner-status">{new_message}</div>
            <div class="big-spinner"></div>
        </div>
        """
        spinner_container.markdown(spinner_html, unsafe_allow_html=True)
    
    # Initial display
    update_spinner(message)
    
    # Return the updater function and the container
    return update_spinner, spinner_container

def show_progress_checklist(parsing_options):
    """Display a spinner with a checklist of processing steps."""
    # Create a container for the spinner and checklist
    progress_container = st.empty()
    
    # Create a list of all processing steps based on enabled options
    steps = []
    if parsing_options['shader']:
        steps.append({"name": "Shader Compilation Data", "status": "⏳", "complete": False})
    if parsing_options['imports']:
        steps.append({"name": "Asset Import Data", "status": "⏳", "complete": False})
    if parsing_options['loading']:
        steps.append({"name": "Project Loading Times", "status": "⏳", "complete": False})
    if parsing_options['build_report']:
        steps.append({"name": "Build Report Data", "status": "⏳", "complete": False})
    if parsing_options['pipeline']:
        steps.append({"name": "Asset Pipeline Refresh Data", "status": "⏳", "complete": False})
    if parsing_options['player_build']:
        steps.append({"name": "Player Build Information", "status": "⏳", "complete": False})
    if parsing_options['il2cpp']:
        steps.append({"name": "IL2CPP Processing Data", "status": "⏳", "complete": False})
    if parsing_options['tundra']:
        steps.append({"name": "Tundra Build Information", "status": "⏳", "complete": False})
    if parsing_options['domain_reload']:
        steps.append({"name": "Domain Reload Data", "status": "⏳", "complete": False})
    
    # Function to update the checklist display
    def update_progress(current_step=None, message="Processing..."):
        # Mark the current step as complete if specified
        if current_step is not None:
            for step in steps:
                if step["name"] == current_step and not step["complete"]:
                    step["status"] = "✅"
                    step["complete"] = True
                    break
        
        # Create HTML for the spinner and checklist
        checklist_html = ""
        for step in steps:
            checklist_html += f"<div style='margin-bottom: 5px;'>{step['status']} {step['name']}</div>"
        
        progress_html = f"""
        <style>
        .progress-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: rgba(255, 255, 255, 0.9);
            z-index: 1000;
        }}
        .progress-header {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #0066cc;
        }}
        .progress-message {{
            font-size: 16px;
            margin-bottom: 20px;
            color: #666;
        }}
        .progress-spinner {{
            border: 12px solid #f3f3f3;
            border-top: 12px solid #0066cc;
            border-radius: 50%;
            width: 80px;
            height: 80px;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }}
        .progress-checklist {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            width: 300px;
            max-height: 300px;
            overflow-y: auto;
            font-size: 14px;
            text-align: left;
            margin-bottom: 20px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        <div class="progress-container">
            <div class="progress-header">Parsing Unity Log File</div>
            <div class="progress-message">{message}</div>
            <div class="progress-spinner"></div>
            <div class="progress-checklist">
                {checklist_html}
            </div>
        </div>
        """
        progress_container.markdown(progress_html, unsafe_allow_html=True)
    
    # Initial display
    update_progress(message="Initializing...")
    
    return update_progress, progress_container
