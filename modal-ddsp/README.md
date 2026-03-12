# DDSP Timbre Transfer on Modal.com

Serverless GPU-powered timbre transfer using [DDSP](https://github.com/magenta/ddsp) (Differentiable Digital Signal Processing) deployed on [Modal.com](https://modal.com).

## 🎯 What is this?

This package deploys DDSP neural audio synthesis models to Modal.com's serverless GPU infrastructure, enabling:

- **Timbre Transfer**: Transform audio to sound like a different instrument (violin, flute, sax, trumpet)
- **Pitch Analysis**: Extract pitch and loudness contours
- **Serverless**: Pay only for compute time, zero idle costs
- **API Access**: REST API + MCP server for integration

## 📁 Files

| File | Description |
|------|-------------|
| `modal_app.py` | Core Modal app with GPU functions |
| `api_server.py` | FastAPI web server for HTTP API |
| `mcp_bridge.py` | MCP server for local agent integration |
| `download_models.py` | Utility to pre-download models |

## 🚀 Quick Start

### 1. Install Modal CLI

```bash
pip install modal
```

### 2. Authenticate with Modal

```bash
modal token new
```

### 3. Deploy the Application

```bash
# Deploy the core app
cd modal-ddsp
modal deploy modal_app.py

# Or deploy the FastAPI server
modal deploy api_server.py
```

### 4. Download Models

```bash
# Download all pre-trained models
modal run modal_app::download_all_models

# Or download specific model
modal run modal_app::download_model --model-name violin
```

Available models:
- `violin` - String instrument
- `flute` - Woodwind, soft tones
- `tenor_sax` - Jazz saxophone
- `trumpet` - Bright brass
- `flute2` - Alternative flute

## 🔌 Usage

### Option 1: MCP Server (for ADK Agent)

The MCP bridge connects your local agent to Modal:

```bash
# In your agent config, add this MCP server:
# Command: uv --directory modal-ddsp run mcp_bridge.py

# Or run directly:
python mcp_bridge.py
```

Tools available:
- `list_models` - List available models
- `download_model` - Download a model
- `timbre_transfer` - Transform audio
- `batch_transfer` - Process multiple files
- `analyze_pitch` - Analyze audio pitch

### Option 2: REST API

After deploying `api_server.py`:

```bash
# Get endpoint URL
modal app show ddsp-api

# Use the API
curl -X POST "https://your-url.modal.run/transfer" \
  -F "audio=@input.wav" \
  -F "model=violin" \
  -F "pitch_shift=0" \
  --output output.wav
```

### Option 3: Direct Modal Functions

```python
import modal

# Call the deployed function
f = modal.Function.lookup("ddsp-timbre-transfer", "timbre_transfer")

with open("input.wav", "rb") as f:
    audio_bytes = f.read()

result = f.remote(
    audio_data=audio_bytes,
    model_name="violin",
    pitch_shift=0.0,
)

# Save output
with open("output.wav", "wb") as f:
    f.write(result["output_audio"])
```

## 💰 Costs (Modal.com)

| Resource | Price | Typical Usage |
|----------|-------|---------------|
| GPU (T4) | ~$0.00016/sec | 30s audio ≈ $0.005 |
| CPU | ~$0.0000045/sec | Negligible |
| Storage | $0.10/GB/month | Models ~500MB |
| Egress | $0.10/GB | Audio files small |

**Example**: Processing a 30-second audio clip costs approximately **$0.005** (half a cent).

## 🔧 Configuration

### Environment Variables

```bash
# .env file
MODAL_TOKEN_ID=your_token_id
MODAL_TOKEN_SECRET=your_token_secret
MODAL_APP_NAME=ddsp-timbre-transfer
```

### Agent Integration

Update your ADK agent config to include the MCP bridge:

```python
# In your agent's config.py
def ddsp_modal_mcp() -> McpToolset:
    return mcp_toolset(
        directory=BASE_DIR / "modal-ddsp",
        script="mcp_bridge.py",
        name="ddsp_modal",
    )
```

## 🎵 Model Training (Optional)

To train your own models:

1. Follow [DDSP training guide](https://github.com/magenta/ddsp/tree/main/ddsp/training)
2. Export checkpoint to `/models/your_model/`
3. Upload to Modal volume:
   ```bash
   modal volume put ddsp-models your_model/ /models/your_model
   ```

## 🐛 Troubleshooting

### Model not found
```bash
# Download the model first
modal run modal_app::download_model --model-name violin
```

### Cold start slow
First GPU invocation takes ~30s (container startup). Subsequent calls are fast.

### Out of memory
Reduce audio length (max 60s) or use GPU with more VRAM (A10G instead of T4).

### Connection errors
```bash
# Check Modal status
modal app show ddsp-timbre-transfer

# View logs
modal app logs ddsp-timbre-transfer
```

## 📚 Resources

- [DDSP Paper](https://arxiv.org/abs/2001.04643)
- [Modal Documentation](https://modal.com/docs)
- [Pre-trained Models](https://github.com/magenta/ddsp/tree/main/ddsp/colab)

## 📝 License

MIT License - See main project LICENSE
