# WeeWX Wunderground Pull Driver

A lightweight, standalone driver for [WeeWX](https://weewx.com/) (v5 compatible) that pulls current weather observations directly from the Weather Underground (Wunderground) API.

This driver is ideal if your weather station uploads to Wunderground, but you want to pull that data back locally into WeeWX to generate reports, store local archives, or push the data to smart home systems like Home Assistant via MQTT.

*Personal small project because my weatherstation only reports to wunderground or ProWeatherLive, and i could not intercept Wifi because of HTTPS communication.*

## Installation

1. **Install requirements:**
   Install the required Python `requests` library if you don't have it:
   ```bash
   sudo apt-get install python3-requests
   ```

2. **Download the driver:**
   Place `wu_pull_driver.py` in your WeeWX user directory:
   ```bash
   sudo wget -O /etc/weewx/bin/user/wu_pull_driver.py [https://raw.githubusercontent.com/Helskov/weewx-wunderground-pull/main/wu_pull_driver.py](https://raw.githubusercontent.com/Helskov/weewx-wunderground-pull/main/wu_pull_driver.py)
   ```
   *(Adjust the path if your WeeWX user directory is located elsewhere, e.g., `/home/weewx/bin/user/`)*

## Configuration

Open your `weewx.conf` file and make the following changes:

**1. Change the station type:**
Locate the `[Station]` section and set the `station_type`:
```ini
[Station]
    ...
    station_type = WUPullCustom
```

**2. Set record generation to software:**
Since this driver generates loop packets based on API polls, WeeWX needs to calculate the archive records itself. Locate the `[StdArchive]` section:
```ini
[StdArchive]
    ...
    record_generation = software
```

**3. Configure Rain Handling (CRITICAL):**
Wunderground provides rain as a daily cumulative total. To prevent WeeWX from incorrectly summing these totals every time the driver polls (causing "exploding" rain values), you **must** add an `[Accumulator]` section. This tells WeeWX to calculate only the difference between polls.

Add this block to your `weewx.conf` (check if `[Accumulator]` already exists, otherwise add it to the end of the file):
```ini
[Accumulator]
    [[rain]]
        extractor = sum
        cumulative = True
```

**4. Add the driver configuration:**
Add this block at the very bottom of your `weewx.conf`:
```ini
[WUPullCustom]
    station_id = YOUR_STATION_ID
    api_key = YOUR_API_KEY
    poll_interval = 60
    driver = user.wu_pull_driver
```

**5. Restart WeeWX:**
```bash
sudo systemctl restart weewx
```

## Troubleshooting

### Verify Data Flow
Check the system log to verify data is flowing:
```bash
sudo journalctl -u weewx -f
```
You should see a success message every 60 seconds (or your chosen `poll_interval`).

### Incorrect Rain Values (Unit Mismatch)
If rain values appear multiplied (e.g., 0.13 mm showing up as 3.3 mm), there is a unit mismatch between the API response and WeeWX. You can fix this by adding a correction in the `[StdCalibrate]` section:
```ini
[StdCalibrate]
    [[Corrections]]
        # Corrects inches-to-mm double conversion if necessary
        rain = rain / 25.4 if rain is not None else None
```
