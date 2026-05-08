import os
import base64
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load API Key from .env
load_dotenv()

console = Console()

# --- 1. Define Structured Output Models ---

class Detection(BaseModel):
    label: str = Field(description="The type of mark: tattoo, scar, blemish, damage, etc.")
    box_2d: List[int] = Field(description="Bounding box [ymin, xmin, ymax, xmax] using normalized coordinates (0-1000)")
    description: str = Field(description="Brief forensic description of this specific detection")

class ForensicReport(BaseModel):
    detections: List[Detection] = Field(description="List of all forensic marks found")
    overall_clarity_score: int = Field(description="Quality score from 1-10", ge=1, le=10)
    detailed_description: str = Field(description="Forensic analysis of the image")

class JudgeResponse(BaseModel):
    decision: str = Field(description="Must be 'Approve' or 'Retry'")
    reasoning: str = Field(description="Brief explanation for the decision")

# --- 2. Define the State ---

class AttemptRecord(TypedDict):
    iteration: int
    analysis: str
    score: int
    decision: str
    reasoning: str
    detections: List[dict] 

class InspectorState(TypedDict):
    image_path: str
    analysis: str
    quality_score: int
    decision: str
    iterations: int
    history: List[AttemptRecord]
    detections: List[dict]

# Initialize LLMs - Optimized for speed and spatial reasoning
llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
structured_analyzer = llm.with_structured_output(ForensicReport)
structured_judge = llm.with_structured_output(JudgeResponse)

def encode_image(path):
    # Restoring to direct file read (no resizing) as it was yesterday
    console.print(f"   [dim]... Reading image file: {path}[/dim]")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# --- 3. Define the Nodes ---

def analyze_image(state: InspectorState):
    current_count = state.get("iterations", 0)
    console.print(f"\n[bold blue]🔍 Step 1: Spatial Vision Analysis[/bold blue] (Attempt {current_count + 1})")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="[cyan]Gemini is performing forensic mapping...[/cyan]", total=None)
        
        img_base64 = encode_image(state['image_path'])
        
        prompt = (
            "Perform a forensic SMT (Scars, Marks, Tattoos) analysis on this image. "
            "Use normalized coordinates (0-1000) for the bounding boxes [ymin, xmin, ymax, xmax]. "
            "Also provide an overall clarity score (1-10) and a detailed description of the findings."
        )
        
        msg = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_base64}"}
        ])
        
        console.print(f"   [dim]... Sending request to {llm.model}[/dim]")
        res: ForensicReport = structured_analyzer.invoke([msg])
    
    console.print(Panel(res.detailed_description, title="[bold green]Analysis Result[/bold green]", border_style="green"))
    if res.detections:
        console.print(f"📍 [bold cyan]Detected {len(res.detections)} forensic points.[/bold cyan]")
    
    return {
        "analysis": res.detailed_description, 
        "quality_score": res.overall_clarity_score,
        "detections": [d.model_dump() for d in res.detections],
        "iterations": current_count + 1
    }

def judge_quality(state: InspectorState):
    console.print("[bold magenta]⚖️  Step 2: Judging Quality[/bold magenta]")
    
    try:
        prompt = (
            f"Evaluate the image quality based on this analysis: {state['analysis']}. "
            f"Quality Score: {state['quality_score']}/10. "
            "Determine if the image is clear enough for forensic work. "
            "It should only be 'Approve' if the quality score is 7 or higher and no significant blur is mentioned. "
            "Decision: 'Approve' or 'Retry'."
        )
        
        res: JudgeResponse = structured_judge.invoke(prompt)
        
        color = "green" if res.decision == "Approve" else "yellow"
        console.print(f"Decision: [bold {color}]{res.decision}[/bold {color}] (Final Score: {state['quality_score']}/10)")
        console.print(f"Reasoning: {res.reasoning}")
        
        new_history = state.get("history", [])
        new_history.append({
            "iteration": state["iterations"],
            "analysis": state["analysis"],
            "score": state["quality_score"],
            "decision": res.decision,
            "reasoning": res.reasoning,
            "detections": state.get("detections", [])
        })
        
        return {
            "decision": res.decision, 
            "history": new_history
        }
    except Exception as e:
        console.print(f"[bold red]Validation error in judge_quality:[/bold red] {e}")
        return {"decision": "Retry"}

# --- 4. Define the Router ---

def should_continue(state: InspectorState):
    # Restoring the 3-iteration limit as it was yesterday
    if state.get("iterations", 0) >= 3:
        console.print("\n[bold red]🛑 MAX ITERATIONS REACHED[/bold red]")
        return END
    
    if state.get("decision") == "Approve":
        console.print("\n[bold green]✅ QUALITY STANDARDS MET[/bold green]")
        return END
    
    console.print("\n[bold yellow]🔄 RETRYING ANALYSIS...[/bold yellow]")
    return "analyze"

# --- 5. Build the Graph ---

workflow = StateGraph(InspectorState)
workflow.add_node("analyze", analyze_image)
workflow.add_node("judge", judge_quality)
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "judge")
workflow.add_conditional_edges("judge", should_continue)
app = workflow.compile()

if __name__ == "__main__":
    console.clear()
    console.print(Panel.fit("🚀 [bold white]Forensic Evidence Mapping System[/bold white] 🚀", style="bold cyan"))

    final_result = app.invoke({
        "image_path": "assets/sample.jpg", 
        "iterations": 0,
        "decision": "",
        "analysis": "",
        "quality_score": 0,
        "detections": [],
        "history": []
    })

    summary_table = Table(show_header=True, header_style="bold magenta", box=None)
    summary_table.add_column("Target Image", style="cyan")
    summary_table.add_column("Final Decision", justify="center")
    summary_table.add_column("Detections", justify="center")
    summary_table.add_column("Final Score", justify="center")

    color = "green" if final_result['decision'] == "Approve" else "red"
    summary_table.add_row(
        final_result['image_path'],
        f"[bold {color}]{final_result['decision']}[/bold {color}]",
        str(len(final_result.get('detections', []))),
        f"[bold]{final_result['quality_score']}/10[/bold]"
    )

    history_table = Table(title="[bold cyan]Iteration History[/bold cyan]", show_header=True, header_style="bold cyan", row_styles=["", "dim"])
    history_table.add_column("Iter", justify="right", style="bold")
    history_table.add_column("Score", justify="center")
    history_table.add_column("Decision")
    history_table.add_column("Reasoning", overflow="fold")

    for record in final_result.get("history", []):
        h_color = "green" if record['decision'] == "Approve" else "yellow"
        status_emoji = "✅" if record['decision'] == "Approve" else "❌"
        history_table.add_row(
            str(record['iteration']),
            f"{record['score']}/10",
            f"[{h_color}]{status_emoji} {record['decision']}[/{h_color}]",
            record['reasoning']
        )

    console.print("\n")
    console.print(Panel(summary_table, title="[bold white]Final Inspection Summary[/bold white]", border_style="magenta", expand=False))
    console.print(history_table)
