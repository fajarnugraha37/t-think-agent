#!/usr/bin/env python3
from __future__ import annotations
import argparse,fnmatch,json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1]
def load(p):return yaml.safe_load(Path(p).read_text())
def errs(o,n):return [e.message for e in Draft202012Validator(json.loads((R/'schemas'/n).read_text())).iter_errors(o)]
def allowed(path,patterns):return any(fnmatch.fnmatchcase(path,p) for p in patterns)
def validate(i,o):
 x=errs(i,'input.schema.json')+errs(o,'output.schema.json')
 if x:return x
 if (i['work_id'],i['lane'])!=(o['work_id'],o['lane']):x.append('identity mismatch')
 tids=[z['task_id'] for z in i['tasks']];rids=[z['task_id'] for z in o['task_results']]
 if sorted(tids)!=sorted(rids) or len(rids)!=len(set(rids)):x.append('every task requires exactly one result')
 for t in i['tasks']:
  if any(not allowed(p,i['approved_write_targets']) for p in t['write_targets']):x.append('task target outside authorization: '+t['task_id'])
 for p in o['source_changes']:
  if not allowed(p,i['approved_write_targets']):x.append('unapproved source change: '+p)
 bad=[z for z in o['task_results'] if z['status']!='COMPLETED']
 if o['status']=='READY_FOR_IMPLEMENTATION_REVIEW':
  if bad or o['new_semantic_decision'] or o['next_state']!='IMPLEMENTATION_REVIEW' or o['required_route'] is not None:x.append('ready output violates completion contract')
 elif o['required_route'] is None:x.append('non-ready output requires route')
 return x
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args();x=validate(load(a.input),load(a.output));print('PASS' if not x else '\n'.join(x));return 1 if x else 0
if __name__=='__main__':raise SystemExit(main())
