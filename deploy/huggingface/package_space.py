"""Build an explicit source allowlist; never mirror the private repository."""
import argparse
import json
from pathlib import Path
import re
import shutil

FILES = {
    "deploy/huggingface/Dockerfile": "Dockerfile",
    "deploy/huggingface/README.md": "README.md",
    "deploy/huggingface/requirements.txt": "requirements.txt",
    "SERVICES/__init__.py": "SERVICES/__init__.py",
    "SERVICES/reference_api.py": "SERVICES/reference_api.py",
    **{f"CORE/{name}.py": f"CORE/{name}.py" for name in (
        "deepcore_runtime", "deepcore_crypto", "deepcore_key_registry", "deepcore_consensus"
    )},
}


def package(root, destination, source_commit):
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source_commit must be the full GitHub commit SHA")
    root, destination = Path(root).resolve(), Path(destination)
    if destination.exists():
        raise ValueError("package destination must not already exist")
    for source in FILES:
        path = root / source
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"invalid deployment source: {source}")
    destination.mkdir(parents=True)
    for source, target in FILES.items():
        output = destination / target
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / source, output)
    (destination / "deployment.json").write_text(json.dumps({"source_commit": source_commit}) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    package(Path(__file__).resolve().parents[2], args.output, args.source_commit)
