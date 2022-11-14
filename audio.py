import math

import pyttsx3
from gtts import gTTS
import soundfile as sf


class GTTS:
    def generate(self, text, filePath):
        try:
            audioFile = gTTS(text=text, lang='en', slow=False)
            audioFile.save(filePath)
            return True
        except:
            return False


class PyTTSX3:
    def generate(self, text, filePath):
        try:
            engine = pyttsx3.init()
            engine.save_to_file(text, filePath)
            engine.runAndWait()
            return True
        except:
            return False


class AudioUtils:
    @staticmethod
    def calculateDuration(audioFilePath: str):
        f = sf.SoundFile(audioFilePath)
        return math.ceil(len(f)/f.samplerate)


class TTS:
    def __init__(self, generator):
        self.generator = generator

    def generate(self, text, filePath):
        return self.generator.generate(text, filePath)
