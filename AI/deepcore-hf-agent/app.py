"""Hugging Face Gradio UI: deploy only as a private, authenticated Space."""
import asyncio
import json
import os
import gradio as gr
from agent import AgentError, cmc_preview, health, summarize

def run_preview(want_summary):
    try:
        data = asyncio.run(cmc_preview())
        note = summarize(data) if want_summary else "Summary not requested"
        return data, note
    except AgentError as exc:
        return {"status":"blocked","reason":str(exc)}, "No report generated"
    except Exception:
        return {"status":"blocked","reason":"External integration failure"}, "No report generated"

with gr.Blocks(title="DeepCore | CMC Advisory Agent") as demo:
    gr.Markdown("# DeepCore CMC Advisory Agent\nRead-only market correlation previews. No custody or trading authority.")
    gr.Code(value=json.dumps(health(),indent=2), label="Configuration (presence only)",
            language="json", interactive=False)
    with gr.Row():
        want_summary = gr.Checkbox(label="Optional OpenAI advisory summary",value=False)
        run = gr.Button("Find and preview BTC cross-asset correlation")
    result = gr.JSON(label="CMC Skill Hub result")
    summary = gr.Textbox(label="Optional model summary", lines=8)
    run.click(run_preview, inputs=[want_summary], outputs=[result,summary],concurrency_limit=1)

if __name__ == "__main__":
    password = os.getenv("DEEPCORE_OPERATOR_PASSWORD")
    if not password:
        raise RuntimeError("Set DEEPCORE_OPERATOR_PASSWORD in Hugging Face Space Secrets")
    demo.launch(server_name="0.0.0.0",server_port=7860,show_error=False,
                auth=(os.getenv("DEEPCORE_OPERATOR_USER","operator"),password))
