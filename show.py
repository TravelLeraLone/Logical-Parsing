import os
import json
import argparse

from tree import Tree

parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', required=True, type=str)
parser.add_argument('--output_dir', required=True, type=str)
parser.add_argument('--target', required=True, type=str, nargs='+', help='list of page ids separate by space')
parser.add_argument('--target_h', type=float, default=960.0)
parser.add_argument('--target_w', type=float, default=540.0)
args = parser.parse_args()

for ids in args.target:
    print(ids)
    for d, _, fs in os.walk(args.output_dir):
        print(d.split('/')[-1])
        for f in fs:
            if ids not in f:
                continue
            tree = Tree.from_ls(json.load(open(os.path.join(d, f))))
            tree.show_split(os.path.join(args.data_dir, f.replace('json', 'jpg')), args.target_h, args.target_w)
