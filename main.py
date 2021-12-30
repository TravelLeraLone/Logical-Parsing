import os
import json
import tkinter
import argparse
from collections import deque

import cv2

from tree import Tree
from utils import resize_img


ORGANIZING = ['Iso', 'List', 'Table', 'Stack', 'Same as prev']
ELEMENT = ['Text', 'Picture', 'Icon', 'Box']
ELEMENT_WITH_END = ['Text', 'Picture', 'Icon', 'Box', 'End']
RELATION = ['Beneath', 'Above', 'Left', 'Right', 'Up', 'Down', 'Interspersed', 'Surrounding', 'Inside']
OVERALL = ['Complex', 'Foreground', 'Background', 'Main', 'Header', 'Footer', 'Sider', 'Floater', 'Same as prev']
FUNCTION = ['Informative', 'Navigational', 'Functional', 'Inputting', 'Composite']
STAGE = [OVERALL, ORGANIZING, ELEMENT, ELEMENT_WITH_END, RELATION]


class Asker:
    def __init__(self, page=False, skip=False):
        self.page = page
        if not self.page:
            self.text = 'Please Select Content Label'
        else:
            self.text = 'Page'
        self.function = 'Please Select Functional Label'
        self.skip = skip
        self.stage = 0 if not self.skip else 1
        self.ind = None
        self.flag = False
        self.finish = True
        # self.frame = tkinter.Tk()
        # self.v = tkinter.IntVar()

    def _content_label_processing(self):
        self.ind = self.v.get()
        if self.stage == 0:
            if self.ind != 0:
                self.text = STAGE[self.stage][self.ind]
                self.flag = True
            else:
                self.stage = 1
        elif self.stage == 1:
            if self.ind == len(STAGE[self.stage]) - 1:
                self.text = STAGE[self.stage][self.ind]
                self.flag = True
            self.text = STAGE[self.stage][self.ind] + ' of '
            self.stage = 2
        else:
            self.text += STAGE[self.stage][self.ind]
            if self.stage == 2:
                self.text += ' with ('
                self.stage = 3
            elif self.stage == 3:
                if self.ind == len(ELEMENT_WITH_END) - 1:
                    self.flag = True
                    self.text += ')'
                else:
                    self.text += ' '
                    self.stage = 4
            else:
                self.text += '), ('
                self.stage = 3
        self.frame.destroy()

    def _relabel(self):
        if not self.page:
            self.text = 'Please Select Content Label'
        else:
            self.text = 'Page'
        self.function = 'Please Select Functional Label'
        self.stage = 0 if not self.skip else 1
        self.ind = None
        self.flag = False
        self.finish = False
        self.frame.destroy()

    def _ask(self):
        tkinter.Button(self.frame, text='Relabel', command=self._relabel).pack()
        tkinter.Label(self.frame, text=self.text).pack()
        candidate = STAGE[self.stage]
        for i, l in enumerate(candidate):
            tkinter.Radiobutton(self.frame, text=l, variable=self.v, value=i).pack()
        tkinter.Button(self.frame, text='OK', command=self._content_label_processing).pack()
        self.frame.mainloop()

    def _functional_label_processing(self):
        self.ind = self.v.get()
        self.function = FUNCTION[self.ind]
        self.frame.destroy()

    def _generate(self):
        if self.text == 'Please Select Content Label':
            while not self.flag:
                # for widget in self.frame.winfo_children():
                #     widget.destroy()
                self.frame = tkinter.Tk()
                self.v = tkinter.IntVar()
                self._ask()
        self.finish = True
        if self.text != 'Same as prev':
            self.frame = tkinter.Tk()
            self.v = tkinter.IntVar()
            tkinter.Button(self.frame, text='Relabel', command=self._relabel).pack()
            tkinter.Label(self.frame, text=self.function).pack()
            for i, l in enumerate(FUNCTION):
                tkinter.Radiobutton(self.frame, text=l, variable=self.v, value=i).pack()
            tkinter.Button(self.frame, text='OK', command=self._functional_label_processing).pack()
            self.frame.mainloop()
        return self.finish

    @classmethod
    def run(cls, text=None, skip=False):
        asker = cls(text, skip)
        while not asker._generate():
            pass
        return asker.text, asker.function


