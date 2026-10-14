# Cosmos 3 Nano video generation: deployment decision

## Current diagnosis (2026-10-14)

- The Foundry account key and OpenAI-compatible chat endpoint work: `POST https://aicocukvideonew.services.ai.azure.com/openai/v1/chat/completions` returned HTTP 200.
- The managed deployment route `/managed-deployments/nvidia--cosmos3-nano/v1/videos/sync` returned 401 with `Authorization: Bearer` and 500 with `api-key`.
- The generic Foundry deployment is therefore **not yet a verified Cosmos 3 video server**. Do not keep retrying this endpoint or treat HTTP 500 as a generated video.
- The current Azure deployment is an A100 80 GB managed deployment. NVIDIA's current vLLM-Omni Cosmos3-Nano online-serving recipe explicitly documents 1x H200 141 GB / B300, and uses the `vllm/vllm-omni:cosmos3` runtime / `vllm serve nvidia/Cosmos3-Nano --omni`. It does not list A100 as a validated online-serving configuration.

## Recommended path

Use a GPU host on which we control the serving runtime and run NVIDIA's vLLM-Omni Cosmos3-Nano server. Keep the existing Foundry deployment only if its chat endpoint is useful for other tasks; it does not currently provide the needed video API.

Before creating anything, check the estimated hourly price and quota. The currently shown A100 deployment is paid capacity; stop or delete it in Azure Foundry if you do not need it while preparing the video server. Do not leave a paid GPU running idle.

### Runtime requirements from upstream

- Ubuntu 22.04+ and a supported NVIDIA CUDA driver/runtime.
- NVIDIA vLLM-Omni Cosmos3 container or matching vLLM-Omni source version.
- Upstream's documented online-serving hardware is 1x H200 141 GB / B300.
- For guarded generation, install `cosmos-guardrail`, accept the gated `nvidia/Cosmos-1.0-Guardrail` model terms on Hugging Face, and configure a Hugging Face token. Do not disable guardrails just to hide a setup error.

Upstream recipe: https://github.com/vllm-project/vllm-omni/blob/main/recipes/cosmos3/Cosmos3-Nano.md

### Server launch (on the supported GPU host)

The upstream launch command is:

```bash
vllm serve nvidia/Cosmos3-Nano --omni --host 0.0.0.0 --port 8000 --init-timeout 1800
```

If using the upstream container, use the current official `vllm/vllm-omni:cosmos3` image and follow its published container/driver instructions. Do not expose port 8000 directly to the public internet. Restrict inbound access to a private network or trusted source IPs, and enable an API key on the server before connecting GitHub Actions.

### Verify the server before connecting the song pipeline

1. `GET /v1/models` must return the Cosmos3 model.
2. Send the upstream multipart request to `POST /v1/videos/sync` with `Accept: video/mp4`.
3. Verify the response is an actual MP4 with nonzero size and playable video streams.
4. Only after this succeeds, wire the endpoint into the repository's video-worker contract and keep YouTube publishing disabled until the generated song visuals and audio pass quality checks.

Example upstream text-to-video request (use a short clip for the first test):

```bash
curl -sS -X POST http://YOUR_PRIVATE_VIDEO_HOST:8000/v1/videos/sync \
  -H "Accept: video/mp4" \
  -F "model=nvidia/Cosmos3-Nano" \
  -F "prompt=A cute yellow duckling, puppy and bunny dance in a bright pastel meadow, full bodies visible, smooth child-friendly motion, no text." \
  -F "negative_prompt=blurry, distorted, low quality, jittery, deformed, watermark" \
  -F "size=640x480" -F "num_frames=25" -F "fps=8" \
  -F "num_inference_steps=10" -F "guidance_scale=6.0" \
  -F "seed=42" -o cosmos3-test.mp4
```

Do not use the Azure Foundry account key as the video server's API key; they are separate credentials. Once the server has its own API key and private endpoint, store those as GitHub Actions secrets, never in source code.

## Cost and publishing guardrails

- Do not create another GPU deployment until the supported GPU type, quota, network access, and hourly price are confirmed.
- Stop/delete any unused paid GPU resource after tests.
- Do not enable automatic YouTube publishing as part of this setup. TR002 remains blocked pending audio/lyric matching and visual quality approval.
