#!/bin/sh
# Pull the event list from the Google Sheet "El Niño events at NYCW" through the
# googled permission proxy (the only Google credential on this Mac), then rebuild
# events/. Run from the repo root. Commit events.csv and events/ together.
#
#   ./fetch_events.sh && open events/index.html
#
# The sheet is read by column HEADER, so columns can be reordered or added in
# the sheet without touching this script. Required headers: Title, Date, URL,
# Start, End. Optional: Location, Host, Why go, Summary, Format, RSVP Type,
# NYCW listed, Spotted by, El Niño role ("About El Niño" = the main list;
# "Two minutes" = a host who promised El Niño two minutes from the main
# microphone; listed separately, never counted as about El Niño).
set -e
cd "$(dirname "$0")"
SHEET_ID="1_F9DN1s0dBg6acL9vrGqQhCcpcutjuVr2jhCIJY7AxE"
pproxy call googled sheet_read id="$SHEET_ID" > .events.json
python3 build_events.py --from-json .events.json
rm -f .events.json
echo "events.csv and events/ rebuilt. Preview: open events/index.html"
