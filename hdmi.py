import sys
import time
import threading
import multiprocessing
from multiprocessing import Manager, freeze_support

import keyboard

import cv2
from pygrabber.dshow_graph import FilterGraph

import argparse
import sounddevice as sd


class Cam():
    def __init__(self, cam=None, device=""):
        self.cam = cam
        self.device = device

    def set_device(self, device):
        # There is indeed two of the same line. I do not know why it is needed, but it is.
        cap = cv2.VideoCapture(device)
        cap = cv2.VideoCapture(device)

        self.device = device

        # vid = cv2.VideoCapture(device + cv2.CAP_DSHOW)

        cap.set(cv2.CAP_PROP_SATURATION, 150)  # Lowers the saturation coming in, which is truly too high by default
        self.cam = cap

    def set_res(self, res_x=1280, res_y=720):
        self.cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))  # depends on fourcc available camera
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, res_x)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, res_y)
        # vid.set(cv2.CAP_PROP_FPS, 60)

    def set_fps(self, fps):
        print("NOT YET IMPLEMENTED")
        # vid.set(cv2.CAP_PROP_FPS, 60)


def is_focused():
    import win32gui
    import win32process
    import os

    focus_window_pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[1]
    current_process_pid = os.getppid()

    focused = focus_window_pid == current_process_pid

    print(f"\rFocused PID: {focus_window_pid} | Current PID: {current_process_pid}", end="")

    return focused


def clear_cam(camera):
    camera.release()
    cv2.destroyAllWindows()


def grab_devices():
    graph = FilterGraph()

    # print(graph.get_input_devices())  # list of camera device
    try:
        device = graph.get_input_devices().index("USB Video")
    except ValueError as e:
        print(e)

    vid = Cam()
    vid.set_device(device)
    vid.set_res()


    vid.cam.set(cv2.CAP_PROP_SATURATION, 150)
    return vid



def audio():
    print("Starting audio...")

    # print(sd.query_devices())

    def int_or_str(text):
        """Helper function for argument parsing."""
        try:
            return int(text)
        except ValueError:
            return text

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-l', '--list-devices', action='store_true',
        help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        '-i', '--input-device', type=int_or_str,
        help='input device (numeric ID or substring)')
    parser.add_argument(
        '-o', '--output-device', type=int_or_str,
        help='output device (numeric ID or substring)')
    parser.add_argument(
        '-c', '--channels', type=int, default=2,
        help='number of channels')
    parser.add_argument('--dtype', help='audio data type')
    parser.add_argument('--samplerate', type=float, help='sampling rate')
    parser.add_argument('--blocksize', type=int, help='block size')
    parser.add_argument('--latency', type=float, help='latency in seconds')
    args = parser.parse_args(remaining)

    def callback(indata, outdata, frames, time, status):
        if status:
            print(status)
        outdata[:] = indata

    try:
        with sd.Stream(device=(1, args.output_device),
                       samplerate=args.samplerate, blocksize=args.blocksize,
                       dtype=args.dtype, latency=args.latency,
                       channels=args.channels, callback=callback):
            sys.stdin = open(0)
            print("Audio playing!")
            while True:
                s = input()
                print(s)
    except KeyboardInterrupt:
        parser.exit('')
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))


def video(audio):
    print("Starting video...")

    camera = grab_devices()
    camera_loaded = camera.cam.isOpened()

    if not camera_loaded:
        print("Error opening video stream or file")
        quit(0)

    print("Video playing!")
    # While we definitely totally 100% have a camera feed
    while camera_loaded:
        ret, frame = camera.cam.read()

        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # # contrast = 1
        # # brightness = 100
        # # frame[:, :, 2] = 20
        # # print(frame[:, :, 1])
        # frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)

        # cv2.normalize(frame, frame, 0, 255, cv2.NORM_MINMAX)

        cv2.namedWindow(f"Bane's HDMI + Audio Display", cv2.WINDOW_FULLSCREEN)
        # cv2.resizeWindow(f"Bane's HDMI + Audio Display", 1920, 1080)
        cv2.imshow(f"Bane's HDMI + Audio Display", frame)

        if keyboard.is_pressed('1'):
            # clear_cam(camera.cam)
            print("Changing resolution of camera...")
            camera.set_device(camera.device)
            camera.set_res(1280, 720)

        if keyboard.is_pressed('2'):
            # clear_cam(camera.cam)
            print("Changing resolution of camera...")
            camera.set_device(camera.device)
            camera.set_res(1920, 1080)

        # If Esc is pressed, break the loop
        if cv2.waitKey(1) & 0xFF == 27:
            audio.terminate()
            break

    return camera.cam.read()
    # Clear and release the camera
    clear_cam(camera.cam)


if __name__ == '__main__':
    freeze_support()
    x = multiprocessing.Process(target=audio)
    x.start()

    time.sleep(5)
    video(x)
