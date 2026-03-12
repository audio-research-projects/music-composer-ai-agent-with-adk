#!/bin/bash
# Quick test script for Modal DDSP deployment

set -e

echo "=== Modal DDSP Quick Test ==="
echo ""

# Check if modal is installed
if ! command -v modal &> /dev/null; then
    echo "❌ Modal CLI not found. Install with: pip install modal"
    exit 1
fi

# Check if sox is installed for generating test audio
if ! command -v sox &> /dev/null; then
    echo "⚠️  SoX not found. Installing test audio generation may not work."
    echo "   Install with: apt-get install sox libsox-fmt-all"
fi

echo "1. Checking deployed apps..."
modal app list | grep ddsp-timbre-transfer || {
    echo "❌ ddsp-timbre-transfer not found. Deploy with: modal deploy modal_app.py"
    exit 1
}
echo "✅ App found"

echo ""
echo "2. Listing models..."
python3 test_transfer.py --list || modal run modal_app.py::list_models

echo ""
echo "3. Downloading violin model (if needed)..."
python3 test_transfer.py --download violin || modal run modal_app.py::download_model --model-name violin

# Generate test audio if not exists
if [ ! -f "test_input.wav" ]; then
    echo ""
    echo "4. Generating test audio (5 seconds, 440Hz sine wave)..."
    if command -v sox &> /dev/null; then
        sox -n -r 16000 -c 1 test_input.wav synth 5 sine 440
        echo "✅ Created test_input.wav"
    else
        echo "⚠️  Cannot generate test audio. Please provide a WAV file."
        exit 1
    fi
else
    echo ""
    echo "4. Using existing test_input.wav"
fi

echo ""
echo "5. Running timbre transfer (violin)..."
python3 test_transfer.py test_input.wav --model violin --output test_output_violin.wav

echo ""
echo "=== Test Complete ==="
echo "Input: test_input.wav"
echo "Output: test_output_violin.wav"

# Play if possible
if command -v aplay &> /dev/null; then
    echo ""
    read -p "Play output? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        aplay test_output_violin.wav
    fi
fi
