#!/usr/bin/python
import numpy as np
import cv2 as cv
import sys

def minmax_rgb(i, w, h, m):
    x = 0
    minmax = 0
    while x < h:
        y = 0
        while y < w:
            if m == 'min':
                minmax = min(i[x][y][0],i[x][y][1],i[x][y][2])
            else:
                minmax = max(i[x][y][0],i[x][y][1],i[x][y][2])
            if minmax == i[x][y][0]: # blue is least/most
                i[x][y][1] = 0
                i[x][y][2] = 0 
            if minmax == i[x][y][1]: # green is least/most
                i[x][y][0] = 0
                i[x][y][2] = 0
            if minmax == i[x][y][2]: # red is least/most
                i[x][y][0] = 0
                i[x][y][1] = 0
            y+=1
        x+=1 
    return i
    
def pixelize(i, pix_w, pix_h):
    i_h, i_w = i.shape[:2]
    # shrink image
    i = cv.resize(i, (pix_w, pix_h), interpolation=cv.INTER_CUBIC)
    # resize
    pixelized = cv.resize(i, (i_w, i_h), interpolation=cv.INTER_NEAREST)
    return pixelized

def sobel(i, k, s):
    # the general convention is to use a gaussian blur on the image,
    # but the pixelization should take care of that here.
    sobx = cv.Sobel(i,cv.CV_16S,1,0,ksize=k,scale=s,delta=0)
    soby = cv.Sobel(i,cv.CV_16S,0,1,ksize=k,scale=s,delta=0)
    abSobx = cv.convertScaleAbs(sobx) # makes the sobels absolute
    abSoby = cv.convertScaleAbs(soby)
    # approximates the sobel algo using built-in cv2 functions
    # the more precise methods produced far less consistent output,
    # likely due to floating-point rounding errors
    sobtot = cv.addWeighted(abSobx, 0.5, abSoby, 0.5, 0)
    cv.imshow('output', sobtot)

# def save_and_preview(sobtot_output, unique_output_file):
def save_and_preview(cv_data, pil_data, png_metadata, unique_output_file):
    if unique_output_file:
        pil_data.save(unique_output_file, pnginfo=png_metadata)
        # cv.imwrite(unique_output_file, sobtot_output)
    show_preview(cv_data)


def show_preview(sobtot_output):
    cv.imshow(f"Preview", sobtot_output)
    cv.waitKey(0)
    cv.destroyAllWindows()


# check if a valid filename is given
try:
   i = cv.imread(sys.argv[1])
   hig, wid, _ = i.shape
except:
    print("Error: image does not exist")
    sys.exit(1)

k = 3 # the 'k' value for the sobel filter. default of 3
mode = 'min' # can choose to minimize or maximize RGB. default of min
shrinkage = 3 # amount of pixelization averaging. default of 3x3 area
scale = 1 # scale of the sobel transform (edge "brightness" in output)

if len(sys.argv) > 2: # if we have a second arg, it should be k
    k = int(sys.argv[2])
    if k%2 == 0:
        print("Error: k must be odd.")
        sys.exit(1)
    if k > 31:
        print("Error: k must be less than 32")
        sys.exit(1)
if len(sys.argv) > 3:
    scale = int(sys.argv[3])
if len(sys.argv) > 4: # third argument should be min or max
    mode = sys.argv[4]
    if mode != 'min' and mode != 'max':
        print("Error: third flag must be \"min\" or \"max\"")
        sys.exit(1)
if len(sys.argv) > 5: # last arg should be the amount of pixelization
    shrinkage = int(sys.argv[5])

pix_w, pix_h = (int(wid/shrinkage), int(hig/shrinkage))
j = minmax_rgb(i, wid, hig, mode)
i = pixelize(j, pix_w, pix_h)
sobel(i, k, scale)
