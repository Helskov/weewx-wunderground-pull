import requests
import time
import logging
import weewx.drivers
import weewx

log = logging.getLogger(__name__)
DRIVER_NAME = 'WUPullCustom'

def loader(config_dict, _):
    return WUPullDriver(**config_dict[DRIVER_NAME])

class WUPullDriver(weewx.drivers.AbstractDevice):
    def __init__(self, **stn_dict):
        self.station_id = stn_dict.get('station_id')
        self.api_key = stn_dict.get('api_key')
        self.poll_interval = float(stn_dict.get('poll_interval', 60))

        # Test mode: set 'test_mode = True' in weewx.conf
        self.test_mode = stn_dict.get('test_mode', 'False').lower() == 'true'
        self.last_rain_total = None

        # Memory for delta validation to filter out API spikes
        self.last_valid_temp = None
        self.last_valid_pres = None

        log.info(f"Driver {DRIVER_NAME} loaded. Test mode: {self.test_mode}")

    def genLoopPackets(self):
        while True:
            # Always request metric units from API.
            # The driver will output data strictly in weewx.METRIC format.
            # WeeWX automatically converts this to US units for American users.
            url = (f"https://api.weather.com/v2/pws/observations/current?"
                   f"stationId={self.station_id}&format=json&units=m&"
                   f"numericPrecision=decimal&apiKey={self.api_key}")

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()['observations'][0]
                    m = data['metric']

                    temp_c = float(m['temp'])
                    pres_hpa = float(m['pressure'])

                    # --- DELTA VALIDATION START ---
                    # Filter out impossible temperature jumps (e.g. > 6C in 2 minutes)
                    if self.last_valid_temp is not None:
                        if abs(temp_c - self.last_valid_temp) > 6.0:
                            log.warning(f"Rejected spike: Temp jumped from {self.last_valid_temp}C to {temp_c}C")
                            time.sleep(self.poll_interval)
                            continue

                    # Filter out impossible pressure jumps (e.g. > 10 hPa in 2 minutes)
                    if self.last_valid_pres is not None:
                        if abs(pres_hpa - self.last_valid_pres) > 10.0:
                            log.warning(f"Rejected spike: Pressure jumped from {self.last_valid_pres}hPa to {pres_hpa}hPa")
                            time.sleep(self.poll_interval)
                            continue

                    # Update valid baseline only after passing checks
                    self.last_valid_temp = temp_c
                    self.last_valid_pres = pres_hpa
                    # --- DELTA VALIDATION END ---

                    # Rain logic (WU API returns metric rain in mm)
                    current_total_mm = float(m['precipTotal'])
                    rain_delta_mm = 0.0

                    if self.test_mode:
                        rain_delta_mm = 0.25
                    elif self.last_rain_total is not None:
                        if current_total_mm >= self.last_rain_total:
                            rain_delta_mm = current_total_mm - self.last_rain_total
                        else:
                            # Midnight reset
                            rain_delta_mm = current_total_mm

                    self.last_rain_total = current_total_mm

                    # CRITICAL FIX: weewx.METRIC unit system expects rain in centimeters (cm)
                    # We must divide the WU mm values by 10
                    rain_delta_cm = rain_delta_mm / 10.0
                    day_rain_cm = current_total_mm / 10.0
                    rain_rate_cm = float(m['precipRate']) / 10.0

                    packet = {
                        'dateTime': int(time.time() + 0.5),
                        'usUnits': weewx.METRIC,
                        'outTemp': temp_c,
                        'outHumidity': data['humidity'],
                        'pressure': pres_hpa,
                        'windSpeed': m['windSpeed'],
                        'windGust': m['windGust'],
                        'windDir': data['winddir'],
                        'dewpoint': m['dewpt'],
                        'rain': rain_delta_cm,
                        'dayRain': day_rain_cm,
                        'rainRate': rain_rate_cm,
                        'radiation': data.get('solarRadiation'),
                        'UV': data.get('uv'),
                    }

                    log.info(
                        f"Loop: T={packet['outTemp']}C, P={packet['pressure']}hPa, "
                        f"R_Delta={rain_delta_mm}mm (Sent as {rain_delta_cm}cm)" +
                        (" [TEST MODE]" if self.test_mode else "")
                    )

                    yield packet
                else:
                    log.error(f"API error: {response.status_code}")

            except Exception as e:
                log.error(f"Driver error: {e}")

            time.sleep(self.poll_interval)

    @property
    def hardware_name(self):
        return DRIVER_NAME
