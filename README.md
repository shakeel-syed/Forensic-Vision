# Forensic Vision

This project implements an automated forensic image quality inspection and spatial mapping system using **LangGraph** and **Google Gemini AI**. It is designed to analyze images, score their quality, and identify specific forensic points of interest (Scars, Marks, Tattoos, or damage) through an iterative process.

## Project Structure

The project has been organized into logical directories:

- **`assets/`**: Contains sample images for testing (`sample.jpg`, `blurry_sample.jpg`).
- **`docs/`**: Project documentation and generated reports (e.g., `Inspection_report.md`, `Market_Analysis.md`).
- **`src/`**: Core application logic.
  - `ForensicAPI.py`: FastAPI service providing REST endpoints for forensic analysis.
  - `ImageQuality.py`: LangGraph workflow for iterative image inspection.
  - `Dashboard.py`: Streamlit-based interactive dashboard for visualization.
  - `SpatialPrompting.py`: Utility for spatial reasoning prompts.
  - `main.py`: Entry point for local testing.
- **`dotnet_client/`**: A C# (.NET) client demonstration for interacting with the Forensic API.
- **`ForensicDashboard/`**: A full .NET web application for managing forensic reports.
- **`RagTutor/`**: A RAG (Retrieval-Augmented Generation) subsystem for forensic knowledge.

## Key Components

### 1. State Management (`InspectorState`)
The workflow maintains a state throughout its execution, tracking:
- `image_path`: Path to the image being analyzed.
- `analysis`: The raw text feedback from the LLM.
- `quality_score`: A numerical score (1-10) assigned to the image.
- `detections`: List of forensic marks identified with bounding boxes.
- `decision`: The outcome of the judgment node (`Approve` or `Retry`).
- `iterations`: The current count of analysis attempts.

### 2. Workflow Nodes
- **Analyze Image**: Encodes the image and sends it to the Gemini model with a spatial prompt to map forensic points.
- **Judge Quality**: Evaluates the analysis to decide whether the image meets professional standards.

### 3. Conditional Routing
- **Max Iterations**: Stops after 3 attempts even if not approved.
- **Approval Logic**: Terminates successfully if the judge issues an "Approve" decision.

## Requirements
- `langchain-google-genai`
- `langgraph`
- `fastapi`
- `streamlit`
- `uvicorn`
- `Pillow`
- Valid `GOOGLE_API_KEY` (configured in `.env`)

## Usage

### Local Script
To run the analysis on `assets/sample.jpg`:
```bash
python src/ImageQuality.py
```

### FastAPI Service
To start the forensic API:
```bash
python src/ForensicAPI.py
```
Visit `http://localhost:8000/docs` for the interactive Swagger documentation.

### Streamlit Dashboard
To launch the visual dashboard:
```bash
streamlit run src/Dashboard.py
```

## Deployment
A `Dockerfile` is provided in the root directory to containerize the API service.
```bash
docker-compose up --build
```

## Final Result
The system outputs a detailed forensic report, including bounding boxes for detected marks and a final quality score.
