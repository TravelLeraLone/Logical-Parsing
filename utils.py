import json

import cv2

global img
global point1, point2


def main():
    global img
    img = cv2.imread('data/488.jpg')
    rects = json.load(open('output/zzh/488.json'))
    for rect in rects:
        point1 = (rect['x'], rect['y'])
        point2 = (rect['x'] + rect['w'], rect['y'] + rect['h'])
        cv2.rectangle(img, point1, point2, (255, 0, 0), 5)
    img = cv2.resize(img, (540, 960))
    cv2.imshow('image', img)
    cv2.waitKey(0)


if __name__ == '__main__':
    main()
