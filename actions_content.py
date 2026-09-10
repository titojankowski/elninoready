# Content for /actions/ (rendered by build_events.py). Edit this file, rebuild, commit.
#
# Every action names the lever it pulls (VISION.md): WARNINGS reach people,
# MONEY moves early, SYSTEMS hold. Every action links to a source someone can
# act on. No numeric claims live here; those stay on the home page with cites.

INTRO_TITLE = "You can see this one <em>coming</em>."
INTRO = ("The forecast is in. What kills people in an El Niño is the gap between the forecast and the action: "
         "the warning that never arrived, the money that came after, the plan that stayed in the drawer. "
         "Here is what to do with the forecast, at whatever scale you can reach.")

LEVERS = {
    "warnings": "Warnings reach people",
    "money": "Money moves early",
    "systems": "Systems hold",
}

TIERS = [
    {
        "id": "family",
        "eyebrow": "/// SCALE 1",
        "title": "For your family",
        "lede": "Things one household can finish this month. Most take an hour.",
        "actions": [
            {
                "title": "Learn what this El Niño means where you live.",
                "body": "El Niño shifts rain and heat differently in every region: drought here, floods there, a hotter summer almost everywhere. Read the plain-language forecast for your part of the world before deciding what to prepare for.",
                "lever": "warnings",
                "links": [("NOAA ENSO blog", "https://www.climate.gov/news-features/blogs/enso"),
                          ("IRI seasonal forecast", "https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/"),
                          ("WMO El Niño update", "https://wmo.int/news/media-centre/el-nino-set-become-very-strong-raising-risks-of-extreme-weather-2027")],
            },
            {
                "title": "Get warnings onto every phone in the house.",
                "body": "Turn on emergency alerts, sign up for your city or county's alert system, and follow your national weather service. A warning that reaches one person in a household reaches the household.",
                "lever": "warnings",
                "links": [("Ready.gov: alerts and warnings", "https://www.ready.gov/alerts")],
            },
            {
                "title": "Make a heat plan before the first heat wave.",
                "body": "Decide now who in your family is most at risk (babies, elders, anyone with a heart or kidney condition, anyone working outdoors), where each of them will cool off when power or air conditioning fails, and who checks on whom. Learn to read the daily HeatRisk forecast.",
                "lever": "systems",
                "links": [("NWS heat safety", "https://www.weather.gov/safety/heat"),
                          ("HeatRisk forecast (US)", "https://www.wpc.ncep.noaa.gov/heatrisk/"),
                          ("WHO: heat and health", "https://www.who.int/news-room/fact-sheets/detail/climate-change-heat-and-health")],
            },
            {
                "title": "If you live near fire or peat country, plan for smoke.",
                "body": "Pick one room you can seal and filter, buy the masks now, and know where to check the air quality index. Smoke travels hundreds of miles and kills quietly, weeks after the fire.",
                "lever": "systems",
                "links": [("EPA: wildfire smoke indoors", "https://www.epa.gov/indoor-air-quality-iaq/wildfires-and-indoor-air-quality-iaq"),
                          ("AirNow air quality", "https://www.airnow.gov/"),
                          ("Ready.gov: wildfires", "https://www.ready.gov/wildfires")],
            },
            {
                "title": "Cover three days without power or tap water.",
                "body": "Heat waves and storms take the grid down when demand peaks. Water, a way to keep food and medicine cold, a charged battery, and a plan for anyone on home medical equipment.",
                "lever": "systems",
                "links": [("Ready.gov: build a kit", "https://www.ready.gov/kit"),
                          ("Ready.gov: power outages", "https://www.ready.gov/power-outages")],
            },
            {
                "title": "Know your water risk, both directions.",
                "body": "Some regions get flooding, some get drought, some get one then the other. Learn which yours is, know your evacuation route if it's floods, and start using less water now if it's drought.",
                "lever": "systems",
                "links": [("Ready.gov: floods", "https://www.ready.gov/floods"),
                          ("Ready.gov: drought", "https://www.ready.gov/drought")],
            },
            {
                "title": "Where mosquitoes carry disease, get ahead of them.",
                "body": "Dengue, malaria, and cholera have followed the shifted rains of every major El Niño. Empty standing water weekly, sleep under nets where malaria is present, and know the early symptoms so nobody waits too long to get treated.",
                "lever": "warnings",
                "links": [("WHO: dengue", "https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue"),
                          ("WHO: malaria", "https://www.who.int/news-room/fact-sheets/detail/malaria")],
            },
            {
                "title": "Tell five people. In their language.",
                "body": "The cheapest warning system on Earth is a group chat. Send the forecast to family in affected regions, to the people who work outside, to whoever looks after someone frail. Attach one thing they can do.",
                "lever": "warnings",
                "links": [("The forecast, in one page", "/")],
            },
        ],
    },
    {
        "id": "community",
        "eyebrow": "/// SCALE 2",
        "title": "For your community",
        "lede": "A congregation, a school, a block, a workplace, a run club. Anywhere people already gather.",
        "actions": [
            {
                "title": "Put El Niño on the agenda of something that already meets.",
                "body": "You don't need a new event. Take two minutes at the start of the meeting, service, practice, or all-hands: the forecast, what it means here, one thing to do. This is the whole idea behind El Niño Climate Week.",
                "lever": "warnings",
                "links": [("Events at Climate Week", "/events/"), ("Add yours", "/#ideas")],
            },
            {
                "title": "List who is most at risk, and who checks on them.",
                "body": "Elders living alone, people on oxygen or dialysis, outdoor workers, families without cooling, people without housing. Heat kills the people nobody checks on. Pair every name with a person who will call or knock.",
                "lever": "systems",
                "links": [("Global Heat Health Information Network", "https://ghhin.org/"),
                          ("WHO: heatwaves", "https://www.who.int/health-topics/heatwaves")],
            },
            {
                "title": "Find or open a cooling place, and publish its hours.",
                "body": "A library, a community center, a house of worship with air conditioning. Agree now that it opens on hot days, decide who holds the key, and make sure the people on your list know where it is.",
                "lever": "systems",
                "links": [("NWS heat safety", "https://www.weather.gov/safety/heat")],
            },
            {
                "title": "Translate the warning.",
                "body": "Official alerts arrive in the official language. Your community may not live in it. Get the forecast and the alerts into the languages people actually speak, on the channels they actually use: local radio, messaging groups, the notice board.",
                "lever": "warnings",
                "links": [("Ready.gov: alerts and warnings", "https://www.ready.gov/alerts")],
            },
            {
                "title": "Ask your local emergency manager three questions.",
                "body": "What is the heat plan, what is the flood or drought plan, and what event triggers each one? If the answers are vague, that is the finding. Plans that live in a drawer don't save anyone.",
                "lever": "systems",
                "links": [("Ready.gov: make a plan", "https://www.ready.gov/plan")],
            },
            {
                "title": "Stock the food bank before prices move.",
                "body": "Harvest failures show up in food prices months after the drought. Give to food banks and mutual aid now, while a dollar buys more, and ask them what they will need in the spring.",
                "lever": "money",
                "links": [("FEWS NET food security outlook", "https://fews.net/")],
            },
            {
                "title": "Host an event, or lend a piece of one.",
                "body": "A forecast briefing at your workplace. A readiness workshop at the school. An online session for family abroad. Bring an idea, a room, a speaker, or an audience and we will help assemble the rest.",
                "lever": "warnings",
                "links": [("Send us the idea", "/#ideas")],
            },
        ],
    },
    {
        "id": "region",
        "eyebrow": "/// SCALE 3",
        "title": "For your state, region, or country",
        "lede": "For people who can move budgets, activate plans, or ask the people who can. The window is the months before the peak.",
        "actions": [
            {
                "title": "Move the money before the disaster, not after.",
                "body": "Anticipatory action means releasing funds on the forecast: food, cash transfers, water treatment, and fuel delivered before the shock lands. Fund it, or ask why your government or your donors are not.",
                "lever": "money",
                "links": [("UN OCHA: anticipatory action", "https://www.unocha.org/anticipatory-action"),
                          ("WFP: anticipatory action", "https://www.wfp.org/anticipatory-actions"),
                          ("Start Network", "https://www.startnetwork.org/")],
            },
            {
                "title": "Pre-position supplies where the forecast points.",
                "body": "Seasonal forecasts already name the regions facing drought, flood, or fire. Stage food, water treatment, medical supplies, and fuel there now, while roads are open and prices are normal.",
                "lever": "money",
                "links": [("IRI seasonal forecast", "https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/"),
                          ("NOAA ENSO discussion", "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml")],
            },
            {
                "title": "Activate a heat action plan with named triggers.",
                "body": "A heat plan needs a threshold that switches it on automatically, a list of who does what when it does, and cooling capacity for the people most at risk. Rehearse it before the first heat wave, not during.",
                "lever": "systems",
                "links": [("WHO: heat-health action plans", "https://www.who.int/publications/i/item/9789240010789"),
                          ("Global Heat Health Information Network", "https://ghhin.org/")],
            },
            {
                "title": "Harden the grid for a hotter peak season.",
                "body": "Demand-response agreements signed, backup power confirmed at hospitals, water plants, and cooling centers, and outage plans that protect people on home medical equipment. Heat is when the grid is needed most and fails most.",
                "lever": "systems",
                "links": [("WMO: extreme weather risks into 2027", "https://wmo.int/news/media-centre/el-nino-set-become-very-strong-raising-risks-of-extreme-weather-2027")],
            },
            {
                "title": "Get water contingency plans out of the drawer.",
                "body": "Reservoir operating rules for drought, storage and treatment staged where floods are likely, well and pump contingencies for the towns that lose supply first. Every one of these is cheaper before the season than during it.",
                "lever": "systems",
                "links": [("Ready.gov: drought", "https://www.ready.gov/drought"),
                          ("Ready.gov: floods", "https://www.ready.gov/floods")],
            },
            {
                "title": "Stand up disease surveillance and stock the response.",
                "body": "Dengue, malaria, and cholera follow shifted rains with a lag of weeks to months. Surveillance, vector control, tests, treatment, and vaccine stocks all need to be in place before cases climb.",
                "lever": "systems",
                "links": [("WHO: dengue", "https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue"),
                          ("WHO: malaria", "https://www.who.int/news-room/fact-sheets/detail/malaria"),
                          ("WHO: cholera", "https://www.who.int/news-room/fact-sheets/detail/cholera")],
            },
            {
                "title": "Fund the last mile of the warning.",
                "body": "A forecast that stops at the capital saves nobody in the village. Pay for the radio time, the local-language translation, the community volunteers, and the messaging channels that carry a warning the final kilometer.",
                "lever": "warnings",
                "links": [("Early Warnings for All", "https://earlywarningsforall.org/")],
            },
            {
                "title": "Ask one question of the people you elect.",
                "body": "What is our El Niño plan? Ask it in public, in writing, and again a month later. The answer, or the silence, tells you which of the actions above still needs doing.",
                "lever": "warnings",
                "links": [("Share the forecast", "/")],
            },
        ],
    },
]

OUTRO_TITLE = "Did one of these? Doing one now?"
OUTRO = ("Tell us. We are building the list of what people actually did, so the next person can copy it. "
         "And if you know an action that belongs here and isn't, send that too.")
