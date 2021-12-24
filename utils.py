import cv2


def resize_img(img, h, w):
    height, weight, _ = img.shape
    factor = min(h / height, w / weight)
    return cv2.resize(img, None, fx=factor, fy=factor), factor
