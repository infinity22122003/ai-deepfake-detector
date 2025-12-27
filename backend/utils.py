import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
from typing import List, Tuple
import numpy as np


def load_model(path: str, device: str = "cpu") -> torch.nn.Module:
    """
    Attempt to load a model from a file. Supports TorchScript, a saved nn.Module, or a checkpoint
    dict containing 'state_dict'. If you have a custom model class, consider scripting the model
    (torch.jit.script/trace) and saving that as model.pt so it loads reliably in production.
    """
    map_location = torch.device(device)
    try:
        # Prefer TorchScript if available
        model = torch.jit.load(path, map_location=map_location)
        model.eval()
        model.to(map_location)
        return model
    except Exception:
        pass

    data = torch.load(path, map_location=map_location)

    # If checkpoint dict with state_dict
    if isinstance(data, dict) and "state_dict" in data:
        # Try a generic model (ResNet18->binary) as a helpful fallback
        try:
            import torchvision.models as models
            model = models.resnet18(pretrained=False)
            # Replace final layer to single-output for binary classification
            model.fc = torch.nn.Linear(model.fc.in_features, 1)
            model.load_state_dict(data.get("state_dict"))
            model.eval()
            model.to(map_location)
            return model
        except Exception:
            raise RuntimeError("Loaded checkpoint contains 'state_dict' but could not instantiate fallback model."
                               " Please provide a scripted model or a full nn.Module in model.pt")

    # If the object itself is a Module
    if isinstance(data, torch.nn.Module):
        model = data
        model.eval()
        model.to(map_location)
        return model

    raise RuntimeError("Unsupported model file format. Provide a TorchScript model, a saved nn.Module, or a checkpoint dict with 'state_dict'.")


# Preprocessing: resize+center crop to 224 and normalize (ImageNet stats)
DEFAULT_TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def preprocess_image(image: Image.Image, transform=DEFAULT_TRANSFORM) -> torch.Tensor:
    """Return a float32 tensor normalized and ready for model input (C,H,W)."""
    return transform(image).unsqueeze(0)


def infer_on_frames(frames: List[Image.Image], model: torch.nn.Module, device: str = "cpu", batch_size: int = 8) -> Tuple[float, List[float]]:
    """
    Run inference on a list of PIL images. Returns aggregated score (mean) and per-frame scores.
    Assumes binary classification (single-output logit). If model outputs >1 dims, converts via softmax
    and returns probability of class 1 when two classes are present.
    """
    map_device = torch.device(device)
    model.to(map_device)
    model.eval()

    tensors = []
    for img in frames:
        t = preprocess_image(img)
        tensors.append(t)

    # Stack in batches
    all_scores = []
    with torch.no_grad():
        for i in range(0, len(tensors), batch_size):
            batch = torch.cat(tensors[i:i + batch_size], dim=0).to(map_device)
            out = model(batch)
            if isinstance(out, tuple) or isinstance(out, list):
                out = out[0]
            out = out.detach().cpu()

            # Handle shapes: (N,1) or (N,) => binary logits
            if out.dim() == 2 and out.shape[1] == 1:
                probs = torch.sigmoid(out.view(-1))
                all_scores.extend(probs.tolist())
            elif out.dim() == 1:
                probs = torch.sigmoid(out)
                all_scores.extend(probs.tolist())
            else:
                # Multi-class: take softmax and use probability of class 1 if exists, else top class
                probs = F.softmax(out, dim=1)
                if out.shape[1] >= 2:
                    class1 = probs[:, 1]
                    all_scores.extend(class1.tolist())
                else:
                    # fallback: take max probability
                    maxp, _ = torch.max(probs, dim=1)
                    all_scores.extend(maxp.tolist())

    if not all_scores:
        raise RuntimeError("No predictions were produced")

    mean_score = float(np.mean(all_scores))
    return mean_score, all_scores
