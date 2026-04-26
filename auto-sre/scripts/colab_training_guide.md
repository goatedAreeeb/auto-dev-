### Cell 2 — Install dependencies

```python
# Step 1: upgrade torch FIRST (Unsloth cpp extensions need >= 2.4.0)
# Colab ships 2.5+cu121 by default — this ensures compatibility.
!pip install "torch>=2.4.0" --index-url https://download.pytorch.org/whl/cu121 -q

# Step 2: install Unsloth (latest, Colab-compatible)
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" -q

# Step 3: install TRL + mergekit
# New TRL versions import mergekit at module level — must be installed.
!pip install "trl>=0.15.0" "mergekit" -q

# Step 4: remaining deps
!pip install "transformers>=4.40" "accelerate>=0.30" \
             "peft>=0.10" "bitsandbytes>=0.43" \
             "datasets>=2.18" "requests" "matplotlib" -q

# Verify
import torch
print(f"torch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
import trl
print(f"trl: {trl.__version__}")
import mergekit
print("mergekit: OK")
print("All deps ready ✓")
```

> **If torch upgrade breaks Colab's environment** (rare), use the pinned TRL workaround instead:
> ```python
> # Alternative: pin TRL to last version before mergekit was required
> !pip install "trl==0.15.2" "mergekit" -q
> ```
