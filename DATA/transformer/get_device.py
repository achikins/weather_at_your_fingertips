import torch
import platform

def get_device():
    system = platform.system()
    if system == "Windows" and torch.cuda.is_available():
        print("Using CUDA GPU on Windows")
        return torch.device("cuda")
    elif system == "Darwin" and torch.backends.mps.is_available():
        print("Using Metal (MPS) GPU on Mac")
        return torch.device("mps")
    else:
        print("Using CPU")
        return torch.device("cpu")
