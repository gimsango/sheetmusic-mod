#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
  TURBO KART 3D  -  폰 버전 (Pydroid 3)            [ kart3d_phone.py ]
==========================================================================
  * 맵 1000개 / 카트 100,000종 / WiFi(LAN) 멀티플레이 / 터치 조작
  * 파일 하나로 실행됩니다. Pydroid 3 에서 이 파일을 열고 ▶ 를 누르세요.
  * 필요한 것: pygame  (Pydroid 3 > 메뉴 > Pip > "pygame" 설치)
  * PC 에서도 그대로 실행됩니다:  python kart3d_phone.py   (키보드 조작)

  [멀티플레이]  같은 WiFi 에 연결된 기기끼리 (폰 + 폰, 폰 + PC 가능)
     - 한 명이 [멀티플레이 > 방 만들기] 후 화면에 나온 IP 를 친구에게 알려주기
     - 친구는 [멀티플레이 > 방 찾기] (자동 검색) 또는 IP 직접 입력
     - 전용 서버:  python kart3d_phone.py --serve
  [옵션]  --window 960x540   창 크기 (PC)     --fps   FPS 표시    --lang en|ko
==========================================================================
"""
import os
import sys
import math
import time
import json
import array
import random as _random

try:
    import pygame
except ImportError:
    print('pygame 이 필요합니다 / pygame is required.')
    print('Pydroid 3: Menu > Pip > install "pygame"      PC: pip install pygame')
    raise SystemExit(1)

# @CORE@
