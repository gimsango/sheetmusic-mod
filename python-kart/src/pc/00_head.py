#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
  TURBO KART 3D  -  컴퓨터 버전 (Python + Panda3D)       [ kart3d_pc.py ]
==========================================================================
  * 맵 1000개 / 카트 100,000종 / WiFi(LAN) 멀티플레이 / GPU 3D (조명·안개·그림자)
  * 파일 하나로 실행:     pip install panda3d       (한 번만)
                          python kart3d_pc.py
  * 폰(Pydroid 3) 버전과 같은 방에서 함께 달릴 수 있습니다.

  [조작]   ↑/W 가속   ↓/S 브레이크   ←→/AD 조향   Space/Shift 드리프트
           R 트랙 복귀   Esc 일시정지   M 소리   F11 전체화면
           게임패드: 왼쪽 스틱 + RT/LT + A(드리프트)
  [멀티]   한 명이 [멀티플레이 > 방 만들기], 나머지는 [방 찾기]/IP 입력
           전용 서버:  python kart3d_pc.py --serve
  [옵션]   --window 1280x720   --fullscreen   --lang en|ko   --port 5555
==========================================================================
"""
import os
import sys
import math
import time
import json
import array
import wave
import tempfile
import subprocess
import random as _random

try:
    from panda3d.core import (loadPrcFileData, Filename, WindowProperties, NodePath, Geom, GeomNode, GeomTriangles, GeomPoints, GeomLines,
                              GeomVertexData, GeomVertexFormat, GeomVertexWriter, Texture, TransparencyAttrib, ColorBlendAttrib,
                              AmbientLight, DirectionalLight, Fog, Vec3, Vec4, Point3, CardMaker, TextNode, LineSegs, AntialiasAttrib,
                              ModifierButtons, ClockObject, InputDevice, DepthOffsetAttrib, OmniBoundingVolume)
    from direct.showbase.ShowBase import ShowBase
    from direct.gui.OnscreenText import OnscreenText
except ImportError:
    print('Panda3D 가 필요합니다 / Panda3D is required.')
    print('    pip install panda3d')
    print('(설치가 어렵다면 kart3d_phone.py 를 PC 에서 실행해도 됩니다: pip install pygame)')
    raise SystemExit(1)

# @CORE@
