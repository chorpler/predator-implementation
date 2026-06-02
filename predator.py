#!/usr/bin/python
import ntpath
from pathlib import Path
import sys
import json
import traceback

import click
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
    return sobtot


# def thermalize(input_file, output_file, k=3, scale=1, mode="min", shrinkage=3, auto_output=False, debug=False):
def add_image_metadata(input_file: str, image_data, val_k: int, val_scale: int, val_mode: str, val_shrinkage: int):
    try:
        src_image = Image.open(input_file)
        existing_metadata = src_image.info

        rgb_img = cv.cvtColor(image_data, cv.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)

        predator_info = {
            "k": val_k,
            "scale": val_scale,
            "mode": val_mode,
            "shrinkage": val_shrinkage
        }
        predator_info_json = json.dumps(predator_info)

        new_png_info = PngInfo()
        for key, value in existing_metadata.items():
            # Filter out internal properties that PIL handles automatically
            if isinstance(value, str):
                new_png_info.add_text(key, value)

        new_png_info.add_text("PredatorInfo", predator_info_json)

        return pil_img, new_png_info

    #     exif_bytes = piexif.dump(piexif.load(input_file))
    #
    #     success, encoded_img = cv.imencode('.png', image_data)
    #     if success:
    #         image_with_exif = piexif.insert(exif_bytes, encoded_img.tobytes())
    #         return image_with_exif
    except Exception as e:
        print(f"add_image_metadata error while saving metadata: {e}\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)



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


def get_unique_filename(file_path: str, digits: int = 3) -> str:
    """
    Generates a unique file path by appending an incrementing counter
    (e.g., '_1', '_2') if a file with the same name already exists.
    """
    path_object = Path(file_path)
    if not path_object.exists():
        return str(path_object)

    stem = path_object.stem
    extension = path_object.suffix
    counter = 1

    # Loop until an available name is found
    while True:
        new_name = f"{stem}_{counter:0{digits}}{extension}"
        new_path = path_object.with_name(new_name)

        if not new_path.exists():
            return str(new_path)

        counter += 1

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

    # Old code, to be removed if new code works
    #
    # if len(sys.argv) > 2: # if we have a second arg, it should be k
    #     k_value = int(sys.argv[2])
    #     if k_value%2 == 0:
    #         print("Error: k must be odd.")
    #         sys.exit(1)
    #     if k_value > 31:
    #         print("Error: k must be less than 32")
    #         sys.exit(1)
    # if len(sys.argv) > 3:
    #     scale = int(sys.argv[3])
    # if len(sys.argv) > 4: # third argument should be min or max
    #     mode = sys.argv[4]
    #     if mode != 'min' and mode != 'max':
    #         print("Error: third flag must be \"min\" or \"max\"")
    #         sys.exit(1)
    # if len(sys.argv) > 5: # last arg should be the amount of pixelization
    #     shrinkage = int(sys.argv[5])

pix_w, pix_h = (int(wid/shrinkage), int(hig/shrinkage))
j = minmax_rgb(i, wid, hig, mode)
i = pixelize(j, pix_w, pix_h)
sobel(i, k, scale)
