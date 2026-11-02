# -*- coding: utf-8 -*-
# ============================================================================
#  TURBO KART 3D (Python)  -  공통 코어
#  맵 1000개 / 카트 100,000종 / 아이템 100종 / 아케이드 물리 / AI / WiFi(LAN) 멀티플레이
# ============================================================================
import math
import json
import socket
import threading
import time
import os
import sys
import queue

VERSION = '1.1'
MAP_COUNT = 1000
KART_COUNT = 100000
DEFAULT_PORT = 5555
DISC_PORT = 5556
TAU = math.pi * 2.0
STEP = 1.0 / 60.0          # 물리 고정 시간 간격


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def sign(v):
    return 1.0 if v > 0 else (-1.0 if v < 0 else 0.0)


def wrap_pi(a):
    return (a + math.pi) % TAU - math.pi


def lerp(a, b, t):
    return a + (b - a) * t


def hex_rgb(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def mix_rgb(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def shade_rgb(c, k):
    return (int(clamp(c[0] * k, 0, 255)), int(clamp(c[1] * k, 0, 255)), int(clamp(c[2] * k, 0, 255)))


class Rng(object):
    """mulberry32 - 모든 기기/파이썬 버전에서 동일한 난수열"""
    __slots__ = ('a',)

    def __init__(self, seed):
        self.a = int(seed) & 0xFFFFFFFF

    def __call__(self):
        a = self.a = (self.a + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((a ^ (a >> 15)) * (1 | a)) & 0xFFFFFFFF
        t = (((t + (((t ^ (t >> 7)) * (61 | t)) & 0xFFFFFFFF)) & 0xFFFFFFFF) ^ t) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0


def hash32(n):
    h = int(float(n + 1) * 2654435761.0) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    return h & 0xFFFFFFFF
