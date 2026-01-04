"""Compatibility shim: expose the original top-level `glow` module

Some WaveGlow checkpoints were saved with `glow` as their module path.
When unpickling, Python must be able to import `glow`. This shim re-exports
the implementation from `tacotron2.waveglow.glow` so existing checkpoints
can be loaded without modifying the saved files.
"""
from tacotron2.waveglow.glow import *

# Also expose common symbols explicitly for clarity
try:
    from tacotron2.waveglow.glow import WaveGlow, remove_weightnorm
except Exception:
    # best-effort; if these names don't exist the import that needs them will still fail later
    pass
