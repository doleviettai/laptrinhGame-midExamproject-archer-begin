import base64
import ctypes
from ctypes import wintypes
import io
import json
from pathlib import Path
import sys
import time

from PIL import ImageGrab

u = ctypes.windll.user32
u.SetProcessDPIAware()
for name in ['GetWindowTextLengthW', 'SetForegroundWindow', 'IsWindowVisible', 'IsIconic']:
    getattr(u, name).argtypes = [wintypes.HWND]
u.GetForegroundWindow.restype = wintypes.HWND
u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
u.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
u.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
cbtype = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
evidence = Path(r'D:\GamePrograms\MidTestExam\Backups\GolemYellow\TestEvidence')
evidence.mkdir(parents=True, exist_ok=True)


def rectangle(hwnd):
    rect = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect


def activate():
    candidates = []

    def cb(hwnd, _):
        n = u.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, title, n + 1)
        if u.IsWindowVisible(hwnd) and title.value.startswith('MidTestExam -') and 'Unity' in title.value:
            candidates.append((hwnd, title.value))
        return True

    u.EnumWindows(cbtype(cb), 0)
    if not candidates:
        raise RuntimeError('Unity project window not found')
    hwnd, title = candidates[0]
    u.ShowWindow(hwnd, 9)
    u.keybd_event(0x12, 0, 0, 0)
    u.keybd_event(0x12, 0, 2, 0)
    u.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    if u.GetForegroundWindow() != hwnd:
        u.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 3)
        r = rectangle(hwnd)
        u.SetCursorPos(r.left + 200, r.top + 12)
        u.mouse_event(2, 0, 0, 0, 0)
        u.mouse_event(4, 0, 0, 0, 0)
        u.SetWindowPos(hwnd, wintypes.HWND(-2), 0, 0, 0, 0, 3)
        time.sleep(0.3)
    print('UNITY_TITLE:' + title, flush=True)
    return hwnd


def key(code, hold=0.05):
    u.keybd_event(code, 0, 0, 0)
    time.sleep(hold)
    u.keybd_event(code, 0, 2, 0)


def chord(codes):
    for code in codes[:-1]:
        u.keybd_event(code, 0, 0, 0)
    key(codes[-1])
    for code in reversed(codes[:-1]):
        u.keybd_event(code, 0, 2, 0)


def text(value):
    for char in value:
        result = u.VkKeyScanW(ord(char))
        if result == -1:
            raise ValueError('Cannot type ' + repr(char))
        code, modifier = result & 255, result >> 8
        if modifier & 1:
            u.keybd_event(0x10, 0, 0, 0)
        key(code, 0.015)
        if modifier & 1:
            u.keybd_event(0x10, 0, 2, 0)


shot_number = 10
print('UNITY_CHECK_READY', flush=True)
for line in sys.stdin:
    try:
        request = json.loads(line)
        if request.get('quit'):
            print('UNITY_CHECK_EXIT', flush=True)
            break
        hwnd = activate()
        for action in request.get('actions', []):
            kind = action['type']
            if kind == 'key':
                key(action['key'], action.get('duration', 0.05))
            elif kind == 'chord':
                chord(action['keys'])
            elif kind == 'text':
                text(action['text'])
            elif kind == 'wait':
                time.sleep(min(action['seconds'], 40))
            elif kind == 'click':
                r = rectangle(hwnd)
                u.SetCursorPos(r.left + int((r.right - r.left) * action['x']), r.top + int((r.bottom - r.top) * action['y']))
                for _ in range(action.get('count', 1)):
                    u.mouse_event(2, 0, 0, 0, 0)
                    u.mouse_event(4, 0, 0, 0, 0)
                    time.sleep(0.07)
            elif kind == 'wheel':
                u.mouse_event(0x0800, 0, 0, action['delta'], 0)
                time.sleep(0.2)
            elif kind == 'capture':
                r = rectangle(hwnd)
                image = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).convert('RGB')
                image.thumbnail((1600, 1100))
                shot_number += 1
                path = evidence / ('yellow_%03d.jpg' % shot_number)
                image.save(path, format='JPEG', quality=80)
                print('IMAGE_PATH:' + str(path), flush=True)
            else:
                raise RuntimeError('Unknown action ' + kind)
        print('UNITY_CHECK_DONE', flush=True)
    except Exception as error:
        print('UNITY_CHECK_ERROR:' + repr(error), flush=True)
