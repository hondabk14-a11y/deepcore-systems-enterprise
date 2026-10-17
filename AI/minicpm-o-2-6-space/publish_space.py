"""Publish to a private Hugging Face Space with an environment-provided HF_TOKEN."""
import argparse
from pathlib import Path
from huggingface_hub import HfApi

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", required=True, help="BKillings/minicpm-o-2-6-vision-demo")
    args = parser.parse_args()
    if args.repo_id != "BKillings/minicpm-o-2-6-vision-demo":
        parser.error("Target repo must be BKillings/minicpm-o-2-6-vision-demo")
    api = HfApi()
    api.create_repo(
        repo_id=args.repo_id,
        repo_type="space",
        space_sdk="gradio",
        private=True,
        exist_ok=True,
    )
    root = Path(__file__).resolve().parent
    api.upload_folder(
        folder_path=str(root),
        repo_id=args.repo_id,
        repo_type="space",
        allow_patterns=["README.md", "app.py", "inference.py", "requirements.txt"],
        commit_message="Deploy MiniCPM-o 2.6 vision demonstration",
    )
    print("Space source uploaded. No GPU assigned. Configure hardware in Hugging Face Settings.")

if __name__ == "__main__":
    main()
