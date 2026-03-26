import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "mistralai/Mistral-7B-v0.1"

# ----------------------------
# STEP 1: Load model + tokenizer
# ----------------------------
print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

model.eval()

# ----------------------------
# STEP 2: Apply INT8 quantization
# ----------------------------
print("Quantizing model...")
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear},   # Quantize linear layers
    dtype=torch.qint8
)

# ----------------------------
# STEP 3: Save as .pth
# ----------------------------
print("Saving quantized model...")
torch.save(quantized_model.state_dict(), "mistral_quantized.pth")

print("✅ Saved as mistral_quantized.pth")

# =========================================================
# 🔁 LOADING + RUNNING (separate step, but included here)
# =========================================================

print("\nReloading model for inference...")

# Recreate model structure
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# Apply SAME quantization again
model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear},
    dtype=torch.qint8
)

# Load saved weights
model.load_state_dict(torch.load("mistral_quantized.pth"))
model.eval()

# ----------------------------
# STEP 4: Forward pass on text
# ----------------------------
text = "Write a simple Manim animation for a sine wave"

inputs = tokenizer(text, return_tensors="pt")

with torch.no_grad():
    output_ids = model.generate(
        **inputs,
        max_length=150
    )

output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

print("\n=== OUTPUT ===")
print(output_text)