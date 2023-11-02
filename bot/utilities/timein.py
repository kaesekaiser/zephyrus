import googlemaps
from googlemaps import convert, geocoding
from datetime import datetime
import utilities.keys as keys

weather_url = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lng}&exclude=minutely,hourly&APPID={key}"
gmaps = googlemaps.Client(key=keys.google_maps)
days = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"


def fahr(k: float):
    return round(9 / 5 * (k - 273.15) + 32)


def time_offset(location: str):
    # taken directly from Google's API example on GitHub, with some parts removed
    params = {
        "location": convert.latlng(lat_long(location)),
        "timestamp": convert.time(datetime.utcnow())
    }
    ret = gmaps._request("/maps/api/timezone/json", params)
    return (ret["rawOffset"] + ret["dstOffset"]) / 3600


def lat_long(place: str):
    return geocoding.geocode(gmaps, place)[0]["geometry"]["location"]


def short_placename(place: str):
    def component_with(components: list, component_type: str):
        try:
            return [g["long_name"] for g in components if component_type in g["types"]][0]
        except IndexError:
            return None

    order = [
        "sublocality",  # used rarely. sometimes for things like new york's boroughs, in which there is no 'locality'
        "locality",  # most common. picks up city/town names
        *(f"administrative_area_level_{x}" for x in range(5, 0, -1)),  # upwards from the smallest administrative area
        "country",  # ideally this should only come up rarely
        "establishment"  # named things that don't fit into any of the above, like international bodies of water
    ]
    req = geocoding.geocode(gmaps, place)
    comps = req[0]["address_components"]
    try:
        return list(filter(bool, [component_with(comps, g) for g in order]))[0]
    except IndexError:
        return req[0]["formatted_address"]


def placename(place: str):
    return geocoding.geocode(gmaps, place)[0]["formatted_address"]


def dt_dict(dt: datetime):
    return {
        "day": dt.weekday(),
        "hour": dt.hour,
        "min": dt.minute,
        "sec": round(dt.second + dt.microsecond / 1000000)
    }


def two_digit(n: int):
    return "0" + str(n) if n < 10 else str(n)


def format_time_dict(d: dict, military: bool = True):
    if not military:
        return f"{(d['hour'] - 1) % 12 + 1}:{two_digit(d['min'])} {'am' if d['hour'] < 12 else 'pm'}, {days[d['day']]}"
    return f"{two_digit(d['hour'])}:{two_digit(d['min'])}, {days[d['day']]}"


def time_in(place: str):
    tz = time_offset(place)
    tz = {"hour": round(tz // 1), "min": round((tz % 1) * 60)}
    dt = dt_dict(datetime.utcnow())
    minute = dt["min"] + tz["min"]
    hour = dt["hour"] + tz["hour"] + (minute // 60)
    day = dt["day"] + hour // 24
    return {"day": day % 7, "hour": hour % 24, "min": minute % 60}
