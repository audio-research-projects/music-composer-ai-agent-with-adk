#!/usr/bin/env python3
"""Simple DDSP test with manual model construction."""

import numpy as np
import os
import tensorflow as tf

# Suppress TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

print(f"TensorFlow version: {tf.__version__}")

# Load checkpoint directly
checkpoint_path = "/tmp/ddsp_models/solo_violin_ckpt/model.ckpt-38100"

# Read checkpoint to see variables
from tensorflow.python.training import py_checkpoint_reader

reader = py_checkpoint_reader.NewCheckpointReader(checkpoint_path)
var_to_shape_map = reader.get_variable_to_shape_map()

print("\nCheckpoint variables (first 50):")
for i, key in enumerate(sorted(var_to_shape_map.keys())):
    if i >= 50:
        print("  ... (truncated)")
        break
    print(f"  {key}: {var_to_shape_map[key]}")

print("\nModel can be built from these components:")
print("- rnn_fc_decoder: GRU-based decoder")
print("- harmonic: Additive synthesizer")  
print("- filtered_noise: Filtered noise synth")
print("- reverb: Convolution reverb")
