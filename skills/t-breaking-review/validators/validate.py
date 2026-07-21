#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1]
ALLOW_NA=True
def load(p):return yaml.safe_load(Path(p).read_text())
def errs(o,n):return [f"{'.'.join(map(str,e.path)) or '$'}: {e.message}" for e in Draft202012Validator(json.loads((R/'schemas'/n).read_text())).iter_errors(o)]
def validate(i,o):
 x=errs(i,'input.schema.json')+errs(o,'output.schema.json')
 if x:return x
 for k in ('work_id','lane','phase','track','reviewer_agent','invocation_id'):
  if i[k]!=o[k]:x.append(k+' mismatch')
 cats=[z['category'] for z in o['checks']]
 if sorted(cats)!=sorted(i['required_categories']) or len(cats)!=len(set(cats)):x.append('required categories must be covered exactly once')
 bad=[z for z in o['checks'] if z['status'] in ('FAIL','BLOCKED')]
 if bad and not o['findings']:x.append('failed checks require findings')
 if o['status']=='PASS' and (bad or o['findings']):x.append('PASS cannot contain failed checks or findings')
 if o['status'] in ('CHANGES_REQUIRED','BLOCKED'):
  if not o['findings']:x.append('non-passing status requires findings')
  if o['recommended_route'] is None:x.append('non-passing status requires route')
 if o['status']=='NOT_APPLICABLE':
  if not ALLOW_NA:x.append('NOT_APPLICABLE forbidden for this track')
  if not o['applicability_reason']:x.append('NOT_APPLICABLE requires reason')
  if any(z['status'] not in ('PASS','NOT_APPLICABLE') for z in o['checks']):x.append('invalid N/A check status')
 if o['status'] in ('PASS','NOT_APPLICABLE') and o['recommended_route'] is not None:x.append('passing status must not route')
 return x
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args();x=validate(load(a.input),load(a.output));print('PASS' if not x else '\n'.join(x));return 1 if x else 0
if __name__=='__main__':raise SystemExit(main())
