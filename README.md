# SIH26008 - Acoustic Monitoring Prototype

## Band Saw Based Prototype for Conveyor Belt Damage Monitoring

This project is a prototype developed for SIH26008 – Belt Joint Rupture and Conveyor Belt Damages in Iron Ore Mining Industry.

The main idea of this prototype is to use the sound produced by a running mechanical system and identify changes in its normal sound pattern. For the experimental setup, we used a band saw as the test machine and an analog microphone sensor to collect the sound signal.

The system learns the normal sound pattern from selected normal portions of a recording. During live operation, it compares the incoming sound with the learned pattern and shows whether the current signal is normal or different from the learned pattern.

The purpose of this prototype is to demonstrate the complete process of data collection, normal-pattern learning, live monitoring, anomaly detection and event recording.

## How the Prototype Works

The prototype works in the following steps:

1. **Microphone Sensor**  
   The microphone captures the sound produced by the band saw.

2. **Arduino UNO**  
   The Arduino reads the analog microphone signal.

3. **Serial Data**  
   The Arduino sends the readings to the computer through the serial port.

4. **Python Program**  
   Python receives and processes the incoming acoustic data.

5. **Normal Pattern Reference**  
   Selected normal portions of the recording are used to create the normal reference.

6. **Live Pattern Comparison**  
   During live monitoring, the current acoustic pattern is compared with the normal reference.

7. **Status Detection**
   -  **NORMAL** – the pattern is within the learned normal variation.
   -  **ERROR** – the pattern is sufficiently different from the normal reference.

8. **Error Recording**  
   When an abnormal pattern is detected, the event is saved with its timing and deviation information.

9. **Review Result**  
   After the recording, detected events can be reviewed. The user can mark an event as **NOT AN ERROR** if it is an acceptable pattern.

10. **Pattern Learning**  
    Accepted patterns are saved in the normal reference so that similar patterns can be recognized in future monitoring.

### Overall Flow

**Microphone → Arduino UNO → Python → Feature Extraction → Normal Reference → Pattern Comparison → NORMAL / ERROR → Event Recording → Review → Accepted Pattern Learning**

The microphone continuously captures the sound from the machine. The Arduino reads the analog signal and sends the values to the computer through the serial connection.

Python then processes the incoming data and compares it with the normal reference.

## Hardware Used

- Arduino UNO
- Analog microphone sound sensor module
- Band saw used as the experimental machine
- Computer

### Microphone Connections

Microphone Module       Arduino UNO

VCC                     5V
GND                     GND
AO                      A0
DO                      Not used

The analog output of the microphone is connected to A0 of the Arduino.

## Software Used

The prototype was developed using Python and Arduino.

Python libraries used:

- NumPy
- Matplotlib
- PySerial

Arduino code is written using the Arduino IDE.

# Project Files

## algorithm.py

This file contains the main signal-processing and anomaly-detection part of the project.

It is responsible for:

- Reading the normal reference
- Extracting signal features
- Building the normal model
- Calculating deviation from the normal pattern
- Comparing patterns with previously accepted variations
- Adding a detected pattern to the accepted variations when the user marks it as not an error

The algorithm is kept separate from the user interface so that the detection method can be used with another interface in the future.

## live_ui.py

This is the live monitoring program.

It connects to the Arduino and continuously receives microphone readings.

The program displays the live signal and the current condition.

The main output is:

NORMAL

or

ERROR

When a different pattern is detected, the event is recorded with its timing and deviation information.

The complete live session is also saved after stopping the monitoring.

## results_ui.py

This program is used after the live recording.

It loads the saved session and displays the detected events one by one.

For each detected event, the user can see the signal and information such as:

- Start time
- End time
- Duration
- Deviation

The user can also select:

NOT AN ERROR

if the detected pattern is actually an acceptable pattern.

## sih.ino

This is the Arduino program used to read the analog microphone signal and send the readings through the serial port.

The current prototype uses a sampling rate of approximately 500 samples per second.

## uno.py

This file was used for Arduino and serial communication testing during development and data acquisition.

It can be used to check whether the Arduino is sending data correctly to the computer.

# Dataset

The repository contains the actual data recorded during the prototype experiment.

## bandsaw_normal_reference.json

This file contains the normal portions selected from the recorded data.

Only the portions selected as normal are used to create the normal reference.

The program does not automatically assume that the complete recording is normal.

The file also stores accepted variations that the user has marked as NOT AN ERROR.

## bandsaw_session_20260928_212525.json

This is the recorded live session used with the prototype.

