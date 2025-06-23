# EditorLogVisTool

The tool is currently hosted on https://editorloganalysistool.streamlit.app/

To run locally:
Install a couple of libraries : pip install streamlit reportlab

Run : `python -m streamlit run .\main.py`

## Running with Docker

You can also run the application inside a Docker container.

1.  Build the Docker image:
    `docker build -t editor-log-analyzer .`

2.  Run the Docker container:
    `docker run -p 8501:8501 editor-log-analyzer`

The application will be available at http://localhost:8501.
