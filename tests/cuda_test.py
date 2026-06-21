
import sys

print(f"Python version: {sys.version}")

# Test 1: PyTorch CUDA
try:
    import torch
    print(f"\n✅ PyTorch version: {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   CUDA version: {torch.version.cuda}")
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("   ⚠️  CUDA not available — CPU-only PyTorch is installed")
except ImportError:
    print("\n❌ PyTorch not installed")

# Test 2: llama-cpp-python CUDA
try:
    from llama_cpp import Llama
    import llama_cpp
    print(f"\n✅ llama-cpp-python version: {llama_cpp.__version__}")
    # Check if CUDA backend is compiled in
    try:
        supports_gpu = llama_cpp.llama_supports_gpu_offload()
        print(f"   GPU offload supported: {supports_gpu}")
    except AttributeError:
        print("   ⚠️  Cannot detect GPU offload support (older version)")
except ImportError:
    print("\n❌ llama-cpp-python not installed")

# Test 3: sentence-transformers device
try:
    import sentence_transformers
    print(f"\n✅ sentence-transformers version: {sentence_transformers.__version__}")
except ImportError:
    print("\n❌ sentence-transformers not installed")

print("\n--- Done ---")
