class Model:
    def __init__(self, name: str, maker: str, airpeed: int, cap: int, fuel_hour: int, tank_liters: int, cost: int,
                 desc: str):
        self.name = name
        self.maker = maker
        self.airspeed = airpeed
        self.cap = cap
        self.fph = fuel_hour
        self.tank = tank_liters
        self.cost = cost
        self.desc = desc


countredirs = {
    "中国": "China", "Deutschland": "Germany", "Österreich": "Austria", "UK": "UnitedKingdom", "РФ": "Russia",
    "مصر": "Egypt", "Türkiye": "Turkey", "United States of America": "UnitedStates", "Brasil": "Brazil",
    "México": "Mexico", "الإمارات العربية المتحدة": "UnitedArabEmirates", "日本": "Japan", "Nederland": "Netherlands",
    "대한민국": "SouthKorea", "ประเทศไทย": "Thailand", "España": "Spain", "Maroc": "Morocco", "ኢ.ፌ.ዲ.ሪ.": "Ethiopia",
    "ⵍⵣⵣⴰⵢⴻⵔ الجزائر": "Algeria", "Perú": "Peru", "Italia": "Italy", "Казахстан": "Kazakhstan", "Madagasikara":
    "Madagascar", "RP": "Poland", "Україна": "Ukraine", "საქართველო": "Georgia", "Isle of Man": "UnitedKingdom",
    "Jersey": "UnitedKingdom", "Guernsey": "UnitedKingdom", "Ísland": "Iceland", "Viti": "Fiji",
    "Kalaallit Nunaat": "Greenland", "België / Belgique / Belgien": "Belgium", "Territorial waters of Faroe Islands":
    "Denmark", "Lëtzebuerg": "Luxembourg", "Schweiz/Suisse/Svizzera/Svizra": "Switzerland", "124": "Spain",
    "Portugal (águas territoriais)": "Portugal", "Arquipélago da Madeira (Portugal)": "Portugal", "Česko":
    "Czechia", "Slovensko": "Slovakia", "Magyarország": "Hungary", "Danmark": "Denmark", "Territorial waters of "
    "Bornholm": "Denmark", "Suomi": "Finland", "Sverige": "Sweden", "Norge": "Norway", "Slovenija": "Slovenia",
    "Hrvatska": "Croatia", "BiH / БиХ": "Bosnia", "Србија": "Serbia", "Kosova": "Kosovo", "Бългaрия": "Bulgaria",
    "Shqipëria": "Albania", "Македонија": "Macedonia", "Ελλάδα": "Greece", "România": "Romania", "Беларусь": "Belarus",
    "Lietuva": "Lithuania", "Latvija": "Latvia", "Eesti": "Estonia", "Maroc ⵍⵎⵖⵔⵉⴱ المغرب": "Morocco",
    "USA": "UnitedStates", "Κύπρος - Kıbrıs": "Cyprus", "لبنان": "Lebanon", "سوريا": "Syria", "ישראל": "Israel",
    "الأردن": "Jordan", "臺灣": "Taiwan", "조선민주주의인민공화국": "NorthKorea", "New Zealand/Aotearoa": "NewZealand",
    "Sāmoa": "Samoa", "Kūki 'Āirani": "CookIslands", "M̧ajeļ": "MarshallIslands", "Việt Nam": "Vietnam",
    "ព្រះរាជាណាចក្រ​កម្ពុជា": "Cambodia", "ປະເທດລາວ": "Laos", "မြန်မာ": "Myanmar", "South Africa": "SouthAfrica",
    "France, Polynésie française (eaux territoriales)": "France", "United States of America (Guam)": "UnitedStates",
    "United States of America (Island of Hawai'i territorial waters)": "UnitedStates", "বাংলাদেশ": "Bangladesh",
    "Papua Niugini": "PapuaNewGuinea", "Solomon Islands": "SolomonIslands", "འབྲུག་ཡུལ་": "Bhutan", "नेपाल": "Nepal",
    "‏پاکستان‎": "Pakistan", "افغانستان": "Afghanistan", "Türkmenistan": "Turkmenistan", "Тоҷикистон": "Tajikistan",
    "Кыргызстан": "Kyrgyzstan", "Oʻzbekiston": "Uzbekistan", "Հայաստան": "Armenia", "Azərbaycan": "Azerbaijan",
    "‏ایران‎": "Iran", "العراق": "Iraq", "‏الكويت‎": "Kuwait", "السعودية": "SaudiArabia", "‏البحرين‎": "Bahrain",
    "‏قطر‎": "Qatar", "عمان": "Oman", "اليمن": "Yemen", "ශ්‍රී ලංකාව இலங்கை": "SriLanka", "ދިވެހިރާއްޖެ": "Maldives",
    "Монгол улс": "Mongolia", "تونس": "Tunisia", "السودان": "Sudan", "Sénégal": "Senegal", "Sesel": "Seychelles",
    "Côte d’Ivoire": "IvoryCoast", "Cabo Verde": "CapeVerde", "Cameroun": "Cameroon", "Moçambique": "Mozambique",
    "RD Congo": "DRCongo", "ليبيا": "Libya", "Tchad تشاد": "Chad", "موريتانيا": "Mauritania", "Guinée": "Guinea",
    "Guiné-Bissau": "GuineaBissau", "Sierra Leone": "SierraLeone", "Burkina": "BurkinaFaso", "Bénin": "Benin",
    "Guinea Ecuatorial": "EquatorialGuinea", "South Sudan": "SouthSudan", "ኤርትራ إرتريا": "Eritrea", "Belau": "Palau",
    "Ködörösêse tî Bêafrîka - République Centrafricaine": "CentralAfricanRepublic", "Djibouti جيبوتي": "Djibouti",
    "Soomaaliya الصومال": "Somalia", "Comores Komori جزر القمر": "Comoros", "eSwatini": "Swaziland",
    "São Tomé e Príncipe": "SaoTome", "Saint Helena, Ascension and Tristan da Cunha": "UnitedKingdom",
    "El Salvador": "ElSalvador", "Costa Rica": "CostaRica", "Panamá": "Panama", "R.D.": "DominicanRepublic",
    "The Bahamas": "Bahamas", "Trinidad and Tobago": "TrinidadandTobago", "Ayiti": "Haiti", "Saint Lucia": "StLucia",
    "Cayman Islands": "UnitedKingdom", "Antigua and Barbuda": "AntiguaandBarbuda",
    "United States of America (USVI Saint Croix)": "UnitedStates", "Saint Kitts and Nevis": "StKittsandNevis",
    "Saint Vincent and the Grenadines": "StVincent", "Falkland Islands": "UnitedKingdom",
    "United States of America (Kaua'i, Ni'ihau, Ka'ula)": "UnitedStates", "Crna Gora / Црна Гора": "Montenegro"
}
craft = {  # name, company, airspeed (km / hr), passenger capacity, fuel usage (L / hr), fuel tank (L), cost, desc
    "tyne-347": Model("Tyne-347", "Tyne", 225, 1, 50, 200, 50000,
                      "A small but capable single-prop plane."),
    "tyne-447": Model("Tyne-447", "Tyne", 250, 2, 50, 250, 100000,
                      "A more powerful single-engine sport-utility plane."),
    "tyne-647": Model("Tyne-647", "Tyne", 350, 4, 60, 500, 200000,
                      "A light turboprop plane built for regional transport."),
    "szg-30": Model("SZG-30", "Syzygy", 650, 3, 150, 400, 250000,
                    "A very light jet used for quick, short business flights."),
    "szg-60": Model("SZG-60", "Syzygy", 800, 5, 200, 750, 350000,
                    "A quick, mid-size business twinjet."),
    "szg-80": Model("SZG-80", "Syzygy", 850, 7, 200, 1400, 500000,
                    "A super-mid-size business jet used for longer-distance flights."),
    "dreamwing": Model("Dreamwing", "Zaffre", 900, 25, 500, 8000, 1500000,
                       "A massive long-haul passenger jet."),
    "mercury": Model("Mercury", "Akron", 100, 5, 40, 2000, 75000,
                     "A blimp! Slow, but reliable."),
    "peregrine": Model("Peregrine", "Whitelock", 3500, 4, 1000, 1600, 2000000,
                       "A hypersonic reconnaissance jet. Top secret."),
    "herakles": Model("Herakles", "Whitelock", 550, 15, 250, 1500, 1200000,
                      "A large four-engine turboprop often used by the military."),
    "hongzhun": Model("Hongzhun", "Xuan", 300, 3, 60, 600, 125000,
                      "A small twin-engine turboprop with the capacity for mid-range flights."),
    "dao": Model("Dao", "Xuan", 2200, 4, 800, 1500, 1500000,
                 "The Way. A military-grade supersonic jet.")
}
makers = list(set(g.maker for g in craft.values()))
