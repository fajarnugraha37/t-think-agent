#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator,RefResolver
R=Path(__file__).resolve().parents[1]; SUITE=R.parents[1]
STATE='IMPLEMENTATION_BLUEPRINT'; READY='READY_FOR_BLUEPRINT_CRITIQUE'; NEXT='BLUEPRINT_CRITIQUE'
def load(p):return yaml.safe_load(Path(p).read_text())
def schema_errors(o,n):
 s=json.loads((R/'schemas'/n).read_text()); shared=json.loads((SUITE/'schemas/composite-track-result.schema.json').read_text()); resolver=RefResolver.from_schema(s,store={shared['$id']:shared});return [e.message for e in Draft202012Validator(s,resolver=resolver).iter_errors(o)]
def expected(lane):
 p=yaml.safe_load((SUITE/'orchestrator/composite-phase-policy.yaml').read_text());return [x for x in p['phases'][STATE]['tracks'] if lane in x['lanes'] and x['required']]
def validate(i,o):
 x=schema_errors(i,'input.schema.json')+schema_errors(o,'output.schema.json')
 if x:return x
 for k in ('work_id','lane','phase'):
  if i[k]!=o[k]:x.append(k+' mismatch')
 exp=expected(i['lane']); ids=[z['track'] for z in i['tracks']]
 if sorted(ids)!=sorted(z['id'] for z in exp) or len(ids)!=len(set(ids)):x.append('required tracks do not match lane policy')
 inv=[z['invocation_id'] for z in i['tracks']]
 if len(inv)!=len(set(inv)):x.append('each track requires a distinct fresh invocation')
 by={z['track']:z for z in i['tracks']}
 for z in exp:
  r=by.get(z['id'])
  if r and (r['agent']!=z['agent'] or r['skill']!=z['skill']):x.append('track '+z['id']+' agent/skill mismatch')
 if i['tracks']!=o['tracks']:x.append('aggregate track bindings drifted')
 invalid=[z for z in i['tracks'] if z['status'] not in ('COMPLETE','CHANGES_REQUIRED','BLOCKED')]
 if invalid:x.append('track status must be COMPLETE, CHANGES_REQUIRED, or BLOCKED')
 bad=[z for z in i['tracks'] if z['status'] in ('CHANGES_REQUIRED','BLOCKED')]
 if bad:
  if o['aggregate_status']==READY:x.append('failed track cannot produce ready aggregate')
  if sorted(o['blocking_tracks'])!=sorted(z['track'] for z in bad):x.append('blocking_tracks mismatch')
 else:
  if o['aggregate_status']!=READY or o['next_state']!=NEXT or o['blocking_tracks']:x.append('passing tracks must produce ready transition')
 if STATE=='IMPLEMENTATION_REVIEW':
  for z in i['tracks']:
   if z['status']=='NOT_APPLICABLE' and z['track'] not in ('security_review','breaking_review'):x.append('NOT_APPLICABLE forbidden for core reviews')
   if z['status']=='NOT_APPLICABLE' and not z.get('applicability_reason'):x.append('NOT_APPLICABLE requires reason')
 return x
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args();x=validate(load(a.input),load(a.output));print('PASS' if not x else '\n'.join(x));return 1 if x else 0
if __name__=='__main__':raise SystemExit(main())
