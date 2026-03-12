#!/usr/bin/env python3
"""Batch process multiple audio files with DDSP timbre transfer.

Usage:
    python batch_process.py input/ --model violin --output output/
    python batch_process.py input/ --model tenor_sax --pattern "*.wav"
"""
import argparse
from pathlib import Path
from timbre_transfer import timbre_transfer
import json


def batch_process(
    input_dir: Path,
    output_dir: Path,
    model_path: Path,
    pattern: str = "*.wav",
    **kwargs
) -> dict:
    """Process multiple audio files.
    
    Args:
        input_dir: Directory with input files
        output_dir: Directory for output files
        model_path: Path to DDSP model
        pattern: File glob pattern
        **kwargs: Additional arguments for timbre_transfer
        
    Returns:
        Summary dict with results
    """
    input_files = list(input_dir.glob(pattern))
    
    if not input_files:
        print(f"No files matching '{pattern}' in {input_dir}")
        return {'processed': 0, 'failed': 0, 'files': []}
    
    print(f"Found {len(input_files)} files to process")
    print(f"Model: {model_path}")
    print(f"Output directory: {output_dir}")
    print()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    for i, input_file in enumerate(input_files, 1):
        print(f"[{i}/{len(input_files)}] Processing: {input_file.name}")
        
        output_file = output_dir / f"{input_file.stem}_processed{input_file.suffix}"
        
        try:
            result = timbre_transfer(
                input_path=input_file,
                output_path=output_file,
                model_path=model_path,
                **kwargs
            )
            results.append({
                'input': str(input_file.name),
                'output': str(output_file.name),
                'status': 'success',
                'elapsed': result.get('elapsed_seconds', 0),
            })
            print(f"  ✓ Saved to: {output_file.name}\n")
            
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            results.append({
                'input': str(input_file.name),
                'status': 'error',
                'error': str(e),
            })
    
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - successful
    
    summary = {
        'total': len(input_files),
        'successful': successful,
        'failed': failed,
        'files': results,
    }
    
    # Save summary
    summary_file = output_dir / 'batch_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("=" * 50)
    print(f"Batch complete: {successful}/{len(input_files)} successful")
    print(f"Summary saved to: {summary_file}")
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="Batch DDSP timbre transfer")
    parser.add_argument("input_dir", type=Path, help="Input directory")
    parser.add_argument("--model", default="violin",
                       choices=["violin", "flute", "tenor_sax", "trumpet", "flute2"],
                       help="Model to use")
    parser.add_argument("--model-path", type=Path, help="Custom model path")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output directory")
    parser.add_argument("--pattern", default="*.wav", help="File pattern (default: *.wav)")
    parser.add_argument("--pitch-shift", type=float, default=0.0, help="Pitch shift")
    parser.add_argument("--loudness-db", type=float, default=0.0, help="Loudness shift")
    parser.add_argument("--models-dir", type=Path, default=Path(__file__).parent / "models",
                       help="Models directory")
    
    args = parser.parse_args()
    
    if not args.input_dir.exists():
        print(f"Error: Input directory not found: {args.input_dir}")
        return 1
    
    # Determine model path
    if args.model_path:
        model_path = args.model_path
    else:
        model_path = args.models_dir / args.model
    
    if not model_path.exists():
        print(f"Error: Model not found: {model_path}")
        print(f"Download it with: python download_models.py --model {args.model}")
        return 1
    
    # Run batch process
    batch_process(
        input_dir=args.input_dir,
        output_dir=args.output,
        model_path=model_path,
        pattern=args.pattern,
        pitch_shift=args.pitch_shift,
        loudness_db_shift=args.loudness_db,
    )
    
    return 0


if __name__ == "__main__":
    exit(main())
