---
title: MiniCPM-o 2.6 Vision Studio
emoji: 👁️
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 4.44.1
python_version: 3.10
app_file: app.py
pinned: false
suggested_hardware: l4x1
license: apache-2.0
models:
  - openbmb/MiniCPM-o-2_6
---

# MiniCPM-o 2.6 Vision Studio

An advisory image-understanding Gradio demo using the official
[OpenBMB MiniCPM-o 2.6](https://huggingface.co/openbmb/MiniCPM-o-2_6)
model, pinned to a specific upstream revision.

**Features:** image Q&A, two-image comparison and OCR. Vision only;
audio, live video, streaming and TTS are not enabled.

## Deployment (manual, secret-protected)

This source lives in `AI/minicpm-o-2-6-space/` in the private DeepCore
GitHub repository. To publish from GitHub Actions:

1. Create a Hugging Face access token with the smallest necessary
   repository-write permission to create/upload the private Space. Keep
   the token out of issues, PRs, code, logs and chat messages.
2. Set it as a **GitHub Actions repository secret named HF_TOKEN** under
   GitHub repository Settings → Secrets and variables → Actions.
3. Review and merge the corresponding GitHub pull request.
4. Run the **Publish MiniCPM Vision Space** workflow manually.
5. The workflow creates or uploads the `BKillings/minicpm-o-2-6-vision-demo`
   **private** Gradio Space. It does **not** select or purchase GPU hardware.
6. Confirm hosting/billing independently, then select **L4 1x** in the
   Hugging Face Space Settings → Hardware. Upgrade if GPU memory requires it.
7. Inspect the Space build/runtime logs and test with a non-sensitive image.

Hugging Face repository write authorization, hosting eligibility and a paid
GPU are **not** provided by a GitHub workflow. An Actions run succeeding
does not prove model inference succeeds.

To deploy from a locally authenticated machine instead, install
`huggingface_hub==0.25.2` and run
`python publish_space.py --repo-id BKillings/minicpm-o-2-6-vision-demo`.
The Space needs GPU access before this model can answer image requests.

**Trust:** Custom upstream code executes via `trust_remote_code=True`;
review it prior to deployment. The model has no access to wallets,
DeepCore ledgers or trading APIs. Keep the Space private while testing.
