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
    performance_df = parsing_data.get('performance_df', pd.DataFrame())

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
    
    # Handle the log file path safely
    log_file_name = "Unity Editor Log"
    if isinstance(log_file_path, str):
        try:
            log_file_name = os.path.basename(log_file_path)
        except (TypeError, AttributeError):
            pass
    elements.append(Paragraph(f"Log File: {log_file_name}", normal_style))
    
    elements.append(Spacer(1, 0.25*inch))
    
    # [... rest of the code up to IL2CPP section remains unchanged ...]
    
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
    
    # [... All other sections remain unchanged ...]
    
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
    
    elements.append(Spacer(1, 0.5*inch))
    
    # PERFORMANCE REPORT SECTION
    if performance_df is not None and not performance_df.empty:
        elements.append(Paragraph("Performance Report Analysis", heading_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Performance summary metrics
        total_operations = len(performance_df)
        total_samples = performance_df['samples'].sum()
        max_percentage = performance_df['percentage'].max()
        
        perf_summary_data = [
            ["Total Operations", str(total_operations)],
            ["Total Samples", str(total_samples)],
            ["Max Time Percentage", f"{max_percentage:.2f}%"]
        ]
        
        # Apply text wrapping
        wrapped_perf_summary = []
        for row in perf_summary_data:
            wrapped_perf_summary.append([
                wrap_cell_text(row[0]), 
                wrap_cell_text(row[1])
            ])
            
        perf_summary_table = Table(wrapped_perf_summary, colWidths=[2.5*inch, 2.5*inch])
        perf_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(perf_summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Top slowest operations
        elements.append(Paragraph("Top 15 Slowest Operations (by Total Time)", subheading_style))
        
        # Sort and get top operations
        sorted_df = performance_df.sort_values('total_us', ascending=False)
        top_n = min(15, len(sorted_df))
        top_operations = sorted_df.head(top_n)
        
        # Convert time to seconds for display
        top_operations['total_s'] = top_operations['total_us'] / 1000000
        
        # Create table for top operations
        if not top_operations.empty:
            # Create header row
            operations_table_data = [["Operation", "Samples", "Avg (s)", "Peak (s)", "Total (s)", "%"]]
            
            # Apply wrapping to header
            operations_table_data[0] = [wrap_cell_text(cell) for cell in operations_table_data[0]]
            
            # Add top operations
            for _, row in top_operations.iterrows():
                # Format values for display
                operation = (row['operation'][:45] + '...') if len(row['operation']) > 48 else row['operation']
                avg_s = row['avg_us'] / 1000000
                peak_s = row['peak_us'] / 1000000
                total_s = row['total_s']
                
                operations_table_data.append([
                    wrap_cell_text(operation),
                    wrap_cell_text(str(row['samples'])),
                    wrap_cell_text(f"{avg_s:.6f}"),
                    wrap_cell_text(f"{peak_s:.6f}"),
                    wrap_cell_text(f"{total_s:.6f}"),
                    wrap_cell_text(f"{row['percentage']:.2f}%")
                ])
            
            operations_table = Table(operations_table_data, colWidths=[2*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.5*inch])
            operations_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(operations_table)
        
        elements.append(Spacer(1, 0.25*inch))
        
        # Category breakdown (if available)
        if 'category' in performance_df.columns:
            elements.append(Paragraph("Performance by Category", subheading_style))
            
            category_df = performance_df.groupby('category').agg(
                total_time_us=('total_us', 'sum'),
                operation_count=('operation', 'count'),
                sample_count=('samples', 'sum')
            ).reset_index().sort_values('total_time_us', ascending=False)
            
            # Convert time to seconds
            category_df['total_time_s'] = category_df['total_time_us'] / 1000000
            
            # Limit to top 10 categories
            top_categories = category_df.head(10)
            
            if not top_categories.empty:
                # Create header row
                categories_table_data = [["Category", "Operations", "Samples", "Total Time (s)"]]
                
                # Apply wrapping to header
                categories_table_data[0] = [wrap_cell_text(cell) for cell in categories_table_data[0]]
                
                # Add top categories
                for _, row in top_categories.iterrows():
                    # Truncate category name if too long
                    category = (row['category'][:42] + '...') if len(row['category']) > 45 else row['category']
                    
                    categories_table_data.append([
                        wrap_cell_text(category),
                        wrap_cell_text(str(row['operation_count'])),
                        wrap_cell_text(str(row['sample_count'])),
                        wrap_cell_text(f"{row['total_time_s']:.6f}")
                    ])
                
                categories_table = Table(categories_table_data, colWidths=[3*inch, 1*inch, 1*inch, 1.5*inch])
                categories_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(categories_table)
        
        elements.append(Spacer(1, 0.25*inch))
        
        # High peak factor operations
        elements.append(Paragraph("Top 10 Operations with Highest Peak Factor", subheading_style))
        
        # Get operations with highest peak factor
        factor_sorted = performance_df.sort_values('peak_factor', ascending=False).head(10)
        
        if not factor_sorted.empty:
            # Create header row
            factor_table_data = [["Operation", "Samples", "Peak Factor", "Avg (s)", "Peak (s)"]]
            
            # Apply wrapping to header
            factor_table_data[0] = [wrap_cell_text(cell) for cell in factor_table_data[0]]
            
            # Add rows
            for _, row in factor_sorted.iterrows():
                # Truncate operation name if too long
                operation = (row['operation'][:42] + '...') if len(row['operation']) > 45 else row['operation']
                
                # Convert values to seconds
                avg_s = row['avg_us'] / 1000000
                peak_s = row['peak_us'] / 1000000
                
                factor_table_data.append([
                    wrap_cell_text(operation),
                    wrap_cell_text(str(row['samples'])),
                    wrap_cell_text(f"{row['peak_factor']:.2f}x"),
                    wrap_cell_text(f"{avg_s:.6f}"),
                    wrap_cell_text(f"{peak_s:.6f}")
                ])
            
            factor_table = Table(factor_table_data, colWidths=[3*inch, 0.8*inch, 1*inch, 1*inch, 1*inch])
            factor_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(factor_table)
        
        # Add note about peak factor
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=normal_style,
            fontSize=9,
            fontName='Helvetica-Oblique'
        )
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph('Note: A high peak factor indicates inconsistent performance across runs.', note_style))

    # Build the PDF
    doc.build(elements)
    
    # Get the PDF from the buffer
    buffer.seek(0)
    return buffer
