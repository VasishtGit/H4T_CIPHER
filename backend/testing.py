import torch
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_NAME = "microsoft/phi-4-mini-instruct"
LOCAL_MODEL_PATH = "./my_local_model"

# 1. 4-bit Config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16
)

# ----------------------------
# STEP 1: Load and Save Locally
# ----------------------------
if not os.path.exists(LOCAL_MODEL_PATH):
    print("Downloading and quantizing model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto"
    )

    print(f"Saving model to {LOCAL_MODEL_PATH}...")
    # This is the industry standard way to save locally
    model.save_pretrained(LOCAL_MODEL_PATH)
    tokenizer.save_pretrained(LOCAL_MODEL_PATH)
    print("✅ Model saved locally.")
else:
    print("Local model found, skipping download.")

# ----------------------------
# STEP 2: Reload for Inference
# ----------------------------
print("\nReloading model from local disk...")
# Note: We still pass the bnb_config to tell the system HOW to read the files
model_reloaded = AutoModelForCausalLM.from_pretrained(
    LOCAL_MODEL_PATH,
    quantization_config=bnb_config,
    device_map="auto"
)
tokenizer_reloaded = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH)

# ----------------------------
# STEP 3: Test Run
# ----------------------------
text = "Write a simple Manim animation"
inputs = tokenizer_reloaded(text, return_tensors="pt").to("cuda")

print("\nGenerating...")
with torch.no_grad():
    output_ids = model_reloaded.generate(
        **inputs,
        max_new_tokens=512,   # Increased to 1024 to allow full code blocks
        do_sample=True,
        temperature=0.7,
        top_p=0.9,             # Added top_p for better quality
        pad_token_id=tokenizer_reloaded.eos_token_id,
        repetition_penalty=1.1 # Prevents the model from getting stuck in loops
    )
print("\n=== OUTPUT ===")
print(tokenizer_reloaded.decode(output_ids[0], skip_special_tokens=True))