import random
from collections import deque

import cv2

from utils import resize_img

ID_GENERATOR = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
LENGTH = 10


class Node:
    def __init__(self, lsid=None, tid=None, rect=None, meta='', label=None, template_id=None, parent=None):
        self.id = lsid if lsid is not None else ''.join(random.choices(ID_GENERATOR, k=LENGTH))
        self.tid = tid
        self.rect = rect
        self.children = []
        self.meta = meta
        self.label = label
        self.template_id = template_id
        self.parent = parent
        self.depth = 0 if parent is None else parent.depth + 1


class Tree:
    def __init__(self, size, img_dir=None):
        self.size = size
        self.root = None
        self.nodes = {}
        self.relation = []
        self.parent = None
        self.img_dir = img_dir

    @classmethod
    def from_ls(cls, annotation):
        def _prepare_rect(rect, origin):
            return {'x': rect['x'] * origin[0] / 100, 'y': rect['y'] * origin[1] / 100,
                    'width': rect['width'] * origin[0] / 100, 'height': rect['height'] * origin[1] / 100}

        def _prepare_kwargs(lsnode):
            kwargs = {'lsid': lsnode['id'],
                      'label': lsnode['value']['labels'][0] if 'labels' in lsnode['value']
                      else lsnode['value']['rectanglelabels'][0],
                      'rect': _prepare_rect(lsnode['value'], tree.size)}
            if 'meta' not in lsnode:
                return kwargs
            meta = lsnode['meta']['text']
            assert len(meta) == 1
            meta = meta[0]
            if meta[0] == 'o':
                tid = meta.split()[0][1:]
                meta = meta[len(tid) + 2:]
            elif meta.split()[0].isdigit():
                tid = meta.split()[0]
                meta = meta[len(tid) + 1:]
            else:
                tid = None
            if 'tid' in lsnode:
                tid = lsnode['tid']
            if 'template_id' in lsnode:
                kwargs['template_id'] = lsnode['template_id']
            kwargs['tid'] = tid
            kwargs['meta'] = meta
            return kwargs

        if 'annotations' in annotation:
            result = annotation['annotations'][0]['result']
            source = 'ls'
            node_pool = [item for item in result if item['type'] == 'labels']
            relations = [item for item in result if item['type'] == 'relation']
        else:
            result = annotation  # ['result']
            source = 'pro'
            node_pool = [item for item in result if item['type'] == 'rectanglelabels']
            relations = [item for item in result if item['type'] == 'relation']
        # base = annotation['data']['image'].replace('\\', '').replace('/data/local-files/?d=mnt/g',
        #                                                              '/home/johnzhao/文档/科研')[:-3]
        # rects = json.loads(open(base + 'json'))
        # html = bs(open(html))
        app = {item['id'] for item in node_pool}

        root = [item for item in node_pool if 'parentID' not in item or item['parentID'] not in app]
        node_pool = [item for item in node_pool if 'parentID' in item and item['parentID'] in app]
        # if len(root) > 1:
        #     last = [item for item in root if
        #             item['value']['labels'][0] in ['Item', 'Attribute', 'Title', 'Value', 'Description', 'Content']]
        #     root = [item for item in root if
        #             item['value']['labels'][0] not in ['Item', 'Attibute', 'Title',
        #                                                'Value', 'Description', 'Content']]
        # else:
        #     last = []
        assert len(root) == 1
        root = root[0]
        tree = cls((root['original_width'], root['original_height']))
        tree.add_children(parent=None, **_prepare_kwargs(root))
        app = {item['id'] for item in node_pool}

        while len(node_pool) > 0:
            used, ind = set(), []
            for i, item in enumerate(node_pool):
                if item['parentID'] in app:
                    continue
                # try:
                # print([c.tid for c in tree.nodes['aJuE9F6RkB'].children])
                # except:
                # pass
                # print(tree.nodes.keys())
                used.add(item['id'])
                ind.append(i)
                tree.add_children(parent=tree.nodes[item['parentID']], **_prepare_kwargs(item))
            for i in range(len(ind) - 1, -1, -1):
                del node_pool[ind[i]]
            app.difference_update(used)

        # for v in tree.nodes.values():
        # print(v.tid)
        # print([ch.tid for ch in v.children])
        # print(len(last))
        # raise RuntimeError()

        # ! last not processed
        # def get_label_nodes():
        #     labels2item = []
        #     node = tree.root
        #     my_stack = []
        #     while node or my_stack:
        #         if node.label == 'Table':
        #             for child in node.children:
        #                 labels2item.append(child)
        #         if node.children:
        #             for child in node.children[::-1]:
        #                 my_stack.append(child)
        #         if my_stack:
        #             node = my_stack.pop()
        #         else:
        #             node = None
        #     return labels2item

        # labels2item = get_label_nodes()
        # while len(last) > 0:
        #     left, flag = last.pop(), False
        #     x = left['value']['x'] * tree.size[0] / 100
        #     y = left['value']['y'] * tree.size[1] / 100
        #     width = left['value']['width'] * tree.size[0] / 100
        #     height = left['value']['height'] * tree.size[1] / 100
        #     for node in labels2item:
        #         _x = node.rect['x']
        #         _y = node.rect['y']
        #         _width = node.rect['width']
        #         _height = node.rect['height']
        #         if x >= _x and y >= _y and \
        #                 x + width <= _x + _width and y + height <= _y + _height:
        #             flag = True
        #             tree.add_children(tree.nodes[node.id], **_prepare_kwargs(left))
        #     if not flag:
        #         raise ValueError()

        tree.relation = relations
        return tree

    def add_children(self, parent, rect, label, template_id=None, lsid=None, tid=None, meta=''):
        # print(lsid, tid)
        node = Node(lsid=lsid, tid=tid, meta=meta, rect=rect, label=label, template_id=template_id, parent=parent)
        # try:
        #     print(id(self.nodes['aJuE9F6RkB']))
        #     print(id(node))
        # except:
        #     print()
        if parent is None:
            assert self.root is None
            self.root = node
        else:
            parent.children.append(node)
        self.nodes[node.id] = node
        return node

    def delete_node(self, node):
        if node.id == self.root.id:
            self.root = None
            self.nodes = {}
            self.relation = []
            self.parent = None
            return
        for ind, n in enumerate(node.parent.children):
            if n.id == node.id:
                del node.parent.children[ind]
        node.parent.children += node.children
        del self.nodes[node.id]
        return

    def depth(self):
        return max([node.depth for node in self.nodes.values()])

    def add_relation(self, start, end, label):
        self.relation.append(
            {'from_id': start, 'to_id': end, 'type': 'relation', 'direction': 'right', 'labels': label})
        return

    def formulate(self):
        def describe(node):
            description = {"original_width": self.size[0], "original_height": self.size[1], "image_rotation": 0}

            value = {'x': node.rect['x'] * 100 / self.size[0], 'y': node.rect['y'] * 100 / self.size[1],
                     'width': node.rect['width'] * 100 / self.size[0],
                     'height': node.rect['height'] * 100 / self.size[1], 'rotation': 0,
                     'rectanglelabels': node.label if isinstance(node.label, list) else [node.label]}
            description['value'] = value
            description["from_name"] = 'label'
            description["to_name"] = 'image'
            description['type'] = 'rectanglelabels'
            description['tid'] = node.tid
            description['template_id'] = node.template_id
            if node.id:
                description['id'] = node.id
            if node.parent:
                if node.parent.id:
                    description['parentID'] = node.parent.id
            if node.meta:
                description['meta'] = {"text": [node.meta]}
            return description

        node = self.root
        result = []
        my_stack = deque()
        while node or my_stack:
            result.append(describe(node))
            if node.children:
                for child in node.children[::-1]:
                    my_stack.append(child)
            if my_stack:
                node = my_stack.popleft()
            else:
                node = None
        result += self.relation
        return result

    def show_split(self, img_dir=None, h=960, w=540):
        def _add_rect(rect, base, label):
            cv2.rectangle(curr_img, (rect['x'] - base['x'], rect['y'] - base['y']),
                          (rect['x'] - base['x'] + rect['width'], rect['y'] - base['y'] + rect['height']),
                          (0, 0, 255), 5)
            if not isinstance(self.root.label, list):
                label = [label]
            text_size, baseline = cv2.getTextSize(label[0], cv2.FONT_HERSHEY_SIMPLEX, 1, thickness=2)
            for i, text in enumerate(label):
                if text:
                    draw_point = (rect['x'] - base['x'],
                                  rect['y'] - base['y'] + (text_size[1] + 2 + baseline) * (i + 1))
                    cv2.putText(curr_img, text, draw_point, cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 0, 0), thickness=2)

        assert self.img_dir is not None or img_dir is not None
        img = cv2.imread(self.img_dir) if self.img_dir is not None else cv2.imread(img_dir)
        q = deque()
        curr_img = img.copy()
        for k, v in self.root.rect.items():
            self.root.rect[k] = round(v)
        q.append(self.root)
        _add_rect(self.root.rect, {'x': 0, 'y': 0}, self.root.label)
        curr_img, _ = resize_img(curr_img, h, w)
        cv2.imshow('image', curr_img)
        cv2.waitKey(0)
        while q:
            node = q.popleft()
            curr_img = img[node.rect['y']: node.rect['y'] + node.rect['height'],
                           node.rect['x']: node.rect['x'] + node.rect['width']].copy()
            if not node.children:
                continue
            for child in node.children:
                for k, v in child.rect.items():
                    child.rect[k] = round(v)
                q.append(child)
                _add_rect(child.rect, node.rect, child.label)
            curr_img, _ = resize_img(curr_img, h, w)
            cv2.imshow('image', curr_img)
            cv2.waitKey(0)
