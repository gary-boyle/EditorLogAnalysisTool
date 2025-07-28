# EditorLogVisTool

This tool allows you to load Editor.log files from Unity Engine builds and view a variety of different statistics to help with Build analysis/debugging.

To run the tool locally:
1. clone the repository
❯ git clone git@github.com:gary-boyle/EditorLogAnalysisTool.git

2. enter the project root
❯ cd EditorLogAnalysisTool

3. make sure python is installed and up-to-date
❯ brew install python3

4. create a virtual environment in the current folder to keep the librairies local and not system wide
❯ python3 -m venv .

5. activate the virtual environment (source is required because execution flag isn't set)
❯ source bin/activate

6. install the required libraries in the virtual environment
❯ pip3 install streamlit reportlab plotly

7. run the project, this opens the web page in your browser
❯ python3 -m streamlit run main.py
