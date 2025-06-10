import pandas as pd

from datetime import datetime
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from Utils import *
def generate_pdf_report(log_file_path, parsing_data):
    """Generate a PDF report with key findings from the log analysis."""
    shader_df = parsing_data.get('shader_df', pd.DataFrame())
    import_df = parsing_data.get('import_df', pd.DataFrame())
    loading_df = parsing_data.get('loading_df', pd.DataFrame())
    build_df = parsing_data.get('build_df', pd.DataFrame())
    refresh_df = parsing_data.get('refresh_df', pd.DataFrame())
    player_build_info = parsing_data.get('player_build_info', [])
    il2cpp_data = parsing_data.get('il2cpp_data', [])
    domain_reloads = parsing_data.get('domain_reloads', [])
    unity_version = parsing_data.get('unity_version', 'Unknown')
    total_build_size = parsing_data.get('total_build_size')
    total_build_unit = parsing_data.get('total_build_unit')
    
    # Create a buffer for the PDF
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
        title="Unity Log Analysis Report"
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading1']
    subheading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create a warning style
    warning_style = ParagraphStyle(
        'WarningStyle',
        parent=normal_style,
        textColor=colors.red
    )
    
    # Create a cell style for tables that supports wrapping
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=normal_style,
        fontSize=9,
        leading=12,  # Line height
        wordWrap='CJK'  # Enable word wrapping
    )
    
    # Helper function to create wrapped text paragraphs for table cells
    def wrap_cell_text(text):
        if not isinstance(text, str):
            text = str(text)
        return Paragraph(text, cell_style)
    
    # Create a list to hold the elements for the PDF
    elements = []
    
    # Add title
    elements.append(Paragraph(f"Unity Log Analysis Report", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add timestamp and Unity version
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generated: {current_time}", normal_style))
    elements.append(Paragraph(f"Unity Version: {unity_version}", normal_style))
    elements.append(Paragraph(f"Log File: {os.path.basename(log_file_path)}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add missing data warnings section
    elements.append(Paragraph("Log Analysis Coverage", heading_style))
    
    # Check which data types are available/missing
    missing_data = []
    if shader_df.empty or 'compilation_seconds' not in shader_df.columns:
        missing_data.append("Shader compilation data could not be found in Editor.log")
    
    if import_df.empty:
        missing_data.append("Asset import data could not be found in Editor.log")
    
    if loading_df.empty:
        missing_data.append("Project loading time data could not be found in Editor.log")
    
    if build_df.empty:
        missing_data.append("Build report data could not be found in Editor.log")
    
    if refresh_df.empty:
        missing_data.append("Asset pipeline refresh data could not be found in Editor.log")
    
    if not player_build_info:
        missing_data.append("Player build performance data could not be found in Editor.log")
    
    if not il2cpp_data:
        missing_data.append("IL2CPP processing data could not be found in Editor.log")
    
    if not domain_reloads:
        missing_data.append("Domain reload data could not be found in Editor.log")
    
    # Add missing data warnings to the PDF
    if missing_data:
        elements.append(Paragraph("The following data types were not found:", normal_style))
        for item in missing_data:
            elements.append(Paragraph(f"• {item}", warning_style))
    else:
        elements.append(Paragraph("✓ All expected data types were found in the log file.", normal_style))
    
    elements.append(Spacer(1, 0.25*inch))
    
    # Add summary section
    elements.append(Paragraph("Performance Summary", heading_style))
    
    # Calculate key metrics for summary
    summary_data = []
    
    # Player Build time
    if player_build_info:
        total_build_time = sum(entry.get('total_duration_sec', 0) for entry in player_build_info)
        summary_data.append(["Total Build Time", format_time(total_build_time)])
    
    # Project Loading time
    if not loading_df.empty and 'total_loading_time' in loading_df.columns:
        total_loading_time = loading_df['total_loading_time'].sum()
        summary_data.append(["Total Loading Time", format_time(total_loading_time)])
    
    # Domain Reloads time
    if domain_reloads:
        total_reload_time = sum((reload.get('reset_time', 0) or 0) for reload in domain_reloads)
        summary_data.append(["Total Domain Reload Time", format_time(total_reload_time)])
    
    # Asset Pipeline Refresh time
    if not refresh_df.empty and 'total_time' in refresh_df.columns:
        total_refresh_time = refresh_df['total_time'].sum()
        summary_data.append(["Total Pipeline Refresh Time", format_time(total_refresh_time)])
    
    # Asset Import time
    if not import_df.empty and 'import_time_seconds' in import_df.columns:
        total_import_time = import_df['import_time_seconds'].sum()
        summary_data.append(["Total Asset Import Time", format_time(total_import_time)])
    
    # Shader Compilation time
    if not shader_df.empty and 'compilation_seconds' in shader_df.columns:
        total_shader_time = shader_df['compilation_seconds'].sum()
        summary_data.append(["Total Shader Compilation Time", format_time(total_shader_time)])
    
    # Add summary table if we have data
    if summary_data:
        # Apply text wrapping to each cell
        wrapped_summary_data = []
        for row in summary_data:
            wrapped_summary_data.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        summary_table = Table(wrapped_summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
    else:
        elements.append(Paragraph("No summary data available", normal_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # PLAYER BUILD SECTION
    elements.append(Paragraph("Player Build Performance", heading_style))
    if player_build_info:
        # Use the first build entry (or allow selection in a more advanced version)
        build_info = player_build_info[0]
        
        build_summary = [
            ["Total Build Time", format_time(build_info['total_duration_sec'])],
            ["Build Phase", build_info['phase']],
            ["Build Steps", str(len(build_info['steps']))]
        ]
        
        # Apply text wrapping
        wrapped_build_summary = []
        for row in build_summary:
            wrapped_build_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        build_table = Table(wrapped_build_summary, colWidths=[2.5*inch, 2.5*inch])
        build_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(build_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add top 5 longest build steps
        elements.append(Paragraph("Top 5 Longest Build Steps", subheading_style))
        steps_data = []
        for step in build_info['steps']:
            duration_ms = step.get('duration', 0)
            description = step.get('description', 'Unknown')
            duration_sec = duration_ms / 1000
            steps_data.append({
                'description': description,
                'duration_sec': duration_sec
            })
        
        if steps_data:
            steps_df = pd.DataFrame(steps_data).sort_values('duration_sec', ascending=False)
            top_steps = steps_df.head(5)
            
            # Create header row
            step_table_data = [["Build Step", "Duration (s)"]]
            
            # Apply wrapping to header
            step_table_data[0] = [wrap_cell_text(cell) for cell in step_table_data[0]]
            
            # Add top steps
            for _, row in top_steps.iterrows():
                step_table_data.append([
                    wrap_cell_text(row['description']),
                    wrap_cell_text(f"{row['duration_sec']:.2f}s")
                ])
            
            step_table = Table(step_table_data, colWidths=[4*inch, 1*inch])
            step_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(step_table)
    else:
        elements.append(Paragraph("No player build performance data was found in the log file.", warning_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # BUILD REPORT SECTION
    elements.append(Paragraph("Build Size Report", heading_style))
    if not build_df.empty:
        # Build report summary
        total_size_readable = f"{total_build_size} {total_build_unit}" if total_build_size and total_build_unit else "N/A"
        
        # Calculate user assets size
        user_assets_size = "N/A"
        user_assets_row = build_df[build_df['category'] == 'Total User Assets']
        if not user_assets_row.empty:
            user_assets_size = f"{user_assets_row.iloc[0]['size_value']} {user_assets_row.iloc[0]['size_unit']}"
        
        build_report_summary = [
            ["Complete Build Size", total_size_readable],
            ["User Assets Size", user_assets_size]
        ]
        
        # Apply text wrapping
        wrapped_report_summary = []
        for row in build_report_summary:
            wrapped_report_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        report_table = Table(wrapped_report_summary, colWidths=[2.5*inch, 2.5*inch])
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(report_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add asset category breakdown
        elements.append(Paragraph("Asset Size by Category", subheading_style))
        
        # Filter out summary rows for the table
        categories_to_exclude = ['Total User Assets', 'Complete build size']
        vis_df = build_df[~build_df['category'].isin(categories_to_exclude)].sort_values('size_in_mb', ascending=False)
        
        if not vis_df.empty:
            # Create header row
            category_table_data = [["Category", "Size", "Percentage"]]
            
            # Apply wrapping to header
            category_table_data[0] = [wrap_cell_text(cell) for cell in category_table_data[0]]
            
            # Add top categories
            for _, row in vis_df.iterrows():
                category_table_data.append([
                    wrap_cell_text(row['category']),
                    wrap_cell_text(f"{row['size_value']} {row['size_unit']}"),
                    wrap_cell_text(f"{row['percentage']}%")
                ])
            
            category_table = Table(category_table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
            category_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(category_table)
    else:
        elements.append(Paragraph("No build size report data was found in the log file.", warning_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # PROJECT LOADING SECTION
    elements.append(Paragraph("Project Loading Performance", heading_style))
    if not loading_df.empty:
        # Use the first loading entry
        entry = loading_df.iloc[0]
        
        loading_summary = [
            ["Total Loading Time", f"{entry['total_loading_time']:.3f}s"],
            ["Project Init Time", f"{entry['project_init_time']:.3f}s"]
        ]
        
        if entry['scene_opening_time'] is not None:
            loading_summary.append(["Scene Opening Time", f"{entry['scene_opening_time']:.3f}s"])
        
        # Apply text wrapping
        wrapped_loading_summary = []
        for row in loading_summary:
            wrapped_loading_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        loading_table = Table(wrapped_loading_summary, colWidths=[2.5*inch, 2.5*inch])
        loading_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(loading_table)
        
        # Create a table for project init breakdown
        elements.append(Paragraph("Project Initialization Breakdown", subheading_style))
        
        # Sub-component names mapping
        subcomponent_names = {
            'template_init': 'Template Init',
            'package_manager_init': 'Package Manager Init',
            'asset_db_init': 'Asset Database Init',
            'global_illumination_init': 'Global Illumination Init',
            'assemblies_load': 'Assemblies Load',
            'unity_extensions_init': 'Unity Extensions Init',
            'asset_db_refresh': 'Asset Database Refresh'
        }
        
        # Create component breakdown table
        component_data = [["Component", "Time (s)"]]
        
        # Apply wrapping to header
        component_data[0] = [wrap_cell_text(cell) for cell in component_data[0]]
        
        for comp, name in subcomponent_names.items():
            if comp in entry and entry[comp] is not None:
                component_data.append([
                    wrap_cell_text(name),
                    wrap_cell_text(f"{entry[comp]:.3f}s")
                ])
        
        component_table = Table(component_data, colWidths=[3*inch, 2*inch])
        component_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(component_table)
    else:
        elements.append(Paragraph("No project loading time data was found in the log file.", warning_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # DOMAIN RELOAD SECTION
    elements.append(Paragraph("Domain Reload Analysis", heading_style))
    if domain_reloads:
        # Calculate summary metrics
        total_time = sum((reload.get('reset_time', 0) or 0) for reload in domain_reloads)
        avg_time = total_time / len(domain_reloads) if domain_reloads else 0
        
        reload_summary = [
            ["Total Domain Reloads", str(len(domain_reloads))],
            ["Total Reload Time", f"{total_time:.2f}s"],
            ["Average Reload Time", f"{avg_time:.2f}s"]
        ]
        
        # Apply text wrapping
        wrapped_reload_summary = []
        for row in reload_summary:
            wrapped_reload_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        reload_table = Table(wrapped_reload_summary, colWidths=[2.5*inch, 2.5*inch])
        reload_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(reload_table)
    else:
        elements.append(Paragraph("No domain reload data was found in the log file.", warning_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # ASSET PIPELINE REFRESH SECTION
    elements.append(Paragraph("Asset Pipeline Refreshes", heading_style))
    if not refresh_df.empty:
        refresh_summary = [
            ["Total Pipeline Refreshes", str(len(refresh_df))],
            ["Total Refresh Time", f"{refresh_df['total_time'].sum():.3f}s"]
        ]
        
        # Apply text wrapping
        wrapped_refresh_summary = []
        for row in refresh_summary:
            wrapped_refresh_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        refresh_table = Table(wrapped_refresh_summary, colWidths=[2.5*inch, 2.5*inch])
        refresh_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(refresh_table)
        
        # Add top 5 slowest refreshes
        elements.append(Paragraph("Top 5 Slowest Asset Pipeline Refreshes", subheading_style))
        
        sorted_df = refresh_df.sort_values('total_time', ascending=False)
        top_refreshes = sorted_df.head(5)
        
        if not top_refreshes.empty:
            # Create header row
            refresh_table_data = [["Initiator", "Time (s)"]]
            
            # Apply wrapping to header
            refresh_table_data[0] = [wrap_cell_text(cell) for cell in refresh_table_data[0]]
            
            # Add top refreshes
            for _, row in top_refreshes.iterrows():
                refresh_table_data.append([
                    wrap_cell_text(row['initiator']),
                    wrap_cell_text(f"{row['total_time']:.2f}s")
                ])
            
            top_refresh_table = Table(refresh_table_data, colWidths=[4*inch, 1*inch])
            top_refresh_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(top_refresh_table)
    else:
        elements.append(Paragraph("No asset pipeline refresh data was found in the log file.", warning_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # ASSET IMPORT SECTION
    elements.append(Paragraph("Asset Import Analytics", heading_style))
    if not import_df.empty:
        import_summary = [
            ["Total Assets Imported", str(len(import_df))],
            ["Total Import Time", f"{import_df['import_time_seconds'].sum():.2f}s"]
            # Removed Average Import Time as requested
        ]
        
        # Apply text wrapping
        wrapped_import_summary = []
        for row in import_summary:
            wrapped_import_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        import_table = Table(wrapped_import_summary, colWidths=[2.5*inch, 2.5*inch])
        import_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(import_table)
        
        # Add top 5 slowest imports
        elements.append(Paragraph("Top 5 Slowest Asset Imports", subheading_style))
        
        sorted_imports = import_df.sort_values('import_time_seconds', ascending=False)
        top_imports = sorted_imports.head(5)
        
        if not top_imports.empty:
            # Create header row
            import_table_data = [["Asset Name", "Type", "Time (s)"]]
            
            # Apply wrapping to header
            import_table_data[0] = [wrap_cell_text(cell) for cell in import_table_data[0]]
            
            # Add top imports
            for _, row in top_imports.iterrows():
                import_table_data.append([
                    wrap_cell_text(row['asset_name']),
                    wrap_cell_text(row['importer_type']),
                    wrap_cell_text(f"{row['import_time_seconds']:.2f}s")
                ])
            
            top_import_table = Table(import_table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
            top_import_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(top_import_table)
    else:
        elements.append(Paragraph("No asset import data was found in the log file.", warning_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # SHADER COMPILATION SECTION
    elements.append(Paragraph("Shader Compilation Analytics", heading_style))
    if not shader_df.empty and 'compilation_seconds' in shader_df.columns:
        # Overall shader statistics
        shader_summary = [
            ["Total Shaders", str(len(shader_df))],
            ["Total Compilation Time", f"{shader_df['compilation_seconds'].sum():.2f}s"]
            # Removed Average Compilation Time as requested
        ]
        
        if 'compiled_variants' in shader_df.columns:
            shader_summary.append(["Total Variants Compiled", str(int(shader_df['compiled_variants'].sum()))])
        
        # Apply text wrapping
        wrapped_shader_summary = []
        for row in shader_summary:
            wrapped_shader_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        shader_table = Table(wrapped_shader_summary, colWidths=[2.5*inch, 2.5*inch])
        shader_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(shader_table)
        
        # Add top 5 slowest shaders
        elements.append(Paragraph("Top 5 Slowest Shaders", subheading_style))
        
        sorted_shaders = shader_df.sort_values('compilation_seconds', ascending=False)
        top_shaders = sorted_shaders.head(5)
        
        if not top_shaders.empty:
            # Create header row
            shader_table_data = [["Shader Name", "Pass", "Time (s)"]]
            
            # Apply wrapping to header
            shader_table_data[0] = [wrap_cell_text(cell) for cell in shader_table_data[0]]
            
            # Add top shaders
            for _, row in top_shaders.iterrows():
                pass_name = row.get('pass_name', 'N/A') if 'pass_name' in row else 'N/A'
                shader_table_data.append([
                    wrap_cell_text(row['shader_name']),
                    wrap_cell_text(pass_name),
                    wrap_cell_text(f"{row['compilation_seconds']:.2f}s")
                ])
            
            top_shader_table = Table(shader_table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
            top_shader_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(top_shader_table)
    else:
        elements.append(Paragraph("No shader compilation data was found in the log file.", warning_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # IL2CPP PROCESSING SECTION
    elements.append(Paragraph("IL2CPP Processing Analysis", heading_style))
    if il2cpp_data:
        # Calculate summary metrics
        total_assemblies = len(il2cpp_data)
        total_time_ms = sum(entry['total_time_ms'] for entry in il2cpp_data)
        total_time_sec = total_time_ms / 1000
        
        il2cpp_summary = [
            ["Total Assemblies Processed", str(total_assemblies)],
            ["Total Processing Time", f"{total_time_sec:.2f}s"]
        ]
        
        # Apply text wrapping
        wrapped_il2cpp_summary = []
        for row in il2cpp_summary:
            wrapped_il2cpp_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        il2cpp_table = Table(wrapped_il2cpp_summary, colWidths=[2.5*inch, 2.5*inch])
        il2cpp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(il2cpp_table)
        
        # Add top 5 assemblies by processing time
        elements.append(Paragraph("Top 5 Assemblies by IL2CPP Processing Time", subheading_style))
        
        # Sort assemblies by processing time
        sorted_data = sorted(il2cpp_data, key=lambda x: x['total_time_ms'], reverse=True)[:5]
        
        if sorted_data:
            # Create header row
            assembly_table_data = [["Assembly", "Time (ms)"]]
            
            # Apply wrapping to header
            assembly_table_data[0] = [wrap_cell_text(cell) for cell in assembly_table_data[0]]
            
            # Add top assemblies
            for entry in sorted_data:
                assembly_table_data.append([
                    wrap_cell_text(entry['assembly']),
                    wrap_cell_text(f"{entry['total_time_ms']}ms")
                ])
            
            assembly_table = Table(assembly_table_data, colWidths=[4*inch, 1*inch])
            assembly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(assembly_table)
    else:
        elements.append(Paragraph("No IL2CPP processing data was found in the log file.", warning_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF from the buffer
    buffer.seek(0)
    return buffer
