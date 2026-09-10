# El Niño regions for the city picker on /actions/. Rendered into the page by build_events.py.
#
# Each region: what an El Niño season USUALLY brings there (a tendency, never a
# forecast), roughly when, which hazards that implies (used to filter actions),
# and a link to the live outlook so the card can't go stale. Wording rule:
# "usually", "tends to", "more likely". Never "will".
#
# Sources for the tendencies: NOAA Climate.gov ENSO impact maps, IRI ENSO
# teleconnection maps, WMO El Niño updates. Review by a climate scientist
# before the profiles are treated as more than a first draft (see README).

HAZARDS = {
    "heat": "Extreme heat",
    "drought": "Drought and water shortage",
    "flood": "Heavy rain and flooding",
    "smoke": "Fire and smoke",
    "disease": "Mosquito and water-borne disease",
    "food": "Harvest loss and food prices",
    "outage": "Power and water outages",
    "cyclone": "Shifted storm tracks",
}

OUTLOOK_IRI = "https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/"
OUTLOOK_NOAA = "https://www.climate.gov/news-features/blogs/enso"
OUTLOOK_WMO = "https://wmo.int/news/media-centre/el-nino-set-become-very-strong-raising-risks-of-extreme-weather-2027"

REGIONS = {
    "us-southwest": {
        "name": "US Southwest and California",
        "usually": "A wetter, stormier winter. Atmospheric rivers, flooding, landslides, and coastal erosion are more likely from December to March. Snow can come as rain. The bright side is drought relief; the dark side is that the rain arrives all at once.",
        "when": "December to March",
        "hazards": ["flood", "outage"],
        "outlook": OUTLOOK_NOAA,
    },
    "us-southeast": {
        "name": "US Southeast and Gulf Coast",
        "usually": "A wetter, cooler winter with more severe storms, including winter tornado outbreaks along the Gulf. Flooding is more likely from December to March. The Atlantic hurricane season tends to be quieter, but it only takes one.",
        "when": "December to March",
        "hazards": ["flood", "outage"],
        "outlook": OUTLOOK_NOAA,
    },
    "us-north": {
        "name": "Northern United States and Canada",
        "usually": "A warmer, drier winter with a thinner snowpack across the Pacific Northwest, the northern Rockies, the Midwest, and much of Canada. That shows up later as lower rivers and reservoirs and a longer fire season the following summer.",
        "when": "December to March, with water and fire effects the following summer",
        "hazards": ["drought", "smoke"],
        "outlook": OUTLOOK_NOAA,
    },
    "hawaii": {
        "name": "Hawaii",
        "usually": "A drier winter. Drought and wildfire risk rise through the dry season, and the islands tend to see fewer of the winter storms that refill the aquifers.",
        "when": "November to April",
        "hazards": ["drought", "smoke"],
        "outlook": OUTLOOK_NOAA,
    },
    "central-america-caribbean": {
        "name": "Mexico, Central America, and the Caribbean",
        "usually": "Drier and hotter across Central America's Dry Corridor and much of the Caribbean, with failed harvests and rising hunger the usual result. Northern Mexico tends to get a wetter winter. The Atlantic hurricane season tends to be quieter. Dengue tends to spread with the heat.",
        "when": "Drought from the second rainy season onward, roughly August to March",
        "hazards": ["drought", "food", "heat", "disease"],
        "outlook": OUTLOOK_IRI,
    },
    "northern-south-america": {
        "name": "Northern South America and the Amazon",
        "usually": "Drier and hotter. Drought across Colombia, Venezuela, the Guianas, and northern and northeastern Brazil, low rivers in the Amazon, and a worse fire and smoke season. Hydropower-dependent grids come under strain.",
        "when": "Roughly July to March, peaking late in the year",
        "hazards": ["drought", "heat", "smoke", "food", "outage"],
        "outlook": OUTLOOK_IRI,
    },
    "andes-pacific-coast": {
        "name": "Peru, Ecuador, and the Pacific coast of South America",
        "usually": "The original El Niño. Warm coastal water brings heavy rain, flooding, and landslides to the normally dry coast, along with dengue and other outbreaks, while fisheries collapse. The Bolivian and Peruvian highlands tend to run drier.",
        "when": "December to April, sometimes starting earlier",
        "hazards": ["flood", "disease", "food", "outage"],
        "outlook": OUTLOOK_IRI,
    },
    "southern-south-america": {
        "name": "Southern Brazil, Uruguay, Paraguay, Argentina, and Chile",
        "usually": "Wetter. Heavy rain and river flooding are more likely across southern Brazil, Uruguay, Paraguay, and northeastern Argentina, and central Chile tends to get a wetter winter.",
        "when": "Roughly September to March in the east; June to September in central Chile",
        "hazards": ["flood", "outage"],
        "outlook": OUTLOOK_IRI,
    },
    "southern-africa": {
        "name": "Southern Africa",
        "usually": "Drier and hotter through the summer rainy season, with drought, failed maize harvests, and rising food prices across South Africa, Zimbabwe, Mozambique, Zambia, Malawi, Botswana, Namibia, and Madagascar. Hydropower and water supply come under strain.",
        "when": "October to March",
        "hazards": ["drought", "heat", "food", "outage"],
        "outlook": OUTLOOK_IRI,
    },
    "east-africa": {
        "name": "East Africa and the Horn",
        "usually": "Wetter. Heavy short rains bring flooding to Kenya, Tanzania, Somalia, Uganda, and southern Ethiopia, and with the water come cholera, malaria, and Rift Valley fever. Northern Ethiopia's main rains tend to be weaker.",
        "when": "October to December",
        "hazards": ["flood", "disease", "food"],
        "outlook": OUTLOOK_IRI,
    },
    "west-africa-sahel": {
        "name": "West Africa and the Sahel",
        "usually": "A weaker, less reliable signal than elsewhere. The monsoon tends to run drier, which means heat and harvest risk, but the connection varies a lot from one El Niño to the next.",
        "when": "June to September",
        "hazards": ["drought", "heat", "food"],
        "outlook": OUTLOOK_IRI,
    },
    "south-asia": {
        "name": "South Asia",
        "usually": "A weaker, later monsoon across India, Pakistan, Bangladesh, Nepal, and Sri Lanka, with drought, punishing pre-monsoon heat, and lower harvests. Afghanistan and northern Pakistan tend to get a wetter winter and spring, with flood risk.",
        "when": "Heat from March, monsoon June to September",
        "hazards": ["heat", "drought", "food", "outage"],
        "outlook": OUTLOOK_IRI,
    },
    "maritime-southeast-asia": {
        "name": "Indonesia, Malaysia, the Philippines, and Papua New Guinea",
        "usually": "Drier and hotter, with drought, water shortages, and a severe peat-fire and haze season. Smoke can blanket cities for weeks. Harvests fall, and dengue tends to rise with the heat.",
        "when": "July to November, sometimes later",
        "hazards": ["drought", "smoke", "heat", "food", "disease", "outage"],
        "outlook": OUTLOOK_IRI,
    },
    "mainland-southeast-asia": {
        "name": "Thailand, Vietnam, Cambodia, Laos, and Myanmar",
        "usually": "Hotter and drier, with a late or weak monsoon, water shortages, and record heat in the pre-monsoon months. Rice and other harvests come under pressure.",
        "when": "Heat from March, dry monsoon June to October",
        "hazards": ["heat", "drought", "food", "outage"],
        "outlook": OUTLOOK_IRI,
    },
    "east-asia": {
        "name": "China, Japan, Korea, and Taiwan",
        "usually": "A mixed picture. Southern China tends to get a wetter winter and spring and a higher flood risk on the Yangtze the following summer, while northern China runs drier. Japan and Korea tend toward a milder winter and a wetter early summer.",
        "when": "Winter through the following summer",
        "hazards": ["flood", "drought"],
        "outlook": OUTLOOK_IRI,
    },
    "australia-nz": {
        "name": "Australia and New Zealand",
        "usually": "Hotter and drier across eastern and northern Australia, with drought, failed crops, and a dangerous bushfire season. Northern and eastern New Zealand tend to run drier too.",
        "when": "Roughly September to March",
        "hazards": ["drought", "heat", "smoke", "food"],
        "outlook": OUTLOOK_IRI,
    },
    "pacific-islands": {
        "name": "Pacific Islands",
        "usually": "The western Pacific (Papua New Guinea, the Solomons, Vanuatu, Fiji) tends toward drought and water shortages, while the central Pacific (Kiribati, the Marshalls) gets heavy rain. Cyclone tracks shift east, exposing islands that rarely see them.",
        "when": "November to April",
        "hazards": ["drought", "flood", "cyclone"],
        "outlook": OUTLOOK_IRI,
    },
    "weak-signal": {
        "name": "Europe, the Middle East, North Africa, and Central Asia",
        "usually": "El Niño's direct signal here is weak and inconsistent. What matters is the global background: a strong El Niño tends to make the following year the hottest on record everywhere, so heat is the thing to prepare for.",
        "when": "The following summer",
        "hazards": ["heat"],
        "outlook": OUTLOOK_WMO,
    },
}

