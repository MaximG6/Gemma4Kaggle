from llama_cpp import llama_supports_gpu_offload
import os
print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES"))
print("GPU offload:", llama_supports_gpu_offload())
