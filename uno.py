import serial
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

ser = serial.Serial("COM5", 115200, timeout=0.05)

buffer = deque([0] * 500, maxlen=500)

plt.ion()
fig, ax = plt.subplots()

line, = ax.plot(range(500), buffer)

ax.set_title("Live Microphone Signal")
ax.set_xlabel("Samples")
ax.set_ylabel("ADC")
ax.set_ylim(500, 530)
ax.set_xlim(0, 500)

try:
    while True:

        # Read all currently available data
        while ser.in_waiting:
            data = ser.readline()

            try:
                value = int(data.strip())

                if 0 <= value <= 1023:
                    buffer.append(value)

            except ValueError:
                pass

        # Update graph
        line.set_ydata(buffer)

        fig.canvas.draw_idle()
        fig.canvas.flush_events()

        plt.pause(0.02)

except KeyboardInterrupt:
    print("Stopped")

finally:
    ser.close()
    plt.close()