import sys
import torch
import numpy as np
from PIL import Image
from types import ModuleType
from importlib.machinery import ModuleSpec
from transformers import AutoProcessor, AutoModelForCausalLM

# Mock flash_attn to satisfy the internal check without needing the package
if "flash_attn" not in sys.modules:
    mock_spec = ModuleSpec("flash_attn", None)
    mock_lib = ModuleType("flash_attn")
    mock_lib.__spec__ = mock_spec
    sys.modules["flash_attn"] = mock_lib

class ModelManager:
    def __init__(self, model_id="microsoft/Florence-2-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load in float16 to keep VRAM at ~1.1GB
        # 'eager' implementation skips the flash_attn hardware check
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            trust_remote_code=True,
            torch_dtype=torch.float16,
            attn_implementation="eager" 
        ).to(self.device).eval()
        
        self.processor = AutoProcessor.from_pretrained(
            model_id, 
            trust_remote_code=True
        )

    def predict(self, cv2_img):
        """
        Extracts mathematical text or a visual description of the graph.
        """
        # Convert OpenCV BGR to PIL RGB
        image_rgb = cv2_img[:, :, ::-1] 
        pil_image = Image.fromarray(image_rgb)

        # Using Detailed Caption to extract mathematical properties
        prompt = "<DETAILED_CAPTION>" 
        
        inputs = self.processor(text=prompt, images=pil_image, return_tensors="pt").to(self.device)
        inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)

        with torch.no_grad():
            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=512,
                num_beams=3
            )

        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        result = self.processor.post_process_generation(
            generated_text, 
            task=prompt, 
            image_size=(pil_image.width, pil_image.height)
        )

        # Return the resulting string (e.g., "y = 2x + 5")
        return result.get('<DETAILED_CAPTION>', "No equation detected.")