# ISO-3166 alpha-2 -> region. Countries split by sub-region are handled in SPLITS below.
COUNTRY_REGION = {}
def _map(region, codes):
    for c in codes.split():
        COUNTRY_REGION[c] = region

_map("us-north", "CA GL PM")
_map("central-america-caribbean", "BL MF MX GT HN SV NI CR PA BZ CU DO HT JM PR TT BS BB AG DM GD KN LC VC AW CW SX BQ KY TC VG VI AI MS GP MQ BM")
_map("northern-south-america", "CO VE GY SR GF")
_map("andes-pacific-coast", "PE EC BO")
_map("southern-south-america", "UY PY AR CL FK")
_map("southern-africa", "SH ZA ZW MZ BW NA ZM MW LS SZ MG AO KM MU RE YT")
_map("east-africa", "KE TZ UG SO ET RW BI SS DJ ER SC")
_map("west-africa-sahel", "NG GH CI SN ML BF NE TD CM BJ TG GN SL LR GM GW MR SD CV CF GA GQ CG CD ST")
_map("south-asia", "IN PK BD LK NP BT AF MV")
_map("maritime-southeast-asia", "ID MY PH SG BN TL PG")
_map("mainland-southeast-asia", "TH VN KH LA MM")
_map("east-asia", "CN JP KR TW MN KP HK MO")
_map("australia-nz", "AU NZ NF CC CX")
_map("pacific-islands", "FJ VU SB WS TO KI TV NR FM MH PW NC PF CK NU TK AS GU MP WF")
_map("weak-signal", "GB IE FR DE ES PT IT NL BE LU CH AT DK SE NO FI IS PL CZ SK HU RO BG GR HR SI BA RS ME MK AL XK MD UA BY LT LV EE RU "
                     "TR CY MT GE AM AZ KZ UZ TM KG TJ IR IQ SY LB IL PS JO SA AE QA KW BH OM YE EG LY TN DZ MA EH AD MC SM VA LI GI FO AX SJ IM JE GG")

# US states -> region (GeoNames admin1 for US is the postal abbreviation).
US_STATES = {}
for s in "CA NV AZ NM UT".split():
    US_STATES[s] = "us-southwest"
for s in "TX OK AR LA MS AL GA FL SC NC TN".split():
    US_STATES[s] = "us-southeast"
US_STATES["HI"] = "hawaii"
# Everything else in the US -> us-north (handled as the default in SPLITS).

# Countries whose region depends on where in the country you are.
# Evaluated in the browser: state code first, then a latitude cut.
SPLITS = {
    "US": {"by_admin1": US_STATES, "default": "us-north"},
    "BR": {"by_lat": [(-16.0, "southern-south-america")], "default": "northern-south-america"},   # south of 16°S -> southern
}
