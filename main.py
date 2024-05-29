import numpy as np
import scipy.io.wavfile as wave
import pygame
import tkinter as tk
from tkinter import filedialog
import os

# Initialize pygame mixer
pygame.mixer.init()


# Function to play sound
def play_sound(file_path):
    sound = pygame.mixer.Sound(file_path)
    sound.play()
    pygame.time.wait(int(sound.get_length() * 1000))


# Function to read and normalize the input signal
def read_and_normalize_wav(inputFile):
    try:
        samplingFreq, inputSignal = wave.read(inputFile)
    except wave.WavFileWarning as e:
        print(f"Warning: {e}")
        return None, None

    # Check if the input signal has multiple channels, and if so, take the first channel
    if len(inputSignal.shape) > 1:
        inputSignal = inputSignal[:, 0]

    # Normalize the input signal
    inputSignal = inputSignal.astype(np.float32) / np.iinfo(inputSignal.dtype).max
    return samplingFreq, inputSignal

# Function to write the output signal to a WAV file
def write_wav(outputFile, samplingFreq, signal):
    wave.write(outputFile, samplingFreq, np.int16(signal * 32767))


# Function to create the reverb effect
def comb_filter(inputSignal, delay, gain_parameter):
    nData = np.size(inputSignal)
    outputSignal = np.zeros(nData)
    for n in np.arange(nData):
        if n < delay:
            outputSignal[n] = inputSignal[n]
        else:
            outputSignal[n] = inputSignal[n] + gain_parameter * outputSignal[n - delay]
    return outputSignal


def calculate_gain_from_reverbTime(reverbTime, combDelays, samplingFreq):
    nDelays = np.size(combDelays)
    combGains = np.zeros(nDelays)
    for ii in np.arange(nDelays):
        combGains[ii] = 10 ** (-3 * combDelays[ii] / (reverbTime * samplingFreq))
    return combGains


def allpass_filters(inputSignal, delay, gain):
    nData = np.size(inputSignal)
    outputSignal = np.zeros(nData)
    for n in np.arange(nData):
        if n < delay:
            outputSignal[n] = inputSignal[n]
        else:
            outputSignal[n] = gain * inputSignal[n] + inputSignal[n - delay] - gain * outputSignal[n - delay]
    return outputSignal


def schroederReverb(inputSignal, mixingParams, combDelays, combGains, allPassDelays, allPassGains):
    nData = np.size(inputSignal)
    tmpSignal = np.zeros(nData)
    ncomp_filter = np.size(combDelays)
    for ii in np.arange(ncomp_filter):
        tmpSignal += mixingParams[ii] * comb_filter(inputSignal, combDelays[ii], combGains[ii])
    nAllPassFilters = np.size(allPassDelays)
    for ii in np.arange(nAllPassFilters):
        tmpSignal = allpass_filters(tmpSignal, allPassDelays[ii], allPassGains[ii])
    return tmpSignal


