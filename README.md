# WeeWX Wunderground Pull Driver

A lightweight, standalone driver for [WeeWX](https://weewx.com/) (v5 compatible) that pulls current weather observations directly from the Weather Underground (Wunderground) API.

This driver is ideal if your weather station uploads to Wunderground, but you want to pull that data back locally into WeeWX to generate reports, store local archives, or push the data to smart home systems like Home Assistant via MQTT.

## Features
* **Lightweight:** No heavy dependencies (only requires `requests`).
* **Unit Auto-Conversion:** Fetches data in US/Imperial units and relies on WeeWX's native `StdConvert` to automatically translate the data to your preferred target units (e.g., Metric) defined in your `weewx.conf`.
* **Reliable:** Uses the official `v2/pws/observations/current` endpoint with decimal precision.
* **Smart Home Ready:** Clean loop packets make it perfect for forwarding live data to Home Assistant using the WeeWX MQTT extension.

## Installation

1. Install the required Python `requests` library if you don't have it:

    sudo apt-get install python3-requests

2. Download `wu_pull_driver.py` and place it in your WeeWX user directory:

    sudo wget -O /etc/weewx/bin/user/wu_pull_driver.py https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/weewx-wunderground-pull/main/wu_pull_driver.py

*(Note: Remember to replace YOUR_GITHUB_USERNAME in the URL with your actual GitHub username. Adjust the path if your WeeWX user directory is located elsewhere, e.g., `/home/weewx/bin/user/`)*

## Configuration

Open your `weewx.conf` file and make the following changes:

**1. Change the station type:**
Locate the `[Station]` section and set the `station_type`:

    [Station]
        ...
        station_type = WUPullCustom

**2. Set record generation to software:**
Because this driver generates loop packets based on API polls, WeeWX needs to calculate the archive records itself. Locate the `[StdArchive]` section and change it to `software`:

    [StdArchive]
        ...
        record_generation = software

**3. Add the driver configuration:**
Add this new block at the very bottom of your `weewx.conf`:

    [WUPullCustom]
        station_id = YOUR_STATION_ID
        api_key = YOUR_API_KEY
        poll_interval = 60
        driver = user.wu_pull_driver

**4. Restart WeeWX:**

    sudo systemctl restart weewx

## Troubleshooting
Check the system log to verify data is flowing:

    sudo journalctl -u weewx -f

You should see a success message every 60 seconds (or whatever you set your `poll_interval` to) indicating the raw temperature and timestamp fetched from the API.
