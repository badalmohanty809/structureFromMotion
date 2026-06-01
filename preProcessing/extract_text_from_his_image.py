# date: 01-06-2026
# author: MohantyB
# topic: historic aerial image processing
# description:


import os
import json
import re
import google.generativeai as genai
from PIL import Image


image_path = r"D:\datasets\wales_gov\penarth_head_to_cold_knap\1951 5129\154.tiff"

out_dir = r"D:\datasets\image_preprocessing\text_extraction\penarth_head_to_cold_knap\1951_5129"
png_path = os.path.join(out_dir, os.path.splitext(os.path.basename(image_path))[0] + "_ocr.png")
json_path = os.path.join(out_dir, os.path.splitext(os.path.basename(image_path))[0] + "_ocr.json")

if not os.path.exists(out_dir):
    os.makedirs(out_dir)


def tiff_to_png(tiff_path, png_path, max_size=(1500, 1500)):
    img = Image.open(tiff_path)
    # ✅ Resize (important)
    img.thumbnail(max_size)
    img.save(png_path, "PNG")
    return png_path


def extract_json_block(json_text):
    match = re.search(r"\{.*\}", json_text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return None


def get_image_dpi(image_path):
    img = Image.open(image_path)
    dpi = img.info.get("dpi", None)
    if dpi is None:
        print(f"Warning: DPI not found for {image_path}. returning None.")
    else:
        dpi = tuple(float(x) for x in dpi)
    return dpi


def save_result(image_path, image_dpi, raw_text, interpreted_json, json_path):
    # Combine everything
    data = {
        "image_name": image_path,
        "image_dpi": image_dpi,
        "raw_text": raw_text,
        "interpreted": interpreted_json
    }
    # Save JSON
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved: {json_path}")


image_png = tiff_to_png(image_path, png_path)
image = Image.open(image_png)

# Read key from environment
api_key = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.5-flash")


response = model.generate_content([
    image,
    "Extract all border text from this aerial image."
])


# print(response.text)
raw_text = response.text.strip()
cleaned_text = response.text.strip().replace("\n", " ").replace("*", "")


response2 = model.generate_content(f"""
    You are an expert in interpreting historical aerial photograph metadata.
    Here is extracted border text:
    {cleaned_text}
    Interpret and convert into structured JSON with:
    - film reference
    - date
    - altitude
    - focal length
    - region
    - classification
""")


# print(response2.text)
json_text = response2.text
interpreted_json = extract_json_block(json_text)

image_dpi = get_image_dpi(image_path)

save_result(image_path, image_dpi, raw_text, interpreted_json, json_path)