It contains the recorded microphone samples and the information generated during the live monitoring session.

The session data includes the detected events and their calculated values.

The file is kept in JSON format so that the complete session can be loaded again later.

# Normal Pattern Learning

Before live monitoring, the system needs a reference for what normal operation sounds like.

Normal sections are selected from the recording and stored in the normal reference.

The system then extracts information from these normal sections and uses it when checking new incoming data.

This is important because a machine does not produce exactly the same sound at every moment. Small changes can happen even when the machine is operating normally.

Because of this, the system does not use a simple single fixed value to decide whether something is an error.

# Handling Small Changes

One of the important parts of the prototype is that a small change in the sound pattern should not immediately become an error.

For example, if two normal patterns are slightly different, they should still be treated as part of normal operation.

The algorithm therefore compares the extracted characteristics of the signal with the learned normal variation instead of requiring an exact match.

# Different Pattern Durations

A sound change may be very short or may continue for a longer period.

The prototype therefore checks the signal at different time scales.

This allows the system to look for both shorter and longer changes in the acoustic pattern.

# Error Detection

During live monitoring, the latest signal window is analyzed and compared with the normal reference.

If the deviation remains within the learned normal range:

NORMAL

is shown.

If the pattern is sufficiently different:

ERROR

is shown and an event is recorded.

The event contains information about when it happened and how different the detected pattern was from the normal reference.

# Reviewing Detected Errors

After the live recording is finished, the saved session can be opened using results_ui.py.

The detected events are shown separately.

The user can inspect each event and decide whether it is actually an error.

If an event is considered a valid error, it remains recorded as an error.

If the event is an acceptable machine pattern, the user can select:

NOT AN ERROR

# Accepted Pattern Learning

When the user marks an event as NOT AN ERROR, its pattern information is stored in the normal reference file.

The next time a similar pattern appears, the system can compare it with the previously accepted pattern.

The basic flow is:

Detected pattern
       |
       v
User checks pattern
       |
       v
NOT AN ERROR
       |
       v
Pattern saved
       |
       v
Normal reference updated
       |
       v
Similar future pattern
       |
       v
Accepted instead of repeatedly reporting it

This allows the reference to be updated based on actual observations.

# Saving the Data

The live program saves the complete session rather than saving only the detected errors.

This makes it possible to review the recording later and check how the system made its decisions.

The normal reference is stored separately so that it can continue to be used for future monitoring.

# Running the Project

## 1. Connect the hardware

Connect the microphone sensor to the Arduino UNO.

VCC  -> 5V
GND  -> GND
AO   -> A0

## 2. Upload the Arduino program

Open:

sih.ino

using Arduino IDE and upload it to the Arduino UNO.

## 3. Check the COM port

Open live_ui.py.

Find:

SERIAL_PORT = "COM5"

Change COM5 to the COM port used by your Arduino if necessary.

## 4. Start live monitoring

Run:

python live_ui.py

The live monitoring window will open.

The program will show the incoming signal and the current status.

## 5. Review the recorded session

After stopping the live monitoring, run:

python results_ui.py

The saved session will be loaded and the detected events can be reviewed.

# File List

| File | Description |
|------|-------------|
| algorithm.py | Main signal processing and anomaly detection |
| live_ui.py | Live monitoring and recording |
| results_ui.py | Review of detected events |
| sih.ino | Arduino microphone data acquisition |
| uno.py | Arduino/serial testing |
| bandsaw_normal_reference.json | Normal acoustic reference |
| bandsaw_session_20260928_212525.json | Recorded prototype session |

# Prototype Data

The data included in this repository was collected during our own prototype experiment using the band saw setup.

The dataset is provided as recorded experimental data and has not been presented as an industrial mining dataset.

The main purpose of the dataset in this project is to demonstrate the complete working pipeline:

Data Collection
      |
      v
Normal Data Selection
      |
      v
Reference Creation
      |
      v
Live Monitoring
      |
      v
Pattern Comparison
      |
      v
Anomaly Detection
      |
      v
Event Recording
      |
      v
Human Verification
      |
      v
Accepted Pattern Learning

# Prototype

The current prototype focuses on acoustic pattern monitoring.

The files in this repository contain the actual working prototype and experimental data used for this implementation.

# SIH26008

This work is developed as a prototype for the SIH26008 problem statement:

Belt Joint Rupture and Conveyor Belt Damages in Iron Ore Mining Industry: Intelligent Monitoring and Prediction of Conveyor Belt Joint Rupture and Damages in Iron Ore Mining Industry.
