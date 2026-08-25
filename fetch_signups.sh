#!/bin/sh
# Dump all "get-involved" form signups from Netlify to signups.csv
# Usage: ./fetch_signups.sh   (needs netlify CLI logged in)
set -e
SITE_ID="ffda90ae-9e76-43d4-b20f-cf753b626158"
FORM_ID=$(netlify api listSiteForms --data "{\"site_id\":\"$SITE_ID\"}" | python3 -c "import json,sys; print([f['id'] for f in json.load(sys.stdin) if f['name']=='get-involved'][0])")
netlify api listFormSubmissions --data "{\"form_id\":\"$FORM_ID\"}" | python3 -c "
import json, sys, csv
subs = json.load(sys.stdin)
w = csv.writer(sys.stdout)
w.writerow(['created_at', 'name', 'email', 'role', 'message'])
for s in sorted(subs, key=lambda x: x['created_at']):
    d = s.get('data', {})
    w.writerow([s['created_at'], d.get('name',''), d.get('email',''), d.get('role',''), d.get('message','')])
" > signups.csv
echo "$(($(wc -l < signups.csv) - 1)) signups -> signups.csv"