def on_mouse(event, x, y, flags, param):
    global curr_img, prev_img, img, point1, point2, tree, curr_rect, factor, q, parent, end_tag, comp
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
            cv2.rectangle(img2, point1, point2, (0, 255, 0), 5)
            cv2.imshow('image', img2)
            if tree.root is None:
                label = Asker.run(text='Page')
            else:
                label = Asker.run(skip=comp)
            if label[0] == 'Same as prev':
                label = q[-1][2].label
            if label[0] not in OVERALL and label[0] != 'Page':
                comp = True
            prev_img.append(img.copy())
            cv2.rectangle(img, point1, point2, (0, 0, 255), 5)
            cv2.imshow('image', img)
            min_x = round(min(point1[0], point2[0]) / factor)
            min_y = round(min(point1[1], point2[1]) / factor)
            width = round(abs(point1[0] - point2[0]) / factor)
            height = round(abs(point1[1] - point2[1]) / factor)
            rect = {'x': min_x + curr_rect['x'],
                    'y': min_y + curr_rect['y'],
                    'width': width,
                    'height': height}
            node = tree.add_children(parent, rect, label)
            q.append((curr_img[min_y:min_y + height, min_x:min_x + width], rect, node))
            end_tag = ord(' ') if q else ord('\r')


def back():
    if parent is None:
        tree.root = None
        return
    for child in parent.children:
        tree.delete_node(child)
    return


def annotate(img_path):
    global curr_img, prev_img, img, point1, point2, tree, curr_rect, factor, q, parent, end_tag, comp
    q = deque()
    temp = cv2.imread(img_path)
    h, w, _ = temp.shape
    tree = Tree((w, h), img_dir=img_path)
    q.append((temp, {'x': 0, 'y': 0, 'width': w, 'height': h}, tree.root))
    history, key_num, comp = [], -1, False

    while q:
        prev_img = []
        if key_num != ord('b'):
            if args.dfs:
                curr_img, curr_rect, parent = q.pop()
            else:
                curr_img, curr_rect, parent = q.popleft()
            history.append(((curr_img, curr_rect, parent), len(q)))
        else:
            last, length = history.pop()
            q.appendleft(last)
            while len(q) > length:
                q.pop()
            curr_img, curr_rect, parent = history[-1][0]
            back()
        img, factor = resize_img(curr_img, args.target_h, args.target_w)
        cv2.namedWindow('image')
        cv2.setMouseCallback('image', on_mouse)
        cv2.imshow('image', img)

        end_tag = ord(' ') if q else ord('\r')
        key_num = cv2.waitKey(0)
        while key_num != end_tag:
            if key_num == ord('b'):
                back()
                break
            if key_num == 8:
                img = prev_img.pop()
                cv2.imshow('image', img)
                _, _, del_node = q.pop()
                tree.delete_node(del_node)
            # print(key_num)
            key_num = cv2.waitKey(0)
    return


parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', required=True, type=str)
parser.add_argument('--output_dir', required=True, type=str)
parser.add_argument('--target_h', type=float, default=960.0)
parser.add_argument('--target_w', type=float, default=540.0)
parser.add_argument('--dfs', action='store_true')
args = parser.parse_args()

global curr_img, prev_img, img, point1, point2, tree, curr_rect, factor, q, parent, end_tag, comp

if __name__ == '__main__':
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    for d, _, fs in os.walk(args.data_dir):
        for f in fs:
            if not f.endswith('.jpg'):
                pass
            print('\n\n\nStart new annotating {}'.format(f))
            annotate(os.path.join(d, f))
            if tree.root is not None:
                with open(os.path.join(args.output_dir, f.replace('jpg', 'json')), 'w') as w:
                    json.dump(tree.formulate(), w, indent=4)

    # tree.show_split()
