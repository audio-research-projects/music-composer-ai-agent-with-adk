# Local DDSP Timbre Transfer

Local testing environment for DDSP (Differentiable Digital Signal Processing) neural audio synthesis.

## 🎯 Purpose

This folder provides a local environment for testing DDSP timbre transfer **without** using Modal.com's cloud infrastructure. Useful for:

- Development and debugging
- Processing audio locally (no internet required after models downloaded)
- Testing new models
- Batch processing without cloud costs

## 📁 Structure

```
local-ddsp/
├── requirements.txt      # Python dependencies
├── download_models.py    # Download pre-trained models
├── timbre_transfer.py    # Single file processing
├── batch_process.py      # Multiple files processing
├── test_local.py         # Test environment setup
├── models/               # Downloaded models (gitignored)
├── input/                # Input audio files (gitignored)
└── output/               # Output audio files (gitignored)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd local-ddsp

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

**Requirements:**
- Python 3.9 or 3.10 (recommended for TF 2.11 compatibility)
- ~4GB RAM minimum
- ~2GB disk space per model

### 2. Test Setup

```bash
python test_local.py
```

This checks:
- All packages installed correctly
- TensorFlow version compatibility
- Creates test audio file

### 3. Download Models

```bash
# List available models
python download_models.py --list

# Download a specific model
python download_models.py --model violin

# Download all models
python download_models.py --all
```

Available models:
- `violin` (~50MB) - String instrument
- `flute` (~50MB) - Woodwind
- `tenor_sax` (~50MB) - Jazz saxophone
- `trumpet` (~50MB) - Brass instrument
- `flute2` (~50MB) - Alternative flute

### 4. Run Timbre Transfer

```bash
# Basic usage
python timbre_transfer.py input/test_tone.wav --model violin

# With custom output path
python timbre_transfer.py my_audio.wav --model tenor_sax --output result.wav

# With pitch shift (+2 semitones)
python timbre_transfer.py input.wav --model flute --pitch-shift 2

# Adjust loudness (+3dB)
python timbre_transfer.py input.wav --model trumpet --loudness-db 3

# Combine multiple options
python timbre_transfer.py input.wav --model violin --pitch-shift -2 --loudness-db 5 -o output.wav
```

### 5. Batch Processing

```bash
# Process all WAV files in a directory
python batch_process.py input_folder/ --model violin --output output_folder/

# With specific pattern
python batch_process.py recordings/ --model tenor_sax --output processed/ --pattern "*.mp3"

# With pitch shift
python batch_process.py input/ --model flute --pitch-shift 3 --output shifted/
```

## 🔧 Troubleshooting

### TensorFlow Version Issues

If you get errors about TensorFlow Probability version:

```bash
# Check versions
python -c "import tensorflow as tf; import tensorflow_probability as tfp; print(f'TF: {tf.__version__}, TFP: {tfp.__version__}')"

# Should be: TF 2.10-2.15, TFP 0.18-0.23
# If not, reinstall:
pip install -r requirements.txt --force-reinstall
```

### GPU Support (Optional)

For faster processing with NVIDIA GPU:

```bash
# Install GPU version of TensorFlow
pip install tensorflow-gpu==2.11.0

# Verify GPU is detected
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

### Out of Memory

- Reduce audio length (max 60 seconds recommended)
- Close other applications
- Use CPU instead of GPU if VRAM limited

### Model Not Found

```bash
# Download the model first
python download_models.py --model violin

# Verify it exists
ls models/
```

## 🎵 Creating Test Audio

```bash
# Generate sine wave (requires sox)
sox -n -r 16000 -c 1 test_tone.wav synth 5 sine 440

# Or use the test script (creates audio automatically)
python test_local.py
```

## 📊 Performance

| Hardware | 30s Audio Processing |
|----------|---------------------|
| CPU (4 cores) | 30-60 seconds |
| GPU (GTX 1060) | 5-10 seconds |
| GPU (RTX 3090) | 1-3 seconds |

## 🔗 Integration with Agent

Once tested locally, you can:

1. **Use Modal for production** (see `modal-ddsp/` folder)
2. **Keep local for development** (this folder)
3. **Create hybrid approach** - local for testing, Modal for production

## 📚 Resources

- [DDSP Paper](https://arxiv.org/abs/2001.04643)
- [DDSP GitHub](https://github.com/magenta/ddsp)
- [Pre-trained Models](https://github.com/magenta/ddsp/tree/main/ddsp/colab)

## 📝 License

Same as main project (MIT)
