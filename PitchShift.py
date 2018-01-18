#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
import pyaudio
# import wave
#import fcntl
#import termios
import time
import sys
import os
# import struct
import numpy as np
from scipy import *

FORMAT = pyaudio.paInt16
CHANNELS = 1        #モノラル
RATE = 44100        #サンプルレート
CHUNK = 2**10       #データ点数
RECORD_SECONDS = 20 #録音する時間の長さ


KEY_CODE_ENTER = 10

class  AudioStream:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            output=True )
        self.frames = []

    def __del__(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def input(self):
        return self.stream.read(CHUNK)

    def output(self, d):
        self.stream.write(d)

    def record(self, d):
        #print("recorded:", d)
        #d = struct.unpack('f', d)
        self.frames.append(d)
        return self.frames

def resampling(frames):
    data = b''.join(frames)
    data = frombuffer(data,dtype = "int16")
    data = changePlaySpeed(data,1)
    data = int16(data).tostring()
    return data

def changePlaySpeed(inp,rate):
    outp = []
    for i in range(int(len(inp) / rate)):
        outp.append(inp[int(i * float(rate))])
    return array(outp)

def speedx(sound_array, factor):
    # multiply the sound's speed by some factor
    indices = np.round(np.arange(0, len(sound_array), factor))
    indices = indices[indices < len(sound_array)].astype(int)
    return sound_array[indices.astype(int)]

def stretch(sound_array, f, window_size, h):
    # stretch the sound by a factor f
    phase = np.zeros(window_size)
    hanning_window = np.hanning(window_size)
    result = np.zeros(int(len(sound_array)//f) + window_size).astype("complex128")

    for i in np.arange(0, len(sound_array) - window_size - h, h*f):
        #two potentially overlapping subarrays
        i1 = int(i)
        a1 = np.nan_to_num(sound_array[i1:i1+window_size])
        a2 = np.nan_to_num(sound_array[i1+h:i1+window_size+h])

        #resynchronize the second array on the first
        s1 = np.nan_to_num(np.fft.fft(hanning_window * a1)) + 0.0001
        s2 = np.nan_to_num(np.fft.fft(hanning_window * a2)) + 0.0001
        #print(a1, s1, a2, s2)
        phase = (phase + np.angle(s2/s1)) % 2 * np.pi
        a2_rephased = np.fft.ifft(np.abs(s2) * np.exp(1j*phase))

        #add to result
        i2 = int(i/f)
        result[i2:i2 + window_size] += hanning_window * a2_rephased

    result = ((2 ** 12) * result/np.amax(result)) #normalize (16bit)
    #print(hanning_window)

    return result.astype('int16')

def pitchshift(snd_array, n, window_size=2**13, h=2**11):
    # change pitch of a sound by n semitones
    factor = 2 ** (1.0 * n / 12.0)
    stretched = stretch(snd_array, 1.0/factor, window_size, h)
    return speedx(stretched[window_size:], factor)

def realtimeVoiceChanger():
    audioStream = AudioStream()
    startTime = time.clock()
    rec = []
    a = 0
    text = input("Press [ENTER] to start\nPress any other key to stop")
    if text == "":
        while time.clock() - startTime < RECORD_SECONDS:
            inputAudio = audioStream.input()
            rec = audioStream.record(inputAudio)
            if (a == 0): print(np.nan_to_num(np.frombuffer(rec[0])))
            a += 1
        #print(b''.join(rec))
        data = np.nan_to_num(np.frombuffer(b''.join(rec), dtype="int16"))
        print(len(data))
        audioStream.output(data)
        data = pitchshift(data, 1.5)
        print(len(data))
        text = input("Press [ENTER] to listen")
        if text == "":
            print("Outputting...")
            audioStream.output(data)
        audioStream.frames = []

    # while True:
    #     text = raw_input("Press [ENTER] to start\nPress any other key to stop\n")
    #     if (text != "" or ): break
    #     input = audioStream.input()
    #     rec = audioStream.record(input)
    #     data = pitchshift(rec, 1, window_size=50, h=10)
    #     audioStream.output(data)
    #     audioStream.frames = []

    del audioStream

if __name__ == '__main__':
    realtimeVoiceChanger()