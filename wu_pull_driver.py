import requests
import time
import logging
import weewx.drivers

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
                     log.error("Wunderground API returned an empty response. Verify API key and station ID.")
                else:
                    data = response.json()['observations'][0]

                    # Map API data to WeeWX US units
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
                        'rain': data['imperial']['precipRate'],
                        'dayRain': data['imperial']['precipTotal'],
                        'radiation': data.get('solarRadiation'),
                        'UV': data.get('uv'),
                    }
                    
                    # Log success to verify data is flowing
                    log.info(f"Successfully fetched data from Wunderground. Raw Temp (F): {packet['outTemp']}, Time: {packet['dateTime']}")
                    
                    yield packet
                    
            except Exception as e:
                # Log error if API call fails
                log.error(f"API fetch failed: {e}")
                if 'response' in locals() and hasattr(response, 'text'):
                    log.error(f"Wunderground API response: {response.text}")

            time.sleep(self.poll_interval)

    @property
    def hardware_name(self):
        return DRIVER_NAME
