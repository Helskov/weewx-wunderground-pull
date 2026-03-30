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

**3. Units and Rain Handling (CRITICAL):**

The driver pulls data in US Customary units (Fahrenheit, Inches, mph) from the API. This is the recommended standard for the WeeWX database to ensure consistency.

WeeWX defaults to calculating the average for unknown data sources. Because this driver calculates and sends rain data as a "delta" (the amount of rain fallen since the last poll), you **must** instruct WeeWX to sum these values together. 

Add the following block to your `weewx.conf` (ensure it is placed in the root of the file, not nested under another section):
```ini
[Accumulator]
    [[rain]]
        extractor = sum
```
Metric Display: To display data in Metric (Celsius, mm, m/s) on your reports or via MQTT, configure your unit_system as follows:

For Home Assistant/MQTT or Reports:
```ini
[[MQTT]]
    unit_system = METRICWX
```

**4. Add the driver configuration:**
Add this block at the very bottom of your `weewx.conf`:
```ini
[WUPullCustom]
    station_id = YOUR_STATION_ID
    api_key = YOUR_API_KEY
    poll_interval = 60
    driver = user.wu_pull_driver
    test_mode = False
```
Note: When enabled, the driver injects a fake 0.01 in rain delta on every single poll. You should see your UI "Rain Today" increase steadily. Remember to set test_mode = False and restart WeeWX when you are done testing!

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

Calculated Values (Wind Chill, Dewpoint, etc.)
If values like Wind Chill or Barometer are missing, ensure StdWXCalculate is enabled in your process_services. For WeeWX v5, use the following path:
```ini
[Engine]
    [[Services]]
        process_services = weewx.engine.StdConvert, weewx.engine.StdCalibrate, weewx.engine.StdQC, weewx.wxservices.StdWXCalculate
```
