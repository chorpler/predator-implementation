#!/usr/bin/python
import ntpath
from pathlib import Path
import sys
import json
import traceback

import click
import numpy as np
import cv2 as cv
from PIL import Image
from PIL.PngImagePlugin import PngInfo

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


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('input_file', required=True)
@click.argument('output_file', required=False)
@click.option('--k', '-k', is_flag=False, type=int, default=3, help='k-value needed by the sobel transformation. A higher value results in thicker edges. Must be odd and less than 32 (default: 3)')
@click.option('--scale', '-s', is_flag=False, type=int, default=1, help='scale value used in the sobel transformation. A higher value results in brighter edges (default: 1)')
@click.option('--mode', '-m', is_flag=False, type=str, default="min", help='select the minimum or maximum RGB value for each pixel (default: min)')
@click.option('--shrinkage', '-S', is_flag=False, type=int, default=3, help='shrinkage, the amount of pixelization averaging. Value of 3 means 3x3 area. (default: 3)')
@click.option('--auto_output', '-a', is_flag=True, default=False, help='output a file with an auto-generated name (default: false)')
@click.option('--debug', '-d', is_flag=True, help='Turn on debug output (deafult: false)')
def thermalize(input_file, output_file, k=3, scale=1, mode="min", shrinkage=3, auto_output=False, debug=False):
    """
    Implements the GIMP 2.10.x "Predator" filter but using python's opencv library.
    # Basic steps:
    1. "pixelize" (average pixels in an X by X area, the size of which is defined by the user)
    2. "min/max RGB" (finds the smallest or largest of the R, G, B values and set the others to zero)
    3. sobel edge-detect

    # Parameters:
    1. k-value - the k-value needed by the sobel transformation. A higher value results in thicker edges. - default of 3
    2. scale - the scale value used in the sobel transformation. A higher value results in brighter edges. - default of 1
    3. minmax - "min" or "max", chooses whether to select the minimum or maximum RGB value for each pixel - default of "min"
    4. shrinkage - the X of the pixelize step's X by X averaging area - default of 3
    """

    ctx = click.get_current_context()
    if not ntpath.exists(input_file):
        print(f"Could not find input file: '{input_file}'", file=sys.stderr)
        sys.exit(1)
    if mode != 'min' and mode != 'max':
        print(f"Error: mode must be \"min\" or \"max\". Invalid value: '{mode}'", file=sys.stderr)
        sys.exit(1)
    if k % 2 == 0:
        print("Error: k value must be odd", file=sys.stderr)
        sys.exit(1)
    if k > 31:
        print("Error: k value must be less than 32", file=sys.stderr)
        sys.exit(1)

    output_filename = output_file
    if output_file:
        # If output file was specified, make it unique if necessary
        output_filename = get_unique_filename(output_file)
    elif auto_output:
        # If auto-output is enabled, generate a unique filename based on input filename
        generated_output_filename = f"{Path(input_file).stem}.output{Path(input_file).suffix}"
        output_filename = get_unique_filename(generated_output_filename)
    else:
        # No output requested, so don't generate an output filenam
        output_filename = None

    # check if input file is a valid image
    try:
       i = cv.imread(input_file)
       print(f"Image info: {i.shape}", file=sys.stderr)
       hig, wid, _ = i.shape
    except Exception as e:
        print(f"Error: image '{input_file}' not valid:\n{e}", file=sys.stderr)
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
    print(f"Pixel width and height: ({pix_w}, {pix_h})", file=sys.stderr)

    j = minmax_rgb(i, wid, hig, mode)
    i = pixelize(j, pix_w, pix_h)
    img_out = sobel(i, k, scale)
    pil_img, png_data = add_image_metadata(input_file, img_out, k, scale, mode, shrinkage)
    save_and_preview(img_out, pil_img, png_data, output_filename)

if __name__ == '__main__':
    thermalize()
