

import os

import cv2
import numpy as np


def smooth_signal(signal, window_size=15):
    """Simple moving average smoothing"""
    kernel = np.ones(window_size) / window_size
    return np.convolve(signal, kernel, mode='same')


def crop_projection(image, margin=0, debug=False):
    """
    Crop black borders using projection-based method.

    Args:
        image: input image (BGR or grayscale)
        margin: safety margin inside detected boundary
        debug: if True, print debug info

    Returns:
        cropped image
    """
    # --- Step 1: Convert to grayscale ---
    if len(image.shape) == 3:
        print("Converting to grayscale")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
#
    h, w = gray.shape
    print(f"Image size: {w}x{h}")
#
    # --- Step 2: Compute projections ---
    row_mean = np.mean(gray, axis=1)   # shape: [h]
    col_mean = np.mean(gray, axis=0)   # shape: [w]
    # col_std = np.std(gray, axis=0)
    # row_std = np.std(gray, axis=1)
#
    # --- Step 3: Smooth signals ---
    row_mean_s = smooth_signal(row_mean, window_size=25)
    col_mean_s = smooth_signal(col_mean, window_size=25)
    # col_std = smooth_signal(col_std)
    # row_std = smooth_signal(row_std)
#
    # --- Step 4: Define adaptive threshold ---
    # Use percentile: more robust than fixed number
    threshold = np.percentile(gray, 11)
    # std_threshold = np.percentile(col_std, 40)
#
    if debug:
        print(f"Threshold: {threshold:.2f}")
#
    # --- Step 5: Find top boundary ---
    top = 0
    for i in range(h):
        if row_mean_s[i] > threshold:
            top = i
            break
#
    # --- Step 6: Find bottom boundary ---
    bottom = h - 1
    for i in range(h - 1, -1, -1):
        if row_mean_s[i] > threshold:
            bottom = i
            break
#
    # --- Step 7: Find left boundary ---
    left = 0
    for j in range(w):
        if col_mean_s[j] > threshold:
            left = j
            break
#
    # --- Step 8: Find right boundary ---
    right = w - 1
    for j in range(w - 1, -1, -1):
        if col_mean_s[j] > threshold:
            right = j
            break
#
    # --- Step 9: Apply margin ---
    top = max(top + margin, 0)
    bottom = min(bottom - margin, h)
    left = max(left + margin, 0)
    right = min(right - margin, w)
#
    if debug:
        print(f"Crop box: top={top}, bottom={bottom}, left={left}, right={right}")
# Crop box: top=0, bottom=2898, left=487, right=3003
    # --- Step 10: Crop ---
    cropped = image[top:bottom, left:right]
#
    return cropped


input_dir = r"D:\datasets\wales_gov\penarth_head_to_cold_knap\1942 4220"
output_dir =  r"D:\datasets\image_preprocessing\01_remove_border\penarth_head_to_cold_knap\1942_4220"

tif_list = [f for f in os.listdir(input_dir) if f.endswith('.tif') or f.endswith('.tiff')]

for tif in tif_list:  # just take the first one for testing
    input_path = os.path.join(input_dir, tif)
    output_path = os.path.join(output_dir, tif.replace('.tif', '_cropped.tif').replace('.tiff', '_cropped.tiff'))
    print(f"Processing {input_path} -> {output_path}")
    image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    cropped = crop_projection(image, margin=0, debug=True)
    cv2.imwrite(output_path, cropped)






def smooth_signal(signal, window_size=25):
    kernel = np.ones(window_size) / window_size
    return np.convolve(signal, kernel, mode='same')


def evaluate_side(mean_vals, std_vals, threshold_mean, threshold_std, min_width=20):
    """
    Evaluate how likely a side is a border.

    Returns:
        boundary index, score
    """
    length = len(mean_vals)
    print(f"Evaluating side of length {length} with mean threshold {threshold_mean:.2f} and std threshold {threshold_std:.2f}")
#
    # Detect candidate region from one side
    count = 0
    boundary = None
#
    for i in range(length):
        is_dark = mean_vals[i] < threshold_mean
        is_flat = std_vals[i] < threshold_std
#
        if is_dark and is_flat:
            count += 1
        else:
            if count >= min_width:
                boundary = i
                break
            count = 0
