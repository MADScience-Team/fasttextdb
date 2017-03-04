import argparse
import sys
import random

parser = argparse.ArgumentParser(
    description='downsamples stdin and writes random lines to stdout (always prints the first and last lines)'
)

parser.add_argument(
    '--rate',
    help='sampling rate (float between 0-1, default 0.1)',
    type=float,
    default=0.1)

args = parser.parse_args()

l = sys.stdin.readline()
lastline = l
printed = True
print(l.strip())
l = sys.stdin.readline()

while l:
    lastline = l
    r = random.random()
    printed = r < args.rate

    if printed:
        print(l.strip())

    l = sys.stdin.readline()

if not printed:
    print(lastline.strip())
