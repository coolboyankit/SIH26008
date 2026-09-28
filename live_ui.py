import serial
import time
import json
import os
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button

from algorithm import (
    load_reference,
    prepare_reference,
    analyze_window
)


# ============================================================
# SETTINGS
# ============================================================

SERIAL_PORT = "COM5"
BAUD_RATE = 115200

REFERENCE_FILE = (
    "bandsaw_normal_reference.json"
)

DISPLAY_SECONDS = 5

PROCESS_SECONDS = 1.0

SAMPLE_RATE = 500


# ============================================================
# LOAD REFERENCE
# ============================================================

print("Loading normal reference...")

if not os.path.exists(REFERENCE_FILE):
    print("Reference file not found.")
    print(
        "Create bandsaw_normal_reference.json first."
    )
    raise SystemExit

reference = load_reference(
    REFERENCE_FILE
)

SAMPLE_RATE = int(
    reference.get(
        "sample_rate_hz",
        SAMPLE_RATE
    )
)

# Build model if necessary
if "normal_model" not in reference:

    print(
        "Building normal model..."
    )

    reference = prepare_reference(
        REFERENCE_FILE
    )


# ============================================================
# SERIAL
# ============================================================

print(
    f"Connecting to {SERIAL_PORT}..."
)

ser = serial.Serial(
    SERIAL_PORT,
    BAUD_RATE,
    timeout=0.1
)

time.sleep(2)

print("Arduino connected.")


# ============================================================
# DATA
# ============================================================

live_samples = []

display_samples = []

error_events = []

current_status = "NORMAL"

current_score = 0.0

error_start = None

session_start = time.time()

running = True


# ============================================================
# FIGURE
# ============================================================

fig, ax = plt.subplots(
    figsize=(12, 6)
)

plt.subplots_adjust(
    bottom=0.18
)

line, = ax.plot(
    [],
    []
)

ax.set_ylim(
    450,
    580
)

ax.set_xlim(
    0,
    DISPLAY_SECONDS
)

ax.set_xlabel(
    "Time (seconds)"
)

ax.set_ylabel(
    "Microphone ADC"
)

ax.set_title(
    "Band Saw Acoustic Monitoring"
)


# Status text
status_text = ax.text(
    0.5,
    1.05,
    "NORMAL",
    transform=ax.transAxes,
    ha="center",
    va="center",
    fontsize=22,
    fontweight="bold"
)

score_text = ax.text(
    0.02,
    0.92,
    "Deviation: 0.00",
    transform=ax.transAxes,
    fontsize=12
)


# ============================================================
# STOP BUTTON
# ============================================================

stop_ax = plt.axes(
    [0.40, 0.03, 0.20, 0.07]
)

stop_button = Button(
    stop_ax,
    "STOP & SAVE"
)


# ============================================================
# SAVE SESSION
# ============================================================

def save_session():

    global running

    running = False

    try:
        ser.close()
    except:
        pass

    session_end = time.time()

    duration = (
        session_end - session_start
    )

    filename = (
        "bandsaw_session_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".json"
    )

    session = {

        "project":
            "Band Saw Acoustic Monitoring",

        "session_id":
            datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            ),

        "sample_rate_hz":
            SAMPLE_RATE,

        "duration_seconds":
            duration,

        "total_samples":
            len(live_samples),

        "samples":
            live_samples,

        "error_events":
            error_events
    }

    with open(
        filename,
        "w"
    ) as f:

        json.dump(
            session,
            f,
            indent=4
        )

    print()
    print(
        "================================"
    )
    print(
        "SESSION SAVED"
    )
    print(
        "================================"
    )

    print(
        "File:",
        filename
    )

    print(
        "Samples:",
        len(live_samples)
    )

    print(
        "Duration:",
        round(duration, 2),
        "seconds"
    )

    print(
        "Errors:",
        len(error_events)
    )

    print(
        "Run results_ui.py to review."
    )

    plt.close(fig)


def stop_clicked(event):

    save_session()


stop_button.on_clicked(
    stop_clicked
)


# ============================================================
# LIVE UPDATE
# ============================================================

def update(frame):

    global current_status
    global current_score
    global error_start

    if not running:
        return

    # Read available serial data
    while ser.in_waiting:

        raw = ser.readline()

        try:

            value = int(
                raw.decode(
                    errors="ignore"
                ).strip()
            )

        except:
            continue

        live_samples.append(
            value
        )

        display_samples.append(
            value
        )

    # Limit graph buffer
    max_display = int(
        DISPLAY_SECONDS *
        SAMPLE_RATE
    )

    if len(display_samples) > max_display:

        del display_samples[
            :-max_display
        ]

    # Need enough data for analysis
    analysis_size = int(
        PROCESS_SECONDS *
        SAMPLE_RATE
    )

    if len(live_samples) < analysis_size:
        return

    # Analyze latest window
    window = np.asarray(
        live_samples[
            -analysis_size:
        ],
        dtype=float
    )

    result = analyze_window(
        window,
        SAMPLE_RATE,
        reference
    )

    current_status = result[
        "status"
    ]

    current_score = result[
        "score"
    ]

    # ========================================================
    # ERROR EVENT
    # ========================================================

    current_time = (
        len(live_samples)
        / SAMPLE_RATE
    )

    if current_status == "ERROR":

        if error_start is None:

            error_start = (
                current_time
                - PROCESS_SECONDS
            )

            error_events.append({

                "event_id":
                    len(error_events) + 1,

                "start_time":
                    error_start,

                "end_time":
                    current_time,

                "duration":
                    PROCESS_SECONDS,

                "deviation":
                    current_score,

                "features":
                    result[
                        "features"
                    ],

                "status":
                    "ERROR"
            })

        else:

            error_events[-1][
                "end_time"
            ] = current_time

            error_events[-1][
                "duration"
            ] = (
                current_time
                - error_start
            )

            error_events[-1][
                "deviation"
            ] = max(
                error_events[-1][
                    "deviation"
                ],
                current_score
            )

    else:

        error_start = None

    # ========================================================
    # GRAPH
    # ========================================================

    if len(display_samples) > 0:

        y = np.asarray(
            display_samples
        )

        x = np.arange(
            len(y)
        ) / SAMPLE_RATE

        x = x - x[-1] + DISPLAY_SECONDS

        line.set_data(
            x,
            y
        )

        minimum = np.min(y)
        maximum = np.max(y)

        if maximum - minimum > 5:

            margin = (
                maximum - minimum
            ) * 0.2

            ax.set_ylim(
                minimum - margin,
                maximum + margin
            )

    # ========================================================
    # STATUS
    # ========================================================

    if current_status == "ERROR":

        status_text.set_text(
            "🔴 ERROR"
        )

        status_text.set_color(
            "red"
        )

        fig.patch.set_facecolor(
            "#ffe6e6"
        )

    else:

        status_text.set_text(
            "🟢 NORMAL"
        )

        status_text.set_color(
            "green"
        )

        fig.patch.set_facecolor(
            "white"
        )

    score_text.set_text(
        f"Deviation: "
        f"{current_score:.2f}"
    )


# ============================================================
# START
# ============================================================

ani = FuncAnimation(
    fig,
    update,
    interval=50,
    cache_frame_data=False
)

plt.show()

# If window closed without button
if running:
    save_session()