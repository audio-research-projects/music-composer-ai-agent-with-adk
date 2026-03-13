# DDSP Timbre Transfer Quality Guide

## Parameters That Affect Quality

### 1. Pitch Shift (`pitch_shift`)
- **Range**: -24.0 to +24.0 (semitones)
- **-12.0**: One octave down (deeper, bass-like)
- **+12.0**: One octave up (higher, whistle-like)
- **0.0**: Original pitch
- **Tip**: Small shifts (-2 to +2) often sound more natural

### 2. Loudness Shift (`loudness_db_shift`)
- **Range**: -20.0 to +20.0 (dB)
- **+3.0 to +6.0**: Boost quiet audio
- **-3.0 to -6.0**: Reduce clipping/distortion
- **Tip**: Match the target instrument's natural dynamics

### 3. Model Parameters (in `build_ddsp_model`)

#### Frame Rate
- **Default**: 250 fps
- **Higher** (500+): Better temporal resolution, more CPU/GPU
- **Lower** (125): Faster, less detailed

#### Harmonic Distribution
- **Current**: 100 harmonics
- **More**: Richer, more complex timbre
- **Fewer**: Simpler, clearer tone

#### Noise Component
- **Current**: 25 frequency bins
- **More**: Better breath/noise texture (for wind instruments)
- **Fewer**: Cleaner, more synthetic sound

### 4. Audio Preprocessing Tips

#### Before Sending to DDSP:
```python
import librosa

# 1. Load at correct sample rate
audio, sr = librosa.load(file, sr=16000, mono=True)

# 2. Normalize to prevent clipping
audio = audio / np.max(np.abs(audio)) * 0.8

# 3. Trim silence
trimmed, _ = librosa.effects.trim(audio, top_db=20)

# 4. Ensure consistent length (multiples of 4s work best)
```

## Recommended Settings by Use Case

### Vocals to Violin
```python
pitch_shift=0.0,           # Keep original pitch
loudness_db_shift=3.0,     # Boost slightly
```

### Voice to Bass/Deep Instrument
```python
pitch_shift=-12.0,         # One octave down
loudness_db_shift=6.0,     # Significant boost
```

### Bright/Ethereal Effect
```python
pitch_shift=7.0,           # Perfect fifth up
loudness_db_shift=-2.0,    # Slightly softer
```

### Natural Sounding
```python
pitch_shift=-1.0,          # Slight detune
loudness_db_shift=0.0,     # No change
```

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Robotic/metallic sound | Too much pitch shift | Use smaller shifts (-2 to +2) |
| Muddy/unclear | Too low pitch + loudness | Reduce loudness_db_shift |
| Harsh/distorted | Input too loud | Normalize input to 0.8 |
| Weak/thin | Input too quiet | Normalize + boost loudness_db_shift |
| Gaps/stuttering | Frame alignment issues | Ensure exact 15.00s duration |

## Advanced: Multiple Passes

For best quality, try:
1. First pass: subtle shift (-2 to +2)
2. Post-process: EQ to match target instrument
3. Optional: Second DDSP pass with different model
