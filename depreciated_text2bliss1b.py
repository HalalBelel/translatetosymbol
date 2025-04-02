#Bliss Translator Project by Miheer Patankar
from __future__ import division

import subprocess, sys

try:
    print("Installing required packages...")
    subprocess.check_call(
        [sys.executable, '-m', 'pip', 'install', 'pyaudio', 'six', 'kivy', 'google-cloud-speech', 'setuptools']
    )
    print("Installation complete.")
except subprocess.CalledProcessError as e:
    print("An error occurred while installing packages:", e)

import os
import threading
import pickle
import pyaudio
from six.moves import queue
import time  # Added for simulation timing

from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.app import App
from kivy.graphics.svg import Svg
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.clock import Clock

# Comment out the google.cloud imports since we are simulating output
# from google.cloud import speech
# from google.cloud.speech import enums
# from google.cloud.speech import types

# obtain a authentication from https://cloud.google.com/docs/authentication/getting-started
# place file path to json below (not needed for simulation)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Path/to/json.json"

# Audio recording parameters (not used in simulation but kept for compatibility)
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
Clock.max_iteration = 1000000

#class microphone stream modification remains unchanged (not used in simulation)
class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b''.join(data)

# The response_loop function is kept unchanged for now.
def response_loop(responses):
    if responses:
        try:
            response = next(responses)
            if not response.results:
                return
            result = response.results[0]
            if not result.alternatives:
                return
            transcript = result.alternatives[0].transcript
            if result.is_final:
                return transcript
        except StopIteration:
            return

# Load dictionaries (make sure your pickle files exist and contain proper data)
with open('./dict/comp_dict.pkl', 'rb') as f:
    comp_dict = pickle.load(f)
with open('./dict/def_dict.pkl', 'rb') as f:
    def_dict = pickle.load(f)
with open('./dict/svg_dict.pkl', 'rb') as f:
    svg_dict = pickle.load(f)

file_root = './svg/'

# Kivy builder for svg widget
Builder.load_string("""
<SvgWidget>:
    do_rotation: False
<FloatLayout>:
    canvas.before:
        Color:
            rgb: (1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
""")

# Kivy SVG widget class
class SvgWidget(Scatter):
    def __init__(self, filename, **kwargs):
        super(SvgWidget, self).__init__(**kwargs)
        with self.canvas:
            svg = Svg(filename)
        self.size = svg.width, svg.height

# Main App for Kivy GUI
class SvgApp(App):
    def build(self):
        self.root = FloatLayout()
        self.n = 0
        self.maintree = []      # data structure for main word images
        self.maintreelabel = [] # data structure for main word text
        self.leaftree = dict()  # data structure for composition (sub) images
        self.sayings = []
        self.leaftreelabel = dict()  # data structure for composition (sub) text

        # Start the simulated speech-to-text in a background thread.
        t1 = threading.Thread(target=self.speechtotext)
        t1.start()

        # Check for new words to display every 0.25 seconds.
        Clock.schedule_interval(self.update, 0.25)
        return self.root

    def update(self, *args, **kwargs):
        try:
            word = self.sayings.pop(0)
            self.screenupdate(word)
        except IndexError:
            pass

    # Modified speech-to-text function that simulates hardcoded output.
    def speechtotext(self):
        simulated_phrase = "I drink water"
        words = simulated_phrase.strip().split()
        for word in words:
            print("Simulated speech output:", word)
            self.sayings.append(word)
            time.sleep(1)  # Delay to simulate interval between words

    # Function to update the GUI based on the word.
    def screenupdate(self, word, *args, **kwargs):
        for wid in self.maintree:
            wid.center = (wid.center_x - 700, wid.center_y)
        for wid in self.maintreelabel:
            wid.center = (wid.center_x - 700, wid.center_y)
        for k, v in self.leaftree.items():
            for val in v:
                self.root.remove_widget(val)
            self.leaftree[k].clear()
        for k, v in self.leaftreelabel.items():
            for val in v:
                self.root.remove_widget(val)
            self.leaftreelabel[k].clear()

        if word in svg_dict.keys():
            filename = file_root + svg_dict[word]
            svg = SvgWidget(filename, size_hint=(None, None))
            svg.scale = 1
            svg.center = Window.center
            self.maintree.append(svg)
            self.root.add_widget(self.maintree[-1])
            mname = Label(text=word, color=(0, 0, 0, 1), size_hint=(None, None))
            mname.center = (svg.center_x, svg.center_y - (svg.scale * 328) / 2)
            self.maintreelabel.append(mname)
            self.root.add_widget(self.maintreelabel[-1])
            if word in comp_dict.keys():
                self.leaftree[word] = []
                self.leaftreelabel[word] = []
                leftpos = (self.maintree[-1].center[0] - ((len(comp_dict[word]) - 1) / 2 * 400 * self.maintree[-1].scale),
                           self.maintree[-1].center[1] - (328.00 * 1.75 * svg.scale) / 2)
                n = 0
                for val in comp_dict[word]:
                    if val in svg_dict.keys():
                        svg_path = file_root + svg_dict[val]
                    else:
                        svg_path = './svg/blank.svg'
                    lsvg = SvgWidget(svg_path, size_hint=(None, None))
                    lsvg.scale = self.maintree[-1].scale * .75
                    lsvg.center = (leftpos[0] + n * 400, leftpos[1])
                    lname = Label(text=val, color=(0, 0, 0, 1), size_hint=(None, None))
                    lname.center = (lsvg.center[0], lsvg.center[1] - (lsvg.scale * 328) / 2)
                    self.leaftree[word].append(lsvg)
                    self.leaftreelabel[word].append(lname)
                    self.root.add_widget(lsvg)
                    self.root.add_widget(lname)
                    n += 1
        else:
            mname = Label(text=word, color=(0, 0, 0, 1), size_hint=(None, None))
            mname.center = Window.center
            self.maintree.append(mname)
            self.root.add_widget(mname)

if __name__ == '__main__':
    SvgApp().run()
