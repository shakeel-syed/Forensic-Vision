import os
import base64
import json
from typing import TypedDict, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Load API Key from .env
load_dotenv()

# Define Pydantic models for structured output
class Detection(BaseModel):
    label: str = Field(description="The type of mark: tattoo, scar, etc.")
    box_2d: List[int] = Field(description="Bounding box [ymin, xmin, ymax, xmax]")
    description: str = Field(description="Detailed forensic description")

class ForensicReport(BaseModel):
    detections: List[Detection]
    overall_clarity_score: int = Field(ge=1, le=10)

# 1. Define the State
class InspectorState(TypedDict):
    image_path: str
    analysis: str # Will hold the json string from gemini
    quality_score: int
    decision: str   # Approve or Retry
    iterations: int

# Initialize the 2026 Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
structured_llm = llm.with_structured_output(ForensicReport)

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
    
# ---- NODE 1: - Forensic Analysis ---

def analyze_image(state: InspectorState):
    current_count = state.get("iterations", 0)
    print(f"\n Forensic Detection (Attempt) {current_count + 1}")

    img_base64 = encode_image(state["image_path"])

    # Spatial Prompting: Asking for [ymin, xmin, ymax, xmax]
    prompt = "Perform a forensic SMT (Scars, Marks, Tattoos) analysis. Use normalized coordinates (0-1000) for the bounding boxes."
    
    msg = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_base64}"}
    ])

    # Using structured output for automatic parsing into Pydantic model
    res = structured_llm.invoke([msg])
    
    return {
        "analysis": res.model_dump_json(),
        "iterations": current_count + 1
    }

# --- NODE 2: Quality Judge ---
def judge_quality(state: InspectorState):
    print("--- Step 2: Judging Quality ---")

    try:
        # Parse the JSON string Gemini gave us
        data = json.loads(state["analysis"])
        score = data.get("overall_clarity_score", 0)

        # Decision logic: if score is 7 or higher, we approve
        if score >= 7:
            return {"decision": "Approve", "quality_score": score}
        else:
            return {"decision": "Retry", "quality_score": score}

    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return {"decision": "Retry", "quality_score": 0} 
    
# --- ROUTER: The Traffic Controller ---
def should_continue(state: InspectorState):
    # Rule 1: Safety Net
    if state.get("iterations", 0) >= 3:
        print("!!! MAX ATTEMPTS REACHED: Stopping to save costs !!!")
        return END
    
    # Rule 2: Logic Check
    if state.get("decision") == "Approve":
        print("Analysis validated")
        return END
    
    print("--- ANALYSIS REJECTED: Looping for better detail ---")
    return "analyze"

# --- 3. Build the Graph Architecture ---
workflow = StateGraph(InspectorState)

workflow.add_node("analyze", analyze_image)
workflow.add_node("judge", judge_quality)

workflow.set_entry_point("analyze")

# Define the roads
workflow.add_edge("analyze", "judge")
workflow.add_conditional_edges("judge", should_continue)

# Compile the App
app = workflow.compile()

# -- Run the Agenct ---
# Ensure "sample.jpg" is in your c:\LearnAI
initial_input = {
    "image_path": "assets/sample.jpg", 
    "iterations": 0,
    "analysis": "",
    "decision": "",
    "quality_score": 0
}

final_result = app.invoke(initial_input)

# Display final forensic output
print("\n" + "="*30)
print("FINAL FORENSIC REPORT")
print("="*30)
print(final_result['analysis'])
print(f"Final Decision: {final_result['decision']}")
print(f"Total Passes: {final_result['iterations']}")