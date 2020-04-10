import PIL
from PIL import Image, ImageTk
import tkinter as tk
import argparse
import atexit
import subprocess
import threading
import datetime
import cv2
import os

class Application: 
    def __init__(self, output_path = "./"):
        """ Initialize application which uses OpenCV + Tkinter. Create objects to handle video streams, 
        handle caching video, handle switching streams, and handle managing threads"""
        self.vs = cv2.VideoCapture() # capture video frames, 0 is your default video camera
        self.vs.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        #Decrease frame size
        self.vs.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        #cv2.CAP_PROP_FRAME_WIDTH
        self.vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.vs.release()
        self.output_path = output_path  # store output path
        self.current_image = None  # current image from the camera

        self.isReplay = False
        self.initStream = True
        self.cClear = True
        self.killThread = False

        self.fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        self.cache = cv2.VideoWriter()
        self.cache.release()
        self.replayStream = cv2.VideoCapture()
        self.replayStream.release()
        print('[SB Live] Initialied video streams...')

        self.root = tk.Tk()  # initialize root window
        self.root.title("SpikeBall Live")  # set window title
        # self.destructor function gets fired when the window is closed
        self.root.protocol('WM_DELETE_WINDOW', self.destructor)

        self.cam = tk.Frame(self.root)
        self.gui = tk.Frame(self.root)
        self.cam.pack(side='top')
        self.gui.pack(side='bottom', fill='both', expand=True)

        self.panel = tk.Label(self.root)  # initialize image panel
        self.panel.pack(in_=self.cam, padx=10, pady=10)
        print('[SB Live] Initialized GUI...')

        self.serverProcess = subprocess.Popen(['python3', 'sblive/server.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.s = threading.Thread(target=self.get_server_response)
        self.s.start()


        # create a button, that when pressed, will take the current frame and save it to file
        btn = tk.Button(self.root, text="Toggle Replay", command=self.toggle_replay)
        btn.pack(in_=self.gui, side='left', expand=True, padx=10, pady=10)

        btn2 = tk.Button(self.root, text="New Point", command=self.clear_cache)
        btn2.pack(in_=self.gui, side='left', expand=True, padx=10, pady=10)

        self.t = threading.Thread(target=self.video_loop)
        print('[SB Live] Initialized stream thread')

        # start a self.video_loop that constantly pools the video sensor
        # for the most recently read frame
        self.t.start()

    def video_loop(self):
        """ Get frame from the video stream and show it in Tkinter """
        if not self.isReplay:
            if self.initStream:
                print('[SB Live] Starting live video stream...')
                self.replayStream.release()
                self.vs.open(0)
                self.initStream = False
                print('[SB Live] Live video stream started')
            if self.cClear:
                self.cache.release()
                os.remove('sblive/cache/replay.mov')
                self.cache.open('sblive/cache/replay.mov', self.fourcc, 10.0, (1280, 720))
                self.cClear = False
            ok, frame = self.vs.read()  # read frame from video stream
            if ok:  # frame captured without any errors
                key = cv2.waitKey(1)
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA
                self.cache.write(frame)
                self.current_image = Image.fromarray(cv2image)  # convert image for PIL
                imgtk = ImageTk.PhotoImage(image=self.current_image)  # convert image for tkinter
                
                self.panel.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector
                self.panel.config(image=imgtk)  # show the image
        else:
            if self.initStream:
                print('[SB Live] Starting replay video stream...')
                self.cache.release()
                self.vs.release()
                self.replayStream.open('sblive/cache/replay.mov')
                self.initStream = False
                print('[SB Live] Replay video stream started')
            ok, frame = self.replayStream.read()
            if ok:
                key = cv2.waitKey(1)
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA
                self.current_image = Image.fromarray(cv2image)  # convert image for PIL
                imgtk = ImageTk.PhotoImage(image=self.current_image)  # convert image for tkinter
                
                self.panel.imgtk = imgtk  # anchor imgtk so it does not be deleted by garbage-collector
                self.panel.config(image=imgtk)  # show the image
            else:
                self.replayStream.release()
                self.replayStream.open('sblive/cache/replay.mov')
        if not self.killThread:
            self.root.after(30, self.video_loop)  # call the same function after 30 milliseconds

    def toggle_replay(self):
        print('[SB Live] Toggling replay...')
        self.isReplay = not self.isReplay
        self.initStream = True
        self.clear_cache()

    def clear_cache(self):
        print('[SB Live] Clearing cache...')
        self.cClear = True

    def get_server_response(self):
        print(self.serverProcess.stdout.readline().decode('utf-8'))
        self.root.after(30, self.video_loop)

    def destructor(self):
        """ Destroy the root object and release all resources """
        print(" [SB Live] Terminating...\n",
              "[SB Live] View most recent cache in \'cache/replay.mov\'")
        self.killThread = True
        self.t.join()
        self.root.destroy()
        self.vs.release()  # release web camera
        self.cache.release()
        self.replayStream.release()
        cv2.destroyAllWindows()  # it is not mandatory in this application

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", default="./",
    help="path to output directory to store snapshots (default: current folder")
args = vars(ap.parse_args())

def test():
    print("test")
# start the app
print(" --------------------------------\n",
      "-------[[SpikeBall Live]]-------\n",
      "--------------------------------")
print("[SB Live] Welcome! This tool allows you to easilt generate and view instant replay straight from an attached camera")
print("[SB Live] Replay video is automatically cached and deleted after every point")
print("[SB Live] Press \"Toggle Replay\" to toggle showing the most recent replay")
pba = Application(args["output"])
pba.root.mainloop()