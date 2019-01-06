import numpy as np
from PIL import Image


def global_fill(im: Image.Image, fro: tuple, to: tuple):
    data = np.array(im)  # both of these work fine. pycharm just doesn't like them
    try:
        red, green, blue, alpha = data.T
    except ValueError:
        red, green, blue = data.T
    areas = (red == fro[0]) & (green == fro[1]) & (blue == fro[2])
    data[..., :-1][areas.T] = to
    return Image.fromarray(data)


def shift_hue(im: Image.Image, relative_shift: int):
    data = np.array(im.convert("HSV"))
    data[..., 0] = (data[..., 0] + relative_shift) % 360
    return Image.fromarray(data, "HSV").convert("RGBA")


def invert_colors(im: Image.Image):
    data = np.array(im.convert("RGBA"))
    data[..., :3] = 255 - data[..., :3]
    return Image.fromarray(data, "RGBA")


def merge_down(top: Image.Image, bottom: Image.Image, x: int=0, y: int=0, center: bool=False):
    if center:
        x -= round(top.width / 2)
        y -= round(top.height / 2)
    bottom.alpha_composite(top, dest=(x, y))


if __name__ == "__main__":
    image = Image.open("C:/Users/Kaesekaiser/Pictures/bharat.jpg")
    print(np.array(image.convert("HSV")))
    print(np.array(shift_hue(image, 15)))
