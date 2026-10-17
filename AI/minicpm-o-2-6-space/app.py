"""Gradio Space demo for OpenBMB MiniCPM-o 2.6, vision only."""
import gradio as gr
from inference import MODEL_ID, MODEL_REVISION, analyze, compare, extract_text

with gr.Blocks(title="MiniCPM-o 2.6 | Vision Studio",
               theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate")) as demo:
    gr.Markdown("# 👁️ MiniCPM-o 2.6 Vision Studio\nOpenBMB's multimodal model, configured for GPU-based vision inference.")
    with gr.Tabs():
        with gr.Tab("Image Q&A"):
            gr.Markdown("Ask questions about photos, documents, and screenshots.")
            with gr.Row():
                image = gr.Image(type="pil", label="Image", sources=["upload", "webcam"])
                with gr.Column():
                    question = gr.Textbox(label="Question", value="Describe this image in detail.")
                    analyze_button = gr.Button("Analyze image", variant="primary")
                    answer = gr.Textbox(label="Model response", lines=14, show_copy_button=True)
            analyze_button.click(analyze, inputs=[image, question], outputs=answer, api_name="analyze_image")
        with gr.Tab("Compare images"):
            with gr.Row():
                first = gr.Image(type="pil", label="Image A")
                second = gr.Image(type="pil", label="Image B")
            compare_prompt = gr.Textbox(
                label="Comparison question",
                value="Describe the important differences between the first and second images.")
            compare_button = gr.Button("Compare images", variant="primary")
            comparison = gr.Textbox(label="Comparison result", lines=14, show_copy_button=True)
            compare_button.click(compare, inputs=[first, second, compare_prompt],
                                 outputs=comparison, api_name="compare_images")
        with gr.Tab("OCR / Read text"):
            document = gr.Image(type="pil", label="Document or screenshot")
            ocr_prompt = gr.Textbox(
                label="Instructions",
                value="Transcribe all clearly visible text and preserve line breaks.")
            ocr_button = gr.Button("Read text", variant="primary")
            extracted = gr.Textbox(label="Text", lines=14, show_copy_button=True)
            ocr_button.click(extract_text, inputs=[document, ocr_prompt],
                             outputs=extracted, api_name="read_text")
    with gr.Accordion("Technical notes", open=False):
        gr.Markdown(
            f"**Model:** https://huggingface.co/{MODEL_ID}\n\n"
            f"**Revision:** `{MODEL_REVISION}`\n\n"
            "A CUDA GPU is required. No audio/video functions are provided. "
            "Custom model code is loaded with trust_remote_code=True. "
            "Model results can be incorrect; review important outputs."
        )
demo.queue(default_concurrency_limit=1, max_size=8)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=False)
