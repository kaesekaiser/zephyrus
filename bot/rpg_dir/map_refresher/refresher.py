from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from os import path
from re import split

clientID = "5158616104-scom8jetbg8urosiljelib3i40i0umb8.apps.googleusercontent.com"
clientSecret = "QZN4dNRh_68rdKr8PZXRY8jE"  # idk if I'll ever need these for anything???
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
ID = '1k2AWcq8It5bt6nY2A3R78fIg0r6YPpU7Np4Y_Ww8jQg'
direct = "C:/Users/Kaesekaiser/PycharmProjects/discobot/rpg_dir/"
destination = direct + "maps/{}.txt"


def color(s: str):
    red, green, blue = int(s[:2], 16), int(s[2:4], 16), int(s[4:], 16)
    return {"red": red / 255, "green": green / 255, "blue": blue / 255}


class Main:
    def __init__(self):
        store = file.Storage(direct + 'map_refresher/token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(direct + 'map_refresher/credentials.json', SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('sheets', 'v4', http=creds.authorize(Http()))
        self.spreadsheet = service.spreadsheets()

    def save(self, sheet: str, map_file: str):
        result = self.spreadsheet.values().get(spreadsheetId=ID, range=sheet + "!A:ZZZ").execute()
        values = result.get('values', [])
        if not values:
            raise ValueError("No such sheet found.")
        else:
            if not path.exists(destination.format(map_file)):
                with open(destination.format(map_file), "x"):
                    pass
            with open(destination.format(map_file), "w") as read:
                read.write("\n".join([" ".join([g.ljust(9) for g in row]).strip() for row in values]))

    def create(self, sheet: str, map_file: str=None):
        if sheet in [g["properties"]["title"] for g in self.spreadsheet.get(spreadsheetId=ID).execute()["sheets"]]:
            raise ValueError("A sheet by that name already exists.")
        else:
            if map_file is None:
                rows, columns = 7, 9
            else:
                if not path.exists(destination.format(map_file)):
                    raise ValueError("No such file found.")
                with open(destination.format(map_file), "r") as read:
                    lines = read.read().splitlines()
                    rows = len(lines)
                    columns = len(split(r"\s+", lines[0]))
            body = {  # json bitch
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": sheet,
                                "gridProperties": {
                                    "rowCount": rows,
                                    "columnCount": columns
                                }
                            }
                        }
                    }
                ]
            }
            self.spreadsheet.batchUpdate(spreadsheetId=ID, body=body).execute()

    def load(self, sheet: str, map_file: str):
        if not path.exists(destination.format(map_file)):
            raise ValueError("No such file found.")
        with open(destination.format(map_file), "r") as read:
            lines = read.read().splitlines()
        request = {
            "values": [split(r"\s+", g) for g in lines]
        }
        self.spreadsheet.values().update(spreadsheetId=ID, valueInputOption="RAW",
                                         range=f"{sheet}!A1", body=request).execute()

    def format(self, sheet: str):
        sheet_id = self.spreadsheet.get(spreadsheetId=ID).execute()["sheets"]
        try:
            sheet_id = [g["properties"]["sheetId"] for g in sheet_id if g["properties"]["title"] == sheet][0]
        except IndexError:
            return ValueError("No such sheet found.")
        formats = {
            "wtr": ("6d9eeb", 1),
            "grs": ("62bd20", 1),
            "dfg": ("ffff8b", 0),
            "mtn": ("b45f06", 1),
            "mttk": ("b45f06", 1),
            "mttw": ("b45f06", 1),
            "mtt": ("733120", 1),
            "mte": ("b45f06", 1),
            "shl": ("a7caff", 0),
            "mtg": ("e69138", 0),
            "cav": ("000000", 1),
            "bla": ("000000", 0),
            "hsf": ("E1C230", 0),
            "hsi": ("A46C00", 1),
            "idr": ("A46C00", 1),
            "iex": ("ECFF6B", 0),
            "hwlpu": ("9C7BA4", 1),
            "hwlor": ("CD7320", 1),
            "hdrpu": ("9C7BA4", 1),
            "hdror": ("CD7320", 1),
            "hrr": ("CD0029", 1),
            "hrp": ("AC18FF", 1),
            "hrk": ("FF00A4", 0),
            "hrb": ("415AFF", 1)
        }
        whole = {
            "sheetId": sheet_id,
            "startRowIndex": 0,
            "endRowIndex": 10000,
            "startColumnIndex": 0,
            "endColumnIndex": 10000
        }
        requests = {
            "requests": [
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 10000
                        },
                        "properties": {
                            "pixelSize": 40
                        },
                        "fields": "pixelSize"
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": 0,
                            "endIndex": 10000
                        },
                        "properties": {
                            "pixelSize": 40
                        },
                        "fields": "pixelSize"
                    }
                },
                {
                    "repeatCell": {
                        "range": whole,
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE",
                                "textFormat": {
                                    "fontSize": 8,
                                    "bold": True
                                }
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)"
                    }
                },
                *[
                    {
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [whole],
                                "booleanRule": {
                                    "condition": {
                                        "type": "TEXT_STARTS_WITH",
                                        "values": [{"userEnteredValue": g}],
                                    },
                                    "format": {
                                        "backgroundColor": color(j[0]),
                                        "textFormat": {
                                            "foregroundColor": {
                                                "red": j[1],
                                                "green": j[1],
                                                "blue": j[1]
                                            }
                                        }

                                    }
                                }
                            },
                            "index": list(formats.keys()).index(g)
                        }
                    }
                    for g, j in formats.items()
                ]
            ]
        }
        self.spreadsheet.batchUpdate(spreadsheetId=ID, body=requests).execute()
