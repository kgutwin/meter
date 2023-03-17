# IoT Meter

This is code powering a little desktop project to create a "physical
progress bar" or an "ambient information display".

## Physical Device

The device itself consists of a Raspberry Pi Pico W connected to three
LEDs (red, green, and blue) and an analog ammeter. By performing PWM
on the outputs to these devices, they render any arbitrary number
between 0 and 100. The Pico also has an onboard temperature sensor
which is reported as part of the device's state. A WiFi interface
provides the bidirectional upstream link to the cloud.

The device runs MicroPython and libraries sufficient to interact with
the AWS IoT service. The IoT service offers a "device shadow"
functionality that helps the device to track what updates are needed
locally to reflect the desired state of the device.

## The `meter` Python package

The data feed to the meter is powered by the `meter` Python package in
this repository. It runs as a terminal app on the user's desktop, and
computes the desired state of the meter based on the selected source
of info. Any potential numerical source that can be retrieved
automatically and mapped to a 0-100 scale is suitable as an
information source. The sources will evolve as the meter is used, but
currently include:

* `InsideTemp`: The temperature from the Pico's onboard temperature sensor
* `OutsideTemp`: Current weather conditions from Open-Meteo.com
* `OctoPrint`: 3D Printer completion progress
* `SfnMapRun`: AWS Step Functions Map Run progress
* `CloudWatchAlarm`: Status of an AWS CloudWatch alarm
* `CloudWatchLogs`: Retrieve a numerical value from CloudWatch Logs
* `Pomodoro`: A simple Pomodoro timer for scheduling work and break periods
* `Meetings`: Progress bar through your meetings
* `Traeger`: Temperature probe data from Traeger WiFire grills

