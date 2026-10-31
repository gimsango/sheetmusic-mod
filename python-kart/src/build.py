#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""공통 코어(src/core/*.py)를 각 프론트엔드에 끼워 넣어 '파일 하나로 실행되는' 단일 .py 를 만든다.

    python3 src/build.py            -> kart3d_phone.py, kart3d_pc.py 생성
    python3 src/build.py core OUT   -> 코어만 OUT 으로 (테스트용)
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MARK = '# @CORE@'


def core_text():
    parts = []
    for p in sorted(glob.glob(os.path.join(HERE, 'core', '*.py'))):
        with open(p, 'r', encoding='utf-8') as f:
            parts.append(f.read().rstrip('\n') + '\n')
    return '\n'.join(parts)


def front_text(front):
    parts = []
    for p in sorted(glob.glob(os.path.join(HERE, front, '*.py'))):
        with open(p, 'r', encoding='utf-8') as f:
            parts.append(f.read().rstrip('\n') + '\n')
    return '\n'.join(parts)


def build(front, out):
    src = front_text(front)
    if MARK not in src:
        raise SystemExit('marker %s not found in %s/' % (MARK, front))
    text = src.replace(MARK, core_text(), 1)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('built %s (%d lines, %d KB)' % (out, text.count('\n'), len(text.encode('utf-8')) // 1024))


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'core':
        with open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as f:
            f.write(core_text())
        print('core ->', sys.argv[2])
    else:
        for front, name in (('phone', 'kart3d_phone.py'), ('pc', 'kart3d_pc.py')):
            if glob.glob(os.path.join(HERE, front, '*.py')):
                build(front, os.path.join(ROOT, name))
