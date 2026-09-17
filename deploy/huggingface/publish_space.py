"""Upload the reviewed package to an existing private Docker Space."""
import argparse
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse


def publish(api, space_id, folder):
    if not re.fullmatch(r"BKillings/[A-Za-z0-9][A-Za-z0-9_.-]*", space_id):
        raise ValueError("deployment must target the BKillings namespace")
    info = api.space_info(space_id)
    if info.private is not True or info.sdk != "docker":
        raise ValueError("refusing upload: target must be an existing private Docker Space")
    return api.upload_folder(
        repo_id=space_id, repo_type="space", folder_path=str(folder),
        parent_commit=info.sha,
        commit_message="Deploy reviewed DeepCore reference service",
    )


def verify_deployment(api, space_id, token, source_commit, timeout=600):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        info = api.space_info(space_id)
        if info.private is not True:
            raise RuntimeError("Space visibility changed; verification stopped")
        runtime = api.get_space_runtime(space_id)
        if runtime.stage in {"BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"}:
            raise RuntimeError(f"Space failed: {runtime.stage}")
        host = getattr(info, "host", None)
        if runtime.stage == "RUNNING" and host:
            base = host if host.startswith("https://") else "https://" + host
            parsed = urlparse(base)
            if parsed.scheme != "https" or not parsed.hostname.endswith(".hf.space") or parsed.username or parsed.password or parsed.port:
                raise RuntimeError("invalid Space host")
            request = urllib.request.Request(base.rstrip("/") + "/api/status", headers={"Authorization": f"Bearer {token}"})
            # Do not forward credentials through redirects.
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *args, **kwargs):
                    return None
            try:
                with urllib.request.build_opener(NoRedirect()).open(request, timeout=10) as response:
                    evidence = json.load(response)
                checks = evidence.get("checks", {})
                expected = {"transaction_signature", "quorum_certificate", "block_commitment", "deterministic_replay"}
                if (evidence.get("source_commit") == source_commit and set(checks) == expected
                        and all(value is True for value in checks.values())
                        and evidence.get("mode") == "reference-simulation"
                        and evidence.get("production_certified") is False):
                    print(json.dumps({"space": space_id, "source_commit": source_commit, "reference_service_verified": True, "production_certified": False}))
                    return
            except (urllib.error.URLError, TimeoutError, ValueError):
                pass
        time.sleep(10)
    raise TimeoutError("uploaded, but the matching deployed revision did not pass health verification")


if __name__ == "__main__":
    from huggingface_hub import HfApi
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    args = parser.parse_args()
    token = os.environ["HF_TOKEN"]
    space_id = os.environ["HF_SPACE_ID"]
    source_commit = json.loads((Path(args.folder) / "deployment.json").read_text())["source_commit"]
    api = HfApi(token=token)
    publish(api, space_id, args.folder)
    verify_deployment(api, space_id, token, source_commit)
