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

    def genLoopPackets(self):
        while True:

            url = f"https://api.weather.com/v2/pws/observations/current?stationId={self.station_id}&format=json&units=e&numericPrecision=decimal&apiKey={self.api_key}"
            
            try:
                response = requests.get(url)
                
                if not response.text.strip():
                     log.error("Wunderground API returned an empty response.")
                else:
                    data = response.json()['observations'][0]

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
                        'rain': data['imperial']['precipTotal'],
                        'rainRate': data['imperial']['precipRate'],
                        'radiation': data.get('solarRadiation'),
                        'UV': data.get('uv'),
                    }
                    
                    log.info(f"Successfully fetched US data. Temp: {packet['outTemp']} F, Time: {packet['dateTime']}")
                    
                    yield packet
                    
            except Exception as e:
                log.error(f"API fetch failed: {e}")

            time.sleep(self.poll_interval)

    @property
    def hardware_name(self):
        return DRIVER_NAME