# Function to apply reverb to the selected file
def apply_reverb():
    error_label.config(text=" ")
    mixingParams = [float(e) for e in mixingParams_entry.get().split(',')]
    CombDelays = [int(e) for e in combDelays_entry.get().split(',')]
    allpassDelays = [int(e) for e in allpassDelays_entry.get().split(',')]
    allPassGains = [float(e) for e in allpassGains_entry.get().split(',')]
    reverbTime = float(reverbTime_entry.get())



    # Check if the number of allpassGains matches the number of allpassDelays
    if len(allPassGains) != len(allpassDelays):
        error_label.config(text="Error: Number of allpassGains must match the number of allpassDelays.")
        return

    # Check if the number of mixingParams matches the number of CombDelays
    if len(mixingParams) != len(CombDelays):
        error_label.config(text="Error: Number of mixingParams must match the number of CombDelays.")
        return

    if not file_path:
        error_label.config(text="Error: Please select a WAV file.")
        return



    samplingFreq, InputSignal = read_and_normalize_wav(file_path)
    CombDelays = np.array(CombDelays)
    allpassDelays = np.array(allpassDelays)
    mixingParams = np.array(mixingParams)
    allPassGains = np.array(allPassGains)

    combFilterGains = calculate_gain_from_reverbTime(reverbTime, CombDelays, samplingFreq)

    ReverbSignal = schroederReverb(InputSignal, mixingParams, CombDelays, combFilterGains, allpassDelays, allPassGains)

    # Check for NaNs or Infs before normalization
    if np.any(np.isnan(ReverbSignal)):
        print("Warning: ReverbSignal contains NaNs.")
    if np.any(np.isinf(ReverbSignal)):
        print("Warning: ReverbSignal contains Infs.")

    max_val = np.max(np.abs(ReverbSignal))
    if max_val == 0:
        print("Warning: Maximum value of ReverbSignal is zero, cannot normalize.")
    else:
        # Normalize the reverb signal to avoid clipping
        ReverbSignal = ReverbSignal / max_val

    # Check again for NaNs or Infs after normalization
    if np.any(np.isnan(ReverbSignal)):
        print("Warning: ReverbSignal contains NaNs after normalization.")
    if np.any(np.isinf(ReverbSignal)):
        print("Warning: ReverbSignal contains Infs after normalization.")

    # Save the reverb signal to a new wav file
    output_dir = os.path.dirname(file_path)
    output_file_name = os.path.basename(file_path).split('.')[0] + "_reverberated.wav"
    outputFile = os.path.join(output_dir, output_file_name)
    write_wav(outputFile, samplingFreq, ReverbSignal)

    play_sound(outputFile)
    print(f"Reverberated file saved as {outputFile}")


# Tkinter GUI
root = tk.Tk()
root.title("WAV File Reverb")
root.geometry("400x500")

# Default values
default_mixingParams = "0.3, 0.25, 0.25, 0.20"
default_combDelays = "1553, 1613, 1493, 1153"
default_allpassDelays = "223, 443"
default_allpassGains = "-0.7, -0.7"
default_reverbTime = "1.2"

# Mixing Params
tk.Label(root, text="Mixing Params (comma separated)").pack()
mixingParams_entry = tk.Entry(root, width=50)
mixingParams_entry.pack()
mixingParams_entry.insert(0, default_mixingParams)

# Comb Delays
tk.Label(root, text="Comb Delays (comma separated)").pack()
combDelays_entry = tk.Entry(root, width=50)
combDelays_entry.pack()
combDelays_entry.insert(0, default_combDelays)

# Allpass Delays
tk.Label(root, text="Allpass Delays (comma separated)").pack()
allpassDelays_entry = tk.Entry(root, width=50)
allpassDelays_entry.pack()
allpassDelays_entry.insert(0,default_allpassDelays)

# Allpass Gains
tk.Label(root, text="Allpass Gains (comma separated)").pack()
allpassGains_entry = tk.Entry(root, width=50)
allpassGains_entry.pack()
allpassGains_entry.insert(0, default_allpassGains)

# Reverb Time
tk.Label(root, text="Reverb Time (seconds)").pack()
reverbTime_entry = tk.Entry(root, width=50)
reverbTime_entry.pack()
reverbTime_entry.insert(0, default_reverbTime)

# Error label
error_label = tk.Label(root, fg="red")
error_label.pack()

# Select file button
def select_file():
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
    if file_path:
        error_label.config(text="")
        apply_reverb_button.config(state=tk.NORMAL)
    else:
        apply_reverb_button.config(state=tk.DISABLED)

btn_select_file = tk.Button(root, text="Select WAV File", command=select_file)
btn_select_file.pack(pady=10)

# Apply reverb button
apply_reverb_button = tk.Button(root, text="Apply Reverb", command=apply_reverb, state=tk.DISABLED)
apply_reverb_button.pack(pady=10)

root.mainloop()

