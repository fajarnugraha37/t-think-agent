#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1]
def load(p):return yaml.safe_load(Path(p).read_text())
def errs(o,n):return [e.message for e in Draft202012Validator(json.loads((R/'schemas'/n).read_text())).iter_errors(o)]
def validate(i,o):
 x=errs(i,'input.schema.json')+errs(o,'output.schema.json')
 if x:return x
 ids=[z['obligation_id'] for z in i['obligations']];rids=[z['obligation_id'] for z in o['results']]
 if sorted(ids)!=sorted(rids) or len(rids)!=len(set(rids)):x.append('every obligation requires exactly one result')
 by={z['obligation_id']:z for z in i['obligations']}
 for z in o['results']:
  if z['obligation_id'] in by and z['command']!=by[z['obligation_id']]['command']:x.append('command drift')
 bad=[z for z in o['results'] if z['status']!='PASS' or z['exit_code']!=0]
 if o['status']=='READY_FOR_RECONCILIATION':
  if bad or o['next_state']!='RECONCILIATION' or o['required_route'] is not None:x.append('ready verification contains failure')
 elif o['required_route'] is None:x.append('non-ready verification requires route')
 return x
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args();x=validate(load(a.input),load(a.output));print('PASS' if not x else '\n'.join(x));return 1 if x else 0
if __name__=='__main__':raise SystemExit(main())
