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
        # Memory state for rain calculation
        self.last_rain = None

    def genLoopPackets(self):
        while True:
            url = f"https://api.weather.com/v2/pws/observations/current?stationId={self.station_id}&format=json&units=e&numericPrecision=decimal&apiKey={self.api_key}"
            
            try:
                response = requests.get(url)
                if not response.text.strip():
                     log.error("Wunderground API returned an empty response.")
                else:
                    data = response.json()['observations'][0]
                    
                    # Calculate rain delta
                    current_total = float(data['imperial']['precipTotal'])
                    
                    if self.last_rain is None:
                        # First run after restart: set baseline, do not count existing rain
                        self.last_rain = current_total
                        rain_delta = 0.0
                    else:
                        rain_delta = current_total - self.last_rain
                        # Handle midnight reset from Wunderground
                        if rain_delta < 0:
                            rain_delta = current_total
                        
                    self.last_rain = current_total

                    packet = {
                        'dateTime': int(time.time() + 0.5),
                        'usUnits': weewx.US, 
                        'outTemp': data['imperial']['temp'],
                        'outHumidity': data['humidity'],
                        'pressure': data['imperial']['pressure'],
                        'windSpeed': data['imperial']['windSpeed'],
                        'windGust': data['imperial']['windGust'],
                        'windDir': data['winddir'],
                        'dewpoint': data['imperial']['dewpt'],
                        'rain': rain_delta,
                        'rainRate': data['imperial']['precipRate'],
                        'radiation': data.get('solarRadiation'),
                        'UV': data.get('uv'),
                    }
                    
                    # Log all primary metrics in one compact line
                    log.info(
                        f"Fetched data -> T: {packet['outTemp']}F, "
                        f"H: {packet['outHumidity']}%, "
                        f"P: {packet['pressure']}in, "
                        f"W: {packet['windSpeed']}mph (Gust: {packet['windGust']}), "
                        f"R_Delta: {rain_delta}in, "
                        f"R_Total: {current_total}in, "
                        f"UV: {packet['UV']}"
                    )
                    
                    yield packet
                    
            except Exception as e:
                log.error(f"API fetch failed: {e}")

            time.sleep(self.poll_interval)

    @property
    def hardware_name(self):
        return DRIVER_NAME