#
    # If never broke but border extends further
    if boundary is None:
        boundary = count if count >= min_width else 0
#
    # Compute score
    score = 0
    if count >= min_width:
        score += 1
    if np.mean(mean_vals[:max(count,1)]) < threshold_mean:
        score += 1
    if np.mean(std_vals[:max(count,1)]) < threshold_std:
        score += 1
#
    return boundary, score


def crop_projection_scored(image, margin=5, debug=False):
    # --- Convert to grayscale ---
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
#
    h, w = gray.shape
#
    # --- Projections ---
    row_mean = np.mean(gray, axis=1)
    col_mean = np.mean(gray, axis=0)
#
    row_std = np.std(gray, axis=1)
    col_std = np.std(gray, axis=0)
#
    # --- Smooth ---
    row_mean = smooth_signal(row_mean)
    col_mean = smooth_signal(col_mean)
    row_std = smooth_signal(row_std)
    col_std = smooth_signal(col_std)
#
    # --- Adaptive thresholds ---
    threshold_mean = np.percentile(gray, 25)
    threshold_std = np.percentile(row_std, 40)
#
    if debug:
        print(f"Mean threshold: {threshold_mean:.2f}")
        print(f"Std threshold: {threshold_std:.2f}")
#
    # --- Evaluate sides ---
    left_b, left_score = evaluate_side(col_mean, col_std,threshold_mean, threshold_std)
#
    right_b, right_score = evaluate_side(col_mean[::-1], col_std[::-1],
                                         threshold_mean, threshold_std)
    right_b = w - right_b  # convert back
#
    top_b, top_score = evaluate_side(row_mean, row_std,
                                    threshold_mean, threshold_std)
#
    bottom_b, bottom_score = evaluate_side(row_mean[::-1], row_std[::-1],
                                           threshold_mean, threshold_std)
    bottom_b = h - bottom_b
#
    if debug:
        print("Scores:")
        print(f"Left: {left_score}, Right: {right_score}, Top: {top_score}, Bottom: {bottom_score}")
#
    # --- Decide which sides to crop ---
    min_score = 2  # require confidence
#
    left = left_b if left_score >= min_score else 0
    right = right_b if right_score >= min_score else w
    top = top_b if top_score >= min_score else 0
    bottom = bottom_b if bottom_score >= min_score else h
#
    # --- Apply margin carefully ---
    left = max(left + margin, 0)
    top = max(top + margin, 0)
    right = min(right - margin, w)
    bottom = min(bottom - margin, h)
#
    if debug:
        print(f"Crop box: {top}:{bottom}, {left}:{right}")
#
    cropped = image[top:bottom, left:right]
#
    return cropped


input_dir = r"D:\datasets\wales_gov\penarth_head_to_cold_knap\1942 4220"
output_dir =  r"D:\datasets\image_preprocessing\01_remove_border\penarth_head_to_cold_knap\1942_4220"

tif_list = [f for f in os.listdir(input_dir) if f.endswith('.tif') or f.endswith('.tiff')]

for tif in tif_list:
    input_path = os.path.join(input_dir, tif)
    output_path = os.path.join(output_dir, tif.replace('.tif', '_cropped_1.tif').replace('.tiff', '_cropped_1.tiff'))
    print(f"Processing {input_path} -> {output_path}")
    image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    cropped = crop_projection_scored(image, margin=10, debug=True)
    cv2.imwrite(output_path, cropped)




input_dir = r"D:\datasets\wales_gov\penarth_head_to_cold_knap\1942 4220"
output_dir =  r"D:\datasets\image_preprocessing\01_remove_border\penarth_head_to_cold_knap\1942_4220"

tif_list = [f for f in os.listdir(input_dir) if f.endswith('.tif') or f.endswith('.tiff')]

tif = tif_list[0]  # just take the first one for testing
input_path = os.path.join(input_dir, tif)
output_path = os.path.join(output_dir, tif.replace('.tif', '_cropped_1.tif').replace('.tiff', '_cropped_2.tiff'))

image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

row = gray[200,:]  # first row, all columns
col = gray[:,20]  # first column, all rows

#  create a figure with col values
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(row, label='Column Mean')
plt.legend()
plt.title('Column Mean and Thresholds')
plt.show()



