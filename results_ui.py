import json
import os
import glob

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.widgets import Button

from algorithm import (
    load_reference,
    save_reference,
    add_accepted_variation
)


# ============================================================
# FIND SESSION
# ============================================================

files = sorted(
    glob.glob(
        "bandsaw_session_*.json"
    )
)

if not files:

    print(
        "No session files found."
    )

    raise SystemExit


print()
print(
    "Available sessions:"
)

for i, file in enumerate(
    files
):

    print(
        i + 1,
        "-",
        file
    )

choice = input(
    "\nEnter session number: "
)

try:

    choice = int(choice) - 1

    session_file = files[
        choice
    ]

except:

    print(
        "Invalid selection."
    )

    raise SystemExit


# ============================================================
# LOAD
# ============================================================

with open(
    session_file,
    "r"
) as f:

    session = json.load(f)


events = session.get(
    "error_events",
    []
)

if not events:

    print(
        "No errors detected."
    )

    raise SystemExit


reference_file = (
    "bandsaw_normal_reference.json"
)

reference = load_reference(
    reference_file
)


# ============================================================
# REVIEW
# ============================================================

current_event = 0


fig, ax = plt.subplots(
    figsize=(12, 6)
)

plt.subplots_adjust(
    bottom=0.20
)


info_text = fig.text(
    0.5,
    0.95,
    "",
    ha="center",
    fontsize=15,
    fontweight="bold"
)


# Buttons
not_error_ax = plt.axes(
    [0.20, 0.04, 0.20, 0.08]
)

next_ax = plt.axes(
    [0.60, 0.04, 0.20, 0.08]
)


not_error_button = Button(
    not_error_ax,
    "NOT AN ERROR"
)

next_button = Button(
    next_ax,
    "NEXT ERROR"
)


# ============================================================
# SHOW EVENT
# ============================================================

def show_event():

    ax.clear()

    if current_event >= len(events):

        ax.text(
            0.5,
            0.5,
            "REVIEW COMPLETE",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=24,
            fontweight="bold"
        )

        info_text.set_text(
            "All detected events reviewed"
        )

        not_error_button.label.set_text(
            "FINISHED"
        )

        next_button.label.set_text(
            "CLOSE"
        )

        fig.canvas.draw_idle()

        return

    event = events[
        current_event
    ]

    start = float(
        event["start_time"]
    )

    end = float(
        event["end_time"]
    )

    samples = np.asarray(
        session["samples"],
        dtype=float
    )

    fs = float(
        session[
            "sample_rate_hz"
        ]
    )

    start_index = max(
        0,
        int(start * fs)
    )

    end_index = min(
        len(samples),
        int(end * fs)
    )

    signal = samples[
        start_index:end_index
    ]

    if len(signal) == 0:
        return

    x = np.arange(
        len(signal)
    ) / fs

    ax.plot(
        x,
        signal
    )

    ax.set_xlabel(
        "Time inside event (seconds)"
    )

    ax.set_ylabel(
        "Microphone ADC"
    )

    ax.grid(
        True,
        alpha=0.3
    )

    info_text.set_text(
        f"ERROR #{current_event + 1}    "
        f"Start: {start:.2f}s    "
        f"End: {end:.2f}s    "
        f"Duration: {end-start:.2f}s    "
        f"Deviation: {event['deviation']:.2f}"
    )

    fig.canvas.draw_idle()


# ============================================================
# NOT AN ERROR
# ============================================================

def mark_not_error(event):

    global current_event

    if current_event >= len(events):
        return

    detected = events[
        current_event
    ]

    features = detected.get(
        "features",
        []
    )

    if not features:

        print(
            "No feature data available."
        )

        current_event += 1

        show_event()

        return

    duration = (
        detected["end_time"]
        -
        detected["start_time"]
    )

    pattern_id = add_accepted_variation(
        reference,
        features,
        duration,
        tolerance=1.5
    )

    save_reference(
        reference,
        reference_file
    )

    detected[
        "status"
    ] = "NOT_AN_ERROR"

    detected[
        "accepted_pattern"
    ] = pattern_id

    print(
        f"Event {current_event + 1} "
        f"saved as {pattern_id}"
    )

    # Update session
    with open(
        session_file,
        "w"
    ) as f:

        json.dump(
            session,
            f,
            indent=4
        )

    current_event += 1

    show_event()


# ============================================================
# NEXT
# ============================================================

def next_event(event):

    global current_event

    current_event += 1

    show_event()


not_error_button.on_clicked(
    mark_not_error
)

next_button.on_clicked(
    next_event
)


# ============================================================
# START
# ============================================================

show_event()

plt.show()