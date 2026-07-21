#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parents[1]
FILES={
 'input':'input.schema.json','output':'output.schema.json','option':'solution-option.schema.json',
 'coverage':'coverage-row.schema.json','decision':'decision-record.schema.json','dominance':'dominance-proof.schema.json',
 'element':'upstream-model-element.schema.json','relation':'upstream-model-relation.schema.json',
 'evidence':'upstream-evidence-record.schema.json','critique_output':'upstream-model-critique-output.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in FILES.items()}

class Issue:
 def __init__(self,path:str,message:str): self.path,self.message=path,message
 def __str__(self): return f'{self.path}: {self.message}'

def norm(v:Any)->Any:
 if isinstance(v,(date,datetime)): return v.isoformat()
 if isinstance(v,dict): return {k:norm(x) for k,x in v.items()}
 if isinstance(v,list): return [norm(x) for x in v]
 return v

def load_doc(path:Path)->Any:
 text=path.read_text(encoding='utf-8')
 if path.suffix.lower()=='.json': return json.loads(text)
 return norm(yaml.safe_load(text))

def get_schema(kind:str)->dict:
 return json.loads(SCHEMAS[kind].read_text(encoding='utf-8'))

def structural(obj:Any,kind:str,prefix='$')->list[Issue]:
 v=Draft202012Validator(get_schema(kind),format_checker=FormatChecker())
 out=[]
 for e in sorted(v.iter_errors(obj),key=lambda x:list(x.absolute_path)):
  path=prefix+''.join(f'[{i}]' if isinstance(i,int) else f'.{i}' for i in e.absolute_path)
  out.append(Issue(path,e.message))
 return out

def load_jsonl(path:Path,kind:str,allow_empty=False):
 rows=[]; issues=[]
 for n,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
  if not line.strip(): continue
  try: obj=json.loads(line)
  except Exception as e: issues.append(Issue(f'{path}:{n}',f'invalid JSON: {e}')); continue
  rows.append(obj); issues.extend(structural(obj,kind,f'{path}:{n}$'))
 if not rows and not allow_empty: issues.append(Issue(str(path),'must contain at least one record'))
 return rows,issues

def split_ids(v:str)->list[str]: return [x for x in (v or '').split('|') if x]

def load_coverage(path:Path):
 rows=[]; issues=[]
 with path.open(encoding='utf-8',newline='') as f:
  for n,row in enumerate(csv.DictReader(f),2):
   obj=dict(row)
   for k in ['evidence_ids','model_ids','verification_ids']: obj[k]=split_ids(obj.get(k,''))
   rows.append(obj); issues.extend(structural(obj,'coverage',f'{path}:{n}$'))
 return rows,issues

def ids(rows): return {x['id'] for x in rows if 'id' in x}

def option_fingerprint(o):
 return (
  ' '.join(o['mechanism'].lower().split()),
  tuple(sorted(x.lower() for x in o['change_surface']['enforcement_points'])),
  tuple(sorted(o['distinguishing_dimensions'])),
  ' '.join(o['transaction_semantics'].lower().split()),
  ' '.join(o['concurrency_semantics'].lower().split()),
  ' '.join(o['failure_semantics'].lower().split()))

def validate_package(a)->list[Issue]:
 issues=[]
 inp=load_doc(Path(a.input)); out=load_doc(Path(a.output)); dec=load_doc(Path(a.decision)); dom=load_doc(Path(a.dominance)); crit=load_doc(Path(a.critique_output))
 issues+=structural(inp,'input','$.input'); issues+=structural(out,'output','$.output'); issues+=structural(dec,'decision','$.decision'); issues+=structural(dom,'dominance','$.dominance'); issues+=structural(crit,'critique_output','$.critique_output')
 opts,e=load_jsonl(Path(a.options),'option'); issues+=e
 elems,e=load_jsonl(Path(a.elements),'element'); issues+=e
 rels,e=load_jsonl(Path(a.relations),'relation',allow_empty=True); issues+=e
 ledger,e=load_jsonl(Path(a.ledger),'evidence'); issues+=e
 cov,e=load_coverage(Path(a.coverage)); issues+=e
 if issues: return issues
 option_ids={o['option_id'] for o in opts}; active=[o for o in opts if o['status']=='ACTIVE']; active_ids={o['option_id'] for o in active}; viable=[o for o in active if o['viability'] in {'VIABLE','CONDITIONALLY_VIABLE'}]
 elem_ids=ids(elems); rel_ids=ids(rels); evid_ids=ids(ledger); target_ids={t['target_id'] for t in inp['design_targets']}; source_ids={sid for t in inp['design_targets'] for sid in t['source_ids']}
 problem_ids={p for x in elems for p in x.get('problem_ids',[])} | {x for x in source_ids if x.startswith(('PS-','PE-','AC-'))}
 invariant_ids={x['id'] for x in elems if x.get('type')=='INVARIANT'} | {x for x in evid_ids if x.startswith('INV-')}
 # Upstream gate and version binding
 if crit['gate_decision']['status']!='READY_FOR_CHANGE_OPTIONS': issues.append(Issue('$.critique_output.gate_decision.status','must be READY_FOR_CHANGE_OPTIONS'))
 if crit['human_model_approval']['status']!='APPROVED': issues.append(Issue('$.critique_output.human_model_approval.status','must be APPROVED'))
 if inp['source_model']['modeling_id']!=crit['source_model']['modeling_id']: issues.append(Issue('$.input.source_model.modeling_id','does not match critique output'))
 if inp['source_model']['model_version']!=crit['human_model_approval']['approved_model_version']: issues.append(Issue('$.input.source_model.model_version','does not match approved model version'))
 if out['source_model']['modeling_id']!=inp['source_model']['modeling_id']: issues.append(Issue('$.output.source_model.modeling_id','does not match input'))
 if out['source_model']['model_version']!=inp['source_model']['model_version']: issues.append(Issue('$.output.source_model.model_version','does not match input'))
 # Target source refs
 for t in inp['design_targets']:
  for ref in t['source_ids']:
   if ref.startswith('MDL-') and ref not in elem_ids: issues.append(Issue(f'$.target[{t["target_id"]}].source_ids',f'unknown model id: {ref}'))
   elif ref.startswith(('F-','INF-','ASM-','UNK-','CON-','INV-','RSK-')) and ref not in evid_ids and ref not in elem_ids: issues.append(Issue(f'$.target[{t["target_id"]}].source_ids',f'unknown evidence/invariant id: {ref}'))
 # Option refs and semantic completeness
 all_vstr={v['verification_id'] for o in opts for v in o['verification_strategy']}
 all_sasm={x['assumption_id'] for o in opts for x in o['new_assumptions']}
 all_srisk={x['risk_id'] for o in opts for x in o['residual_risks']}
 blocking=[]
 for o in opts:
  oid=o['option_id']
  for x in o['target_ids']:
   if x not in target_ids: issues.append(Issue(f'$.option[{oid}].target_ids',f'unknown target: {x}'))
  for x in o['problem_ids']:
   if x not in problem_ids: issues.append(Issue(f'$.option[{oid}].problem_ids',f'unknown problem id: {x}'))
  for x in o['model_ids']:
   if x not in elem_ids: issues.append(Issue(f'$.option[{oid}].model_ids',f'unknown model id: {x}'))
  for x in o['evidence_ids']+o['assumption_ids']:
   if x not in evid_ids: issues.append(Issue(f'$.option[{oid}].evidence_ids',f'unknown evidence id: {x}'))
  for x in o['invariant_ids']:
   if x not in invariant_ids and x not in elem_ids: issues.append(Issue(f'$.option[{oid}].invariant_ids',f'unknown invariant id: {x}'))
  for s in o['new_assumptions']:
   if s['blocking']: blocking.append(s['assumption_id'])
  if o['status']=='ACTIVE' and not o['target_ids']: issues.append(Issue(f'$.option[{oid}].target_ids','active option must address at least one target'))
  if o['viability']=='NOT_VIABLE' and o['status']!='ELIMINATED': issues.append(Issue(f'$.option[{oid}]','NOT_VIABLE option must be ELIMINATED'))
  if o['status']=='ELIMINATED' and o['viability']!='NOT_VIABLE': issues.append(Issue(f'$.option[{oid}]','ELIMINATED option must be NOT_VIABLE'))
  vtargets={x for v in o['verification_strategy'] for x in v['target_ids']}
  missing=set(o['target_ids'])-vtargets
  if missing: issues.append(Issue(f'$.option[{oid}].verification_strategy',f'missing verification for targets: {sorted(missing)}'))
 # Distinctness exact conservative fingerprint
 fps=defaultdict(list)
 for o in viable: fps[option_fingerprint(o)].append(o['option_id'])
 dup=[]
 for group in fps.values():
  if len(group)>1:
   for i in range(len(group)):
    for j in range(i+1,len(group)): dup.append(sorted([group[i],group[j]]))
 # Coverage matrix exact Cartesian product for active options x targets
 seen=Counter((r['option_id'],r['target_id']) for r in cov)
 for r in cov:
  if r['option_id'] not in option_ids: issues.append(Issue(f'$.coverage[{r["coverage_id"]}].option_id',f'unknown option: {r["option_id"]}'))
  if r['target_id'] not in target_ids: issues.append(Issue(f'$.coverage[{r["coverage_id"]}].target_id',f'unknown target: {r["target_id"]}'))
  for x in r['evidence_ids']:
   if x not in evid_ids: issues.append(Issue(f'$.coverage[{r["coverage_id"]}].evidence_ids',f'unknown evidence: {x}'))
  for x in r['model_ids']:
   if x not in elem_ids: issues.append(Issue(f'$.coverage[{r["coverage_id"]}].model_ids',f'unknown model: {x}'))
  for x in r['verification_ids']:
   if x not in all_vstr: issues.append(Issue(f'$.coverage[{r["coverage_id"]}].verification_ids',f'unknown verification strategy: {x}'))
  if r['coverage_status']=='FULL' and (not r['verification_ids'] or not r['mechanism'].strip()): issues.append(Issue(f'$.coverage[{r["coverage_id"]}]','FULL coverage requires mechanism and verification'))
 for oid in active_ids:
  for tid in target_ids:
   n=seen[(oid,tid)]
   if n!=1: issues.append(Issue('$.coverage',f'active option {oid} and target {tid} require exactly one row, found {n}'))
 # Every FULL-required target must have full viable option
 uncovered=[]
 for t in inp['design_targets']:
  if t['required_coverage']=='FULL':
   good=any(r['target_id']==t['target_id'] and r['option_id'] in {o['option_id'] for o in viable} and r['coverage_status']=='FULL' for r in cov)
   if not good: uncovered.append(t['target_id'])
 # Decision refs and no approval
 if dec['status']=='APPROVED': issues.append(Issue('$.decision.status','solution-design cannot approve a decision'))
 if set(dec['candidate_option_ids'])!=active_ids: issues.append(Issue('$.decision.candidate_option_ids','must exactly match active option ids'))
 if dec['recommended_option_id'] is not None and dec['recommended_option_id'] not in active_ids: issues.append(Issue('$.decision.recommended_option_id','must reference active option'))
 for c in dec['comparison_criteria']:
  if set(c['option_scores'])!=active_ids: issues.append(Issue(f'$.decision.comparison_criteria[{c["criterion"]}].option_scores','must score every active option exactly once'))
 # Dominance
 single=len(viable)==1
 if single:
  if not inp['option_policy']['allow_single_viable_option']: issues.append(Issue('$.options','single viable option is prohibited by input policy'))
  if not dom['required']: issues.append(Issue('$.dominance.required','must be true when exactly one viable option exists'))
  else:
   if dom['surviving_option_id']!=viable[0]['option_id']: issues.append(Issue('$.dominance.surviving_option_id','must match the only viable option'))
   for alt in dom['considered_alternatives']:
    for x in alt['evidence_ids']:
     if x not in evid_ids: issues.append(Issue(f'$.dominance.alternative[{alt["alternative_id"]}]',f'unknown evidence: {x}'))
 else:
  if dom['required']: issues.append(Issue('$.dominance.required','must be false when multiple viable options exist'))
 # Output counts
 ds=out['design_summary']; counts=Counter(o['viability'] for o in opts)
 expected={'total_options':len(opts),'viable_options':counts['VIABLE'],'conditionally_viable_options':counts['CONDITIONALLY_VIABLE'],'eliminated_options':sum(1 for o in opts if o['status']=='ELIMINATED'),'required_targets':len(target_ids),'single_option_mode':single}
 for k,v in expected.items():
  if ds[k]!=v: issues.append(Issue(f'$.output.design_summary.{k}',f'expected {v}, got {ds[k]}'))
 cs=out['coverage_summary']; ccount=Counter(r['coverage_status'] for r in cov); target_full={r['target_id'] for r in cov if r['coverage_status']=='FULL' and r['option_id'] in {o['option_id'] for o in viable}}
 expcs={'total_rows':len(cov),'full_rows':ccount['FULL'],'partial_rows':ccount['PARTIAL'],'none_rows':ccount['NONE'],'targets_with_at_least_one_full_option':len(target_full),'uncovered_target_ids':sorted(uncovered)}
 for k,v in expcs.items():
  got=sorted(cs[k]) if isinstance(v,list) else cs[k]
  if got!=v: issues.append(Issue(f'$.output.coverage_summary.{k}',f'expected {v}, got {got}'))
 # Artifact counts
 expected_files={'options':len(opts),'coverage_matrix':len(cov),'decision_record':1,'dominance_proof':1,'report':1}
 for k,n in expected_files.items():
  if out['artifact_files'][k]['record_count']!=n: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {n}'))
 # Summary consistency
 if sorted(out['distinctness_summary']['duplicate_option_pairs'])!=sorted(dup): issues.append(Issue('$.output.distinctness_summary.duplicate_option_pairs',f'expected {dup}'))
 if out['distinctness_summary']['materially_distinct']!=(not dup): issues.append(Issue('$.output.distinctness_summary.materially_distinct',f'must be {not dup}'))
 actual_dims=sorted({d for o in viable for d in o['distinguishing_dimensions']})
 if sorted(out['distinctness_summary']['dimensions_used'])!=actual_dims: issues.append(Issue('$.output.distinctness_summary.dimensions_used',f'expected {actual_dims}'))
 if sorted(out['assumption_summary']['blocking_assumption_ids'])!=sorted(blocking): issues.append(Issue('$.output.assumption_summary.blocking_assumption_ids',f'expected {sorted(blocking)}'))
 nonblocking=sorted([s['assumption_id'] for o in opts for s in o['new_assumptions'] if not s['blocking']]+[x for o in opts for x in o['assumption_ids']])
 if sorted(out['assumption_summary']['nonblocking_assumption_ids'])!=sorted(set(nonblocking)): issues.append(Issue('$.output.assumption_summary.nonblocking_assumption_ids',f'expected {sorted(set(nonblocking))}'))
 critrisks=sorted([r['risk_id'] for o in opts for r in o['residual_risks'] if r['severity']=='CRITICAL'])
 accept=sorted([r['risk_id'] for o in opts for r in o['residual_risks'] if r['acceptance_required']])
 if sorted(out['risk_summary']['critical_risk_ids'])!=critrisks: issues.append(Issue('$.output.risk_summary.critical_risk_ids',f'expected {critrisks}'))
 if sorted(out['risk_summary']['human_acceptance_required_ids'])!=accept: issues.append(Issue('$.output.risk_summary.human_acceptance_required_ids',f'expected {accept}'))
 if out['risk_summary']['all_options_have_residual_risks']!=all(bool(o['residual_risks']) for o in active): issues.append(Issue('$.output.risk_summary.all_options_have_residual_risks','does not match active options'))
 if out['recommendation']['binding'] is not False: issues.append(Issue('$.output.recommendation.binding','must be false'))
 if out['recommendation']['recommended_option_id']!=dec['recommended_option_id']: issues.append(Issue('$.output.recommendation.recommended_option_id','must match decision record'))
 # Gate
 gate=out['gate_decision']; qc=out['quality_checks']; ready=not issues and not blocking and not uncovered and not dup and len(viable)>=1 and (len(viable)>1 or dom['required'])
 if gate['status']=='READY_FOR_SOLUTION_CRITIQUE':
  if gate['next_state']!='SOLUTION_CRITIQUE': issues.append(Issue('$.output.gate_decision.next_state','must be SOLUTION_CRITIQUE'))
  if out['metadata']['status']!='COMPLETE': issues.append(Issue('$.output.metadata.status','must be COMPLETE'))
  if not all(qc.values()): issues.append(Issue('$.output.quality_checks','all checks must be true'))
  if blocking: issues.append(Issue('$.output.gate_decision','blocking assumptions prevent transition'))
  if uncovered: issues.append(Issue('$.output.gate_decision',f'uncovered targets prevent transition: {uncovered}'))
  if dup: issues.append(Issue('$.output.gate_decision',f'duplicate option pairs prevent transition: {dup}'))
  if len(viable)<1: issues.append(Issue('$.output.gate_decision','at least one viable option required'))
 if gate['status']=='RETURN_TO_INVESTIGATION':
  if gate['next_state']!='INVESTIGATION': issues.append(Issue('$.output.gate_decision.next_state','must be INVESTIGATION'))
  if not blocking: issues.append(Issue('$.output.gate_decision','RETURN_TO_INVESTIGATION requires blocking assumptions/evidence needs'))
 if gate['status']=='RETURN_TO_SYSTEM_MODEL' and gate['next_state']!='SYSTEM_MODEL': issues.append(Issue('$.output.gate_decision.next_state','must be SYSTEM_MODEL'))
 if gate['status']=='BLOCKED' and gate['next_state']!='SOLUTION_DESIGN': issues.append(Issue('$.output.gate_decision.next_state','must remain SOLUTION_DESIGN'))
 if a.require_transition_ready and gate['status']!='READY_FOR_SOLUTION_CRITIQUE': issues.append(Issue('$.output.gate_decision.status','package is not transition-ready for SOLUTION_CRITIQUE'))
 return issues

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--kind',required=True,choices=['input','output','option','coverage','decision','dominance','package'])
 p.add_argument('--file')
 for x in ['input','output','options','coverage','decision','dominance','critique-output','elements','relations','ledger']: p.add_argument('--'+x)
 p.add_argument('--require-transition-ready',action='store_true')
 a=p.parse_args()
 if a.kind=='package':
  missing=[x for x in ['input','output','options','coverage','decision','dominance','critique_output','elements','relations','ledger'] if getattr(a,x,None) is None]
  if missing: p.error('missing package arguments: '+', '.join(missing))
  issues=validate_package(a)
 elif a.kind=='option':
  if not a.file: p.error('--file required')
  _,issues=load_jsonl(Path(a.file),'option')
 elif a.kind=='coverage':
  if not a.file: p.error('--file required')
  _,issues=load_coverage(Path(a.file))
 else:
  if not a.file: p.error('--file required')
  issues=structural(load_doc(Path(a.file)),a.kind)
 if issues:
  print(f'INVALID ({len(issues)} issue(s))',file=sys.stderr)
  for i in issues: print('- '+str(i),file=sys.stderr)
  return 1
 print('VALID'+(' and transition-ready for SOLUTION_CRITIQUE' if a.kind=='package' and a.require_transition_ready else ''))
 return 0
if __name__=='__main__': raise SystemExit(main())
