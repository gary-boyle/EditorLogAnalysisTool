# Unity Editor Log Analysis Tool

A tool for analyzing and visualizing Unity Editor log files, with support for PDF report generation and interactive web-based exploration.

## Features

- **Parse Unity Editor.log files** for build, asset, domain reload, IL2CPP, Tundra, and performance data.
- **Interactive web interface** powered by Streamlit.
- **PDF report generation** for offline sharing.
- **Customizable analysis**: Select which data types to parse for faster results.
- **Timestamp gap analysis**: Detect frozen or unresponsive periods in the Editor.
- **Helpful visualizations** and summaries.

<img width="2476" height="454" alt="image" src="https://github.com/user-attachments/assets/48f51b74-734c-490e-b2aa-edcc2ffc9ca2" />
<img width="2348" height="592" alt="image" src="https://github.com/user-attachments/assets/e7b8b2bb-c362-4dfa-a653-742eb7b3b648" />
<img width="2354" height="987" alt="image" src="https://github.com/user-attachments/assets/454ef644-ff3f-48c2-b2d8-8b3898fb35d5" />


## Getting Started

### Prerequisites

- [Python 3.8+](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [reportlab](https://www.reportlab.com/)
- [Plotly](https://plotly.com/)

To run the tool locally:
1. Clone the repository
`git clone git@github.com:gary-boyle/EditorLogAnalysisTool.git`

2. Enter the project root
`cd EditorLogAnalysisTool`

3. Make sure Python is installed and up-to-date
`brew install python3`

4. (Optional) Create a virtual environment in the current folder to keep the librairies local and not system wide
`python3 -m venv .`

5. (Optional) Activate the virtual environment
`source bin/activate`

6. Install the required libraries in the virtual environment
`pip3 install streamlit reportlab plotly`

7. Run the project, this opens the web page in your browser
`python3 -m streamlit run main.py`

### Running the Tool

#### Web Interface

Launch the Streamlit app:

```sh
python -m streamlit run main.py
```

Open the provided local URL in your browser.

#### Command-Line PDF Report

Generate a PDF report from a log file:

```sh
python main.py --log_file path/to/Editor.log --output path/to/report.pdf
```

If `--output` is omitted, the PDF will be saved next to the log file.

## Usage

1. **Select Data Types**: Use checkboxes to choose which log data to analyze.
2. **Upload Log File**: Drag and drop or select your Unity Editor.log file.
3. **View Results**: Visualizations and summaries will appear automatically.
4. **Tips**:
   - Disable unnecessary data types for large logs to speed up analysis.
   - Domain Reload parsing is intensive for large logs.
   - Enable timestamps in Unity for detailed analysis.

## Project Structure

```
.
├── main.py                  # Entry point for both CLI and Streamlit app
├── Parsers/                 # Log parsing modules
├── Reporting/               # PDF and reporting utilities
├── Visualizers/             # Visualization components
├── Utils/                   # Utility functions
├── Examples/                # Example log files
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
```

## How the Parsers Work

The core of this tool is a set of specialized parsers that extract structured information from Unity Editor log files. Each parser is designed to identify and process specific types of log entries (such as build steps, asset imports, domain reloads, IL2CPP compilation, and Tundra build data).

### Regular Expression (Regex) Based Parsing

- **Pattern Matching:**  
  Each parser uses Python’s `re` module to define regular expressions that match the unique patterns of relevant log lines. For example, a build step might be matched with a pattern like `r"\[BuildStep\] (.+?): (\d+\.\d+) seconds"`.

- **Line-by-Line Analysis:**  
  The log file is read line by line. Each line is tested against the parser’s regex patterns. If a match is found, the parser extracts the relevant data (such as timestamps, step names, durations, or error messages).

- **Data Extraction:**  
  Captured groups from the regex are used to populate structured Python objects or dictionaries. This allows for easy aggregation, filtering, and visualization later in the workflow.

- **Multiple Parsers:**  
  Different log sections (e.g., asset import, domain reload, IL2CPP) have their own parser classes or functions, each with tailored regex patterns to handle the specific log format and data fields.

- **Performance Considerations:**  
  For large log files, only the enabled parsers are run, and some (like domain reload analysis) may be slower due to more complex or numerous regex matches.

#### Example

```python
import re

# Example: Parse build step durations
pattern = re.compile(r"\[BuildStep\] (?P<step>.+?): (?P<duration>\d+\.\d+) seconds")
for line in log_file:
    match = pattern.search(line)
    if match:
        step = match.group("step")
        duration = float(match.group("duration"))
        # Store or process the extracted data
```

This approach allows the tool to robustly extract actionable insights from the often-unstructured Unity Editor logs.

## Example Logs

Sample logs are available in the [Examples/](Examples/) directory for testing and demonstration.

## Contributing

Pull requests and issues are welcome!

## License

[MIT](LICENSE) (add
