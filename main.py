import os
import json
import argparse
from collections import deque

import cv2


def on_mouse(event, x, y, flags, param):
    global curr_img, prev_img, img, point1, point2, rects, curr_rect, factor, q
    img2 = img.copy()
    if event == cv2.EVENT_LBUTTONDOWN:  # 左键点击
        point1 = (x, y)
        cv2.circle(img2, point1, 10, (0, 255, 0), 5)
        cv2.imshow('image', img2)
    elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):  # 按住左键拖曳
        cv2.rectangle(img2, point1, (x, y), (255, 0, 0), 5)
        cv2.imshow('image', img2)
    elif event == cv2.EVENT_LBUTTONUP:  # 左键释放
        point2 = (x, y)
        if point1 != point2:
            prev_img.append(img.copy())
            cv2.rectangle(img, point1, point2, (0, 0, 255), 5)
            cv2.imshow('image', img)
            min_x = int(min(point1[0], point2[0]) / factor)
            min_y = int(min(point1[1], point2[1]) / factor)
            width = int(abs(point1[0] - point2[0]) / factor)
            height = int(abs(point1[1] - point2[1]) / factor)
            rect = {'x': min_x + curr_rect['x'],
                    'y': min_y + curr_rect['y'],
                    'w': width,
                    'h': height}
            rects.append(rect)
            q.append((curr_img[min_y:min_y + height, min_x:min_x + width], rect))
    elif event == cv2.EVENT_MBUTTONDOWN:
        img = prev_img.pop()
        cv2.imshow('image', img)
        rects.pop()
        q.pop()


def resize_img(img):
    height, weight, _ = img.shape
    factor = min(args.target_h / height, args.target_w / weight)
    return cv2.resize(img, None, fx=factor, fy=factor), factor


def annotate(img_path):
    global curr_img, prev_img, img, point1, point2, rects, curr_rect, factor, q
    rects = []
    q = deque()
    temp = cv2.imread(img_path)
    h, w, _ = temp.shape
    q.append((temp, {'x': 0, 'y': 0, 'w': w, 'h': h}))
    while len(q) != 0:
        prev_img = []
        if args.dfs:
            curr_img, curr_rect = q.pop()
        else:
            curr_img, curr_rect = q.popleft()
        img, factor = resize_img(curr_img)
        cv2.namedWindow('image')
        cv2.setMouseCallback('image', on_mouse)
        cv2.imshow('image', img)
        cv2.waitKey(0)
    return


parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', required=True, type=str)
parser.add_argument('--output_dir', required=True, type=str)
parser.add_argument('--target_h', type=float, default=960.0)
parser.add_argument('--target_w', type=float, default=540.0)
parser.add_argument('--dfs', action='store_true')
args = parser.parse_args()

global curr_img, prev_img, img, point1, point2, rects, curr_rect, factor, q

if __name__ == '__main__':
    for d, _, fs in os.walk(args.data_dir):
        for f in fs:
            if not f.endswith('.jpg'):
                pass
            print('\n\n\nStart new annotating {}'.format(f))
            annotate(os.path.join(d, f))
            with open(os.path.join(args.output_dir, f.replace('jpg', 'json')), 'w') as w:
                json.dump(rects, w, indent=4)
