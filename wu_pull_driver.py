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

        log.info(f"Driver {DRIVER_NAME} loaded. Test mode: {self.test_mode}")

    def genLoopPackets(self):
        while True:
            url = (f"https://api.weather.com/v2/pws/observations/current?"
                   f"stationId={self.station_id}&format=json&units=e&"
                   f"numericPrecision=decimal&apiKey={self.api_key}")
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()['observations'][0]
                    imperial = data['imperial']
                    
                    current_total = float(imperial['precipTotal'])
                    rain_delta = 0.0
                    
                    if self.test_mode:
                        rain_delta = 0.01  # Force rain for testing
                    elif self.last_rain_total is not None:
                        if current_total >= self.last_rain_total:
                            rain_delta = current_total - self.last_rain_total
                        else:
                            # Midnight reset handler
                            rain_delta = current_total
                    
                    self.last_rain_total = current_total

                    packet = {
                        'dateTime': int(time.time() + 0.5),
                        'usUnits': weewx.US, 
                        'outTemp': imperial['temp'],
                        'outHumidity': data['humidity'],
                        'pressure': imperial['pressure'],
                        'windSpeed': imperial['windSpeed'],
                        'windGust': imperial['windGust'],
                        'windDir': data['winddir'],
                        'dewpoint': imperial['dewpt'],
                        'rain': rain_delta,
                        'rainRate': imperial['precipRate'],
                        'radiation': data.get('solarRadiation'),
                        'UV': data.get('uv'),
                    }
                    
                    # Log all primary metrics
                    log.info(
                        f"Fetched data -> T: {packet['outTemp']}F, "
                        f"H: {packet['outHumidity']}%, "
                        f"P: {packet['pressure']}in, "
                        f"W: {packet['windSpeed']}mph (Gust: {packet['windGust']}), "
                        f"R_Delta: {rain_delta}in, "
                        f"R_Total: {current_total}in, "
                        f"UV: {packet['UV']}" +
                        (" [TEST MODE ACTIVE]" if self.test_mode else "")
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
