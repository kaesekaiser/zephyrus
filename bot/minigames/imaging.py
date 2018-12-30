import numpy as np
from PIL import Image


def global_fill(im: Image.Image, fro: tuple, to: tuple):
    data = np.array(im)  # both of these work fine. pycharm just doesn't like them
    red, green, blue, alpha = data.T
    red_areas = (red == fro[0]) & (green == fro[1]) & (blue == fro[2])
    data[..., :-1][red_areas.T] = to
    return Image.fromarray(data)


def merge_down(top: Image.Image, bottom: Image.Image, x: int=0, y: int=0, center: bool=False):
    if center:
        x -= round(top.width / 2)
        y -= round(top.height / 2)
    bottom.alpha_composite(top, dest=(x, y))


if __name__ == "__main__":
    image = Image.open("C:/Users/Kaesekaiser/Pictures/bharat.jpg")
    print(image.mode)
