# date: 02-03-2026
# author: MohantyB
# topic: historic aerial image processing
# description: script to enhance the input image by

import os
import numpy as np
import cv2
from skimage import exposure
from PIL import Image
import matplotlib.pyplot as plt


# set the OpenCV log level to error to suppress warnings
cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
# os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

sub_dir = "1951_5129"
in_prt_dir = r"D:\datasets\image_preprocessing\remove_border\penarth_head_to_cold_knap"
out_prt_dir = r"D:\datasets\image_preprocessing\histogram_equalisation\penarth_head_to_cold_knap"

input_image_dir = os.path.join(in_prt_dir, sub_dir)
out_dir = os.path.join(out_prt_dir, sub_dir)

if not os.path.exists(out_dir):
    print(f"Output directory {out_dir} does not exist. Creating it.")
    os.makedirs(out_dir)


# read the input image paths from the text file and make a list
# input_image_list = open(input_image_txt, 'r').read().splitlines()
input_image_list = os.listdir(input_image_dir)
input_image_list = [os.path.join(input_image_dir, img) for img in input_image_list if 'br.' in img]

print(f'total {len(input_image_list)} files found in the folder')

# exit if there is no file in the folder
if len(input_image_list) == 0:
    exit()

def generate_histogram(image: np.ndarray, out_path: str, type: str) -> None:
    '''
    function to generate histogram and cdf of the input image and save
    the plot

    image: input image as numpy array
    out_path: path to save the histogram plot
    return: None
    '''
    # For color images, convert to grayscale for histogram
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Determine bit depth from dtype (e.g., uint8 -> 8 bits)
    bit_depth = image.dtype.itemsize * 8
    # Number of possible intensity levels
    num_bins = 2 ** bit_depth
    # Histogram range is [0, max_value + 1]
    hist_range = [0, num_bins]
    # Calculate histogram with num_bins bins over range [0, num_bins]
    hist,_ = np.histogram(image.flatten(), bins = num_bins, range = hist_range)
    # Compute cumulative sum of histogram values
    # (Cumulative Distribution Function)
    cdf = hist.cumsum()
    # Normalize CDF to match histogram maximum for visualization
    cdf_normalized = cdf * float(hist.max()) / cdf.max()
    # clear the current figure
    plt.clf()
    # Plot the normalized CDF as a blue line
    plt.plot(cdf_normalized, color = 'b')
    # Plot histogram with num_bins bins as red bars
    plt.hist(image.flatten(), bins = num_bins, range = hist_range,
             color = 'r')
    # Set x-axis limits to [0, num_bins]
    plt.xlim([0,num_bins])
    # add axis names
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Frequency')
    # add title
    plt.title(f'Histogram and CDF of the {type} Image')
    # Add legend identifying CDF and histogram lines
    plt.legend(('cdf','histogram'), loc = 'upper left')
    # Save the plot to the specified output path
    plt.savefig(out_path)
    # Display the plot
    # plt.show()

def save_image(image: np.ndarray, out_path: str, type: str) -> None:
    '''
    function to save the input image as tif file

    image: input image as numpy array
    out_path: path to save the image
    return: None
    '''
    # save the image using OpenCV
    cv2.imwrite(out_path, image)
    print(f"\t{type} image saved at: {out_path}")

def img_linear_stretch(img_gray_clahe: np.ndarray) -> np.ndarray:
    '''
    function to rescale the pixel values of the input image using linear
    stretching based on the 1st and 99th percentiles to avoid influence
    of outliers

    img_gray_clahe: input image as numpy array
    return: rescaled image as numpy array
    '''
    min_val = np.uint8(np.floor(np.percentile(img_gray_clahe, 1)))
    max_val = np.uint8(np.ceil(np.percentile(img_gray_clahe, 99)))
    img_rescale = exposure.rescale_intensity(img_gray_clahe, in_range=(min_val, max_val))
    return img_rescale

def clahe_equalize_image(img: np.ndarray, clipLimit=2.0,
                         tileGridSize=(8,8)) -> np.ndarray:
    '''
    Contrast Limited Adaptive Histogram Equalization
    Works for both grayscale and color images

    img_gray: input image (despite name, can be color or grayscale)
    return: enhanced image with same number of bands as input
    '''
    # Check if image is color or grayscale
    clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
#
    if len(img.shape) == 3:
        # Color image - convert to LAB, apply CLAHE to L channel
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        # apply CLAHE to L channel
        l_clahe = clahe.apply(l)
        # rescale L channel using percentiles to avoid influence of
        # outliers
        l_rescale = img_linear_stretch(l_clahe)
        # Merge back and convert to BGR
        lab_rescale = cv2.merge([l_rescale, a, b])
        img_rescale = cv2.cvtColor(lab_rescale, cv2.COLOR_LAB2BGR)
    else:
        # Grayscale image
        img_gray_clahe = clahe.apply(img)
        # rescale using percentiles to avoid influence of outliers
        img_rescale = img_linear_stretch(img_gray_clahe)
#
    return img_rescale

def save_image_with_dpi(input_path: str, image: np.ndarray, out_path: str, type: str):
    '''
    Save image preserving DPI from input image
    '''
    # read original DPI
    with Image.open(input_path) as img_in:
        dpi = img_in.info.get('dpi', (300, 300))  # fallback if missing
    # convert OpenCV (BGR) to PIL (RGB)
    if len(image.shape) == 3:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        image_rgb = image
    pil_img = Image.fromarray(image_rgb)
    # save with original DPI
    pil_img.save(out_path, dpi=dpi)
    print(f"\t{type} Image saved with preserved DPI at: {out_path}")


for image_path in input_image_list:
    print(f"Processing image: {image_path}")
    image_name = image_path.split('\\')[-1].split('.')[0]
    # read the image using OpenCV
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    # check if the image is read properly
    assert image is not None, "file could not be read"
    # check if the image is grayscale or color
    if len(image.shape) == 2:  # Grayscale image
        print("The image is grayscale.")
    elif len(image.shape) == 3:  # Color image
        print("The image is color.")
    elif len(image.shape) == 4:  # Multichannel image (e.g., RGBA)
        print("The image is multichannel (e.g., RGBA).")
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    # if the image is not greyscale the the codes to enhance the
    # image will have to chnage as the below functions work with
    # grey scale images only
    #
    # check the original image
    generate_histogram(image, os.path.join(out_dir, image_name + '_original_histogram.png'), type='original')
    # save_image(image, os.path.join(out_dir, image_name + '_original_image.tif'), type='original')
    #
    # option 3: apply CLAHE as per HSFM paper
    # only if image has no border
    clahe_hsfm_image = clahe_equalize_image(image)
    # save the clahe hsfm enhanced image
    generate_histogram(clahe_hsfm_image, os.path.join(out_dir, image_name + '_clahe_histogram.png'), type='clahe_hsfm')
    # save_image(clahe_hsfm_image, os.path.join(out_dir, image_name + '_clahe.tif'), type='clahe_hsfm')
    save_image_with_dpi(image_path, clahe_hsfm_image, os.path.join(out_dir, image_name + '_clahe.tif'), type='clahe_hsfm')
    print(f"\tCLAHE enhanced image saved at: {os.path.join(out_dir, image_name + '_clahe.tif')}")


