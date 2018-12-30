import googlemaps
from googlemaps import convert, geocoding
from datetime import datetime
import urllib.request as req
weatherURL = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&APPID={}"
weatherKey = "5e9bf4d64a4d29780ac3691e5f7455e5"
gmaps = googlemaps.Client(key="AIzaSyCvK6pyZCWyPNsUIAxkepEWffQl8oxSNXM")
days = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
adjDict = {"Clear": "clear", "Clouds": "cloudy", "Rain": "raining", "Mist": "misting", "Snow": "snowing",
           "Drizzle": "drizzling", "Thunderstorm": "storming", "Haze": "hazy"}


def readurl(url):
    return str(req.urlopen(url).read())


def fahr(k):
    return round(9 / 5 * (k - 273.15) + 32)


class WeatherParser:
    def __init__(self):
        self.weather = {}
        self.locale = ()
        self.printing = ""

    def feed(self, s):
        try:
            self.weather["temp"] = fahr(float(s.split("\"temp\":")[1].split(",")[0]))
        except IndexError:
            self.weather["temp"] = "???"
        try:
            self.weather["time"] = datetime.fromtimestamp(int(s.split("\"dt\":")[1].split(",")[0]))
        except IndexError:
            self.weather["time"] = "???"
        else:
            self.weather["time"] = format_dict(t_dict(self.weather["time"]), False).split(",")[0] + " NYC time"
        try:
            self.weather["phrase"] = s.split("\"main\":\"")[1].split('"')[0]
        except IndexError:
            self.weather["phrase"] = "???"
        else:
            self.weather["phrase"] = adjDict.get(self.weather["phrase"], self.weather["phrase"])


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


def directions(origin, destination,
               mode=None, waypoints=None, alternatives=False, avoid=None,
               language=None, units=None, region=None, departure_time=None,
               arrival_time=None, optimize_waypoints=False, transit_mode=None,
               transit_routing_preference=None, traffic_model=None):
    # also directly from GitHub
    params = {
        "origin": convert.latlng(getlatlong(origin)),
        "destination": convert.latlng(getlatlong(destination))
    }

    if mode:
        if mode not in ["driving", "walking", "bicycling", "transit"]:
            raise ValueError("Invalid travel mode.")
        params["mode"] = mode

    if waypoints:
        waypoints = convert.location_list(waypoints)
        if optimize_waypoints:
            waypoints = "optimize:true|" + waypoints
        params["waypoints"] = waypoints

    if alternatives:
        params["alternatives"] = "true"

    if avoid:
        params["avoid"] = convert.join_list("|", avoid)

    if language:
        params["language"] = language

    if units:
        params["units"] = units

    if region:
        params["region"] = region

    if departure_time:
        params["departure_time"] = convert.time(departure_time)

    if arrival_time:
        params["arrival_time"] = convert.time(arrival_time)

    if departure_time and arrival_time:
        raise ValueError("Should not specify both departure_time and"
                         "arrival_time.")

    if transit_mode:
        params["transit_mode"] = convert.join_list("|", transit_mode)

    if transit_routing_preference:
        params["transit_routing_preference"] = transit_routing_preference

    if traffic_model:
        params["traffic_model"] = traffic_model

    return gmaps._request("/maps/api/directions/json", params).get("routes", [])[0]["legs"][0]


def getlatlong(s):
    return geocoding.geocode(gmaps, s)[0]["geometry"]["location"]


def getcity(s):
    gc = geocoding.geocode(gmaps, s)
    try:
        country = [g["long_name"] for g in gc[0]["address_components"] if "country" in g["types"]][0]
    except IndexError:
        return ["Unable to precisely locate."]
    try:
        state = [g["long_name"] for g in gc[0]["address_components"] if "administrative_area_level_1" in g["types"]][0]
    except IndexError:
        try:
            city = [g["long_name"] for g in gc[0]["address_components"] if "locality" in g["types"]][0]
            return city, country
        except IndexError:
            return [country]
    try:
        city = [g["long_name"] for g in gc[0]["address_components"] if "locality" in g["types"]][0]
        return city, state, country
    except IndexError:
        return state, country


def t_dict(t: datetime):
    return {"day": t.weekday(), "hour": t.hour, "min": t.minute, "sec": round(t.second + round(t.microsecond * 1000000))}


def twodig(n):
    return "0" + str(n) if n < 10 else str(n)


def format_dict(d: dict, military=True):
    if not military:
        return f"{(d['hour'] - 1) % 12 + 1}:{twodig(d['min'])} {'am' if d['hour'] < 12 else 'pm'}, {days[d['day']]}"
    return f"{twodig(d['hour'])}:{twodig(d['min'])}, {days[d['day']]}"


def timein(s):
    tz = timezone(s)
    tz = {"hour": round(tz // 1), "min": round((tz % 1) * 60)}
    dt = t_dict(datetime.utcnow())
    minute = dt["min"] + tz["min"]
    hour = dt["hour"] + tz["hour"] + (minute // 60)
    day = dt["day"] + hour // 24
    return {"day": day % 7, "hour": hour % 24, "min": minute % 60}


def weather(s):
    ll = getlatlong(s)
    ll = [str(round(ll[key], 2)) for key in ll]
    wp = WeatherParser()
    wp.feed(readurl(weatherURL.format(*ll, weatherKey)))
    # print(readurl(weatherURL.format(*ll, weatherKey)))
    wp.locale = getcity(s)
    if wp.weather["temp"] == "???":
        raise ValueError
    return wp


if __name__ == "__main__":
    d = directions("Cape Town", "Vladivostok", units="imperial")
    for i in d:
        if i != "steps":
            print(i)
            print(d[i])
