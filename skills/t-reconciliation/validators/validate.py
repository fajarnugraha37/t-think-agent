#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1];SUITE=R.parents[1]
def load(p):return yaml.safe_load(Path(p).read_text())
def errs(o,n):return [e.message for e in Draft202012Validator(json.loads((R/'schemas'/n).read_text())).iter_errors(o)]
def validate(i,o):
 x=errs(i,'input.schema.json')+errs(o,'output.schema.json')
 if x:return x
 req=yaml.safe_load((SUITE/'orchestrator/lane-registry.yaml').read_text())['lanes'][i['lane']]['phase_path'][:-1]
 got=[z['phase'] for z in i['phase_artifacts']];missing=sorted(set(req)-set(got));duplicates=len(got)!=len(set(got))
 unsatisfied=sorted(z['criterion_id'] for z in i['acceptance_criteria'] if z['status']!='SATISFIED')
 if duplicates:x.append('duplicate phase artifact')
 if o['missing_phases']!=missing:x.append('missing_phases mismatch')
 if o['unsatisfied_criteria']!=unsatisfied:x.append('unsatisfied_criteria mismatch')
 blocked=bool(missing or unsatisfied or i['open_blocking_findings'])
 if o['status']=='RECONCILED_COMPLETE':
  if blocked or o['next_state']!='COMPLETED':x.append('completion contract not satisfied')
 elif not blocked:x.append('non-complete output requires an actual blocker')
 return x
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args();x=validate(load(a.input),load(a.output));print('PASS' if not x else '\n'.join(x));return 1 if x else 0
if __name__=='__main__':raise SystemExit(main())
