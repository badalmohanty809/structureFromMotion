# date: 02-03-2026
# author: MohantyB
# topic: historic aerial image processing
# description: script to enhance the input image by

import numpy as np
import cv2
import matplotlib.pyplot as plt

# path for the text file which contains the list of input image paths
input_image_txt = ('C:\\Users\\c25045127\\OneDrive - Cardiff University\\'
                   'data_analysis\\image_list.txt')

# define the out path
out_dir = ('D:\\datasets\\image_preprocessing\\penarth_head_to_cold_knap\\'
           '1951_5129\\71-79\\')


# read the input image paths from the text file and make a list
input_image_list = open(input_image_txt, 'r').read().splitlines()



image_path  = input_image_list[2]
# read the image using OpenCV
image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

assert image is not None, "file could not be read"


# check if the image is grayscale or color
if len(image.shape) == 2:  # Grayscale image
    print("The image is grayscale.")
elif len(image.shape) == 3:  # Color image
    print("The image is color.")

# if the image is not greyscale the the codes to enhance the
# image will have to chnage as the below functions work with grey
# scale images only


def generate_histogram(image: np.ndarray, out_path: str, type: str) -> None:
    '''
    function to generate histogram and cdf of the input image and save
    the plot

    image: input image as numpy array
    out_path: path to save the histogram plot
    return: None
    '''
    # Determine bit depth from dtype (e.g., uint8 -> 8 bits)
    bit_depth = image.dtype.itemsize * 8
    # Number of possible intensity levels
    num_bins = 2 ** bit_depth
    # Histogram range is [0, max_value + 1]
    hist_range = [0, num_bins]
    # Calculate histogram with num_bins bins over range [0, num_bins]
    hist,_ = np.histogram(image.flatten(),num_bins,hist_range)
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
    plt.hist(image.flatten(),num_bins,hist_range, color = 'r')
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
    function to save the input image as png file

    image: input image as numpy array
    out_path: path to save the image
    return: None
    '''
    # clear the current figure
    plt.clf()
    # display the image
    plt.imshow(image, cmap='gray')
    # add title to the image
    plt.title(type)
    # remove axis
    plt.axis('off')
    # save the image
    plt.savefig(out_path)
    # plt.show()


# chcek the original image
generate_histogram(image, out_dir + 'original_histogram.png', type='original')
save_image(image, out_dir + 'original_image.png', type='original')

# option 1: apply histogram equalization to enhance the image contrast
enhanced_image = cv2.equalizeHist(image)
# save the enhanced image
generate_histogram(enhanced_image, out_dir + 'enhanced_histogram.png',
                   type='enhanced')
save_image(enhanced_image, out_dir + 'enhanced_image.png', type='enhanced')


# option 2: apply CLAHE with default parameters
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
clahe_image = clahe.apply(image)
# save the clahe enhanced image
generate_histogram(clahe_image, out_dir + 'clahe_histogram.png', type='clahe')
save_image(clahe_image, out_dir + 'clahe_image.png', type='clahe')


# option 3: apply CLAHE as per HSFM paper - not sure the np.clip is a good idea when the image has borders
# clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
# clahe_hsfm_image_1 = clahe.apply(image)
# # apply linear histogram stretch ignoring the black or white pixels
# min_val = np.uint8(np.floor(np.percentile(clahe_hsfm_image_1, 1)))
# max_val = np.uint8(np.ceil (np.percentile(clahe_hsfm_image_1, 99)))
# clahe_hsfm_image_2 = np.clip(clahe_hsfm_image_1, min_val, max_val)
# clahe_hsfm_image = cv2.normalize(clahe_hsfm_image_2, None, 0, 255, cv2.NORM_MINMAX)
# # save the clahe hsfm enhanced image
# generate_histogram(clahe_hsfm_image, out_dir + 'clahe_hsfm_histogram.png', type='clahe_hsfm')
# save_image(clahe_hsfm_image, out_dir + 'clahe_hsfm_image.png', type='clahe_hsfm')


