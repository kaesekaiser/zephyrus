import googlemaps
from googlemaps import convert, geocoding
from datetime import datetime
import utilities.keys as keys

weather_url = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lng}&exclude=minutely&APPID={key}"
gmaps = googlemaps.Client(key=keys.google_maps)
days = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"


def fahr(k: float):
    return round(9 / 5 * (k - 273.15) + 32)


def timezone(location: str, timestamp=None, language=None):
    # taken directly from Google's API example on GitHub
    params = {
        "location": convert.latlng(getlatlong(location)),
        "timestamp": convert.time(timestamp or datetime.utcnow())
    }
    if language:
        params["language"] = language
    ret = gmaps._request("/maps/api/timezone/json", params)
    return (ret["rawOffset"] + ret["dstOffset"]) / 3600


def getlatlong(s: str):
    return geocoding.geocode(gmaps, s)[0]["geometry"]["location"]


def getcity(s: str, allow_empty: bool = False):
    gc = geocoding.geocode(gmaps, s)
    try:
        country = [g["long_name"] for g in gc[0]["address_components"] if "country" in g["types"]][0]
    except IndexError:
        if allow_empty:
            return None, None, None
        else:
            raise ValueError("Unable to precisely locate.")
    try:
        state = [g["long_name"] for g in gc[0]["address_components"] if "administrative_area_level_1" in g["types"]][0]
    except IndexError:
        try:
            city = [g["long_name"] for g in gc[0]["address_components"] if "locality" in g["types"]][0]
            return city, None, country
        except IndexError:
            return None, None, country
    try:
        city = [g["long_name"] for g in gc[0]["address_components"] if "locality" in g["types"]][0]
        return city, state, country
    except IndexError:
        return None, state, country


def t_dict(t: datetime):
    return {"day": t.weekday(), "hour": t.hour, "min": t.minute, "sec": round(t.second + round(t.microsecond * 1000000))}


def twodig(n: int):
    return "0" + str(n) if n < 10 else str(n)


def format_dict(d: dict, military: bool = True):
    if not military:
        return f"{(d['hour'] - 1) % 12 + 1}:{twodig(d['min'])} {'am' if d['hour'] < 12 else 'pm'}, {days[d['day']]}"
    return f"{twodig(d['hour'])}:{twodig(d['min'])}, {days[d['day']]}"


def timein(s: str):
    tz = timezone(s)
    tz = {"hour": round(tz // 1), "min": round((tz % 1) * 60)}
    dt = t_dict(datetime.utcnow())
    minute = dt["min"] + tz["min"]
    hour = dt["hour"] + tz["hour"] + (minute // 60)
    day = dt["day"] + hour // 24
    return {"day": day % 7, "hour": hour % 24, "min": minute % 60}
