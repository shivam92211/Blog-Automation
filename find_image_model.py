"""
A temporary script to find available image generation models for the user's API key.
This version looks for models that support 'generateContent' and specifically
attempts to generate an image to confirm capability.
"""
import os
import sys
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
import time

# Add project root to path to load config
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file to get the API key
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
    sys.exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)

    print("Searching for available models that support multimodal content generation (text to image)...")
    found_multimodal_models = []

    for m in genai.list_models():
        # Check if the model supports content generation
        if "generateContent" in m.supported_generation_methods:
            print(f"\nFound potential multimodal model: {m.name}")
            print(f"  Description: {m.description}")
            print(f"  Supported methods: {m.supported_generation_methods}")
            
            # Now, attempt to generate an image with it to confirm capability
            try:
                test_model = genai.GenerativeModel(model_name=m.name)
                print(f"  Attempting a dummy image generation with {m.name}...")
                
                # Use a small, quick query to avoid long waits
                response = test_model.generate_content(
                    "a small red square",
                    generation_config={
                        "temperature": 0.1,
                        "response_mime_type": "image/png"
                    },
                    request_options={"timeout": 30} # Set a timeout
                )
                
                # Check if the response contains image data
                if response and response.candidates and response.candidates[0].content.parts[0].inline_data:
                    print(f"  ✓ Model '{m.name}' successfully generated image data.")
                    found_multimodal_models.append(m.name)
                else:
                    print(f"  ✗ Model '{m.name}' did not return image data for 'image/png' mime type.")

            except Exception as e:
                print(f"  ✗ Error testing model '{m.name}' for image generation: {e}")
            time.sleep(1) # Small delay to avoid hitting rate limits too quickly

    if found_multimodal_models:
        print("\n==================================================")
        print("RECOMMENDED MODELS FOR IMAGE GENERATION (multimodal):")
        print("==================================================")
        for model_name in found_multimodal_models:
            print(f"- {model_name}")
    else:
        print("\n==================================================")
        print("No models supporting image generation (multimodal) found for your API key.")
        print("Please ensure your API key has access to multimodal models or try a different key.")
        print("==================================================")

except Exception as e:
    print(f"An error occurred: {e}")
