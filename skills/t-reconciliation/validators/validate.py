#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, warnings
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any
import yaml
warnings.filterwarnings('ignore',category=DeprecationWarning)
from jsonschema import Draft202012Validator, FormatChecker, RefResolver
ROOT=Path(__file__).resolve().parents[1]
MAP={'input':'input.schema.json','output':'output.schema.json','assignment':'reconciler-assignment.schema.json','artifact':'artifact-registry-row.schema.json','node':'traceability-node.schema.json','link':'traceability-link.schema.json','closure':'closure-obligation.schema.json','contradiction':'contradiction.schema.json','gap':'residual-gap.schema.json','approval':'closure-approval.schema.json','result_contract':'reconciliation-result-contract.schema.json','verification_output':'upstream-verification-output.schema.json','verification_contract':'upstream-verification-result-contract.schema.json','verification_obligation':'upstream-verification-obligation.schema.json','verification_execution':'upstream-verification-execution.schema.json','verification_evidence':'upstream-verification-evidence.schema.json','technical_review_contract':'upstream-technical-review-result-contract.schema.json','implementation_contract':'upstream-implementation-result-contract.schema.json','checklist_contract':'upstream-approved-checklist-contract.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in MAP.items()}
ROWS={'artifact','node','link','closure','contradiction','gap','verification_obligation','verification_execution','verification_evidence'}
PHASES=['PROBLEM_ALIGNMENT','INVESTIGATION','SYSTEM_MODEL','MODEL_CRITIQUE','SOLUTION_DESIGN','SOLUTION_CRITIQUE','IMPLEMENTATION_PLAN','PLAN_CRITIQUE','IMPLEMENTATION_CHECKLIST','CHECKLIST_CRITIQUE','BOUNDED_IMPLEMENTATION','SELF_REVIEW','TECHNICAL_REVIEW','VERIFICATION']
PRIORITY=['PROBLEM_ALIGNMENT','INVESTIGATION','SYSTEM_MODEL','MODEL_CRITIQUE','SOLUTION_DESIGN','SOLUTION_CRITIQUE','IMPLEMENTATION_PLAN','PLAN_CRITIQUE','IMPLEMENTATION_CHECKLIST','CHECKLIST_CRITIQUE','BOUNDED_IMPLEMENTATION','SELF_REVIEW','TECHNICAL_REVIEW','VERIFICATION','RECONCILIATION']
class Issue:
 def __init__(self,path,msg): self.path,self.message=path,msg
 def __str__(self): return f'{self.path}: {self.message}'
def load(path):
 p=Path(path); text=p.read_text()
 if p.suffix=='.jsonl': return [json.loads(x) for x in text.splitlines() if x.strip()]
 if p.suffix=='.json': return json.loads(text)
 return yaml.safe_load(text)
def validate_obj(obj,kind):
 schema=json.loads(SCHEMAS[kind].read_text()); base=SCHEMAS[kind].resolve().as_uri(); resolver=RefResolver(base_uri=base,referrer=schema)
 return [Issue('$'+''.join(f'[{x}]' if isinstance(x,int) else f'.{x}' for x in e.path),e.message) for e in Draft202012Validator(schema,resolver=resolver,format_checker=FormatChecker()).iter_errors(obj)]
def structural(obj,kind):
 if kind in ROWS:
  if not isinstance(obj,list): return [Issue('$','expected JSONL/list')]
  out=[]
  for i,x in enumerate(obj):
   for e in validate_obj(x,kind): e.path=f'$[{i}]'+e.path[1:]; out.append(e)
  return out
 return validate_obj(obj,kind)
def unique(rows,key,path,issues):
 vals=[x[key] for x in rows]; d=[x for x,c in Counter(vals).items() if c>1]
 if d: issues.append(Issue(path,'duplicate IDs: '+', '.join(d)))
def digest_file(path): return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canon(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def bundle(assignment,arts,nodes,links,closures,contradictions,gaps,approval,source_binding):
 return 'sha256:'+hashlib.sha256(canon({'assignment':assignment,'artifact_registry':arts,'traceability_nodes':nodes,'traceability_links':links,'closure_obligations':closures,'contradictions':contradictions,'residual_gaps':gaps,'closure_approval':approval,'source_binding':source_binding})).hexdigest()
def expected_route(closures,contradictions,gaps,approval):
 blockers=[]
 for x in closures:
  if x['blocking'] and x['closure_status'] in ['OPEN','BLOCKED','CONFLICT']: blockers.append((x['closure_id'],x['required_route']))
 for x in contradictions:
  if x['blocking'] and x['status']=='OPEN': blockers.append((x['contradiction_id'],x['required_route']))
 for x in gaps:
  if x['blocking'] and x['status']=='OPEN': blockers.append((x['gap_id'],x['required_route']))
 if blockers:
  routes={r for _,r in blockers}; route=next((r for r in PRIORITY if r in routes),'RECONCILIATION')
  return 'LOOPBACK_REQUIRED' if route!='RECONCILIATION' else 'BLOCKED',route,[i for i,_ in blockers]
 if approval['decision']!='APPROVED' or not approval['confirmation']['authorize_completion']:
  return 'AWAITING_HUMAN_CLOSURE','RECONCILIATION',[]
 return 'RECONCILED_COMPLETE','COMPLETED',[]
def has_path(adj,start,target,allowed=None):
 q=deque([start]); seen={start}
 while q:
  x=q.popleft()
  if x==target: return True
  for n in adj.get(x,[]):
   if n not in seen: seen.add(n); q.append(n)
 return False
def validate_package(a):
 issues=[]
 names=['input','output','assignment','verification_output','verification_contract','verification_obligations','verification_executions','verification_evidence','technical_review_contract','implementation_contract','checklist_contract','artifacts','nodes','links','closures','contradictions','gaps','approval','result_contract']
 vals={n:load(getattr(a,n)) for n in names}
 kinds={'input':'input','output':'output','assignment':'assignment','verification_output':'verification_output','verification_contract':'verification_contract','verification_obligations':'verification_obligation','verification_executions':'verification_execution','verification_evidence':'verification_evidence','technical_review_contract':'technical_review_contract','implementation_contract':'implementation_contract','checklist_contract':'checklist_contract','artifacts':'artifact','nodes':'node','links':'link','closures':'closure','contradictions':'contradiction','gaps':'gap','approval':'approval','result_contract':'result_contract'}
 for n in names: issues+=structural(vals[n],kinds[n])
 if issues: return issues
 inp,out,ass=vals['input'],vals['output'],vals['assignment']; vo,vc=vals['verification_output'],vals['verification_contract']; vobs,vexec,vevid=vals['verification_obligations'],vals['verification_executions'],vals['verification_evidence']; trc,ic,cc=vals['technical_review_contract'],vals['implementation_contract'],vals['checklist_contract']; arts,nodes,links,closures,cons,gaps,approval,rc=vals['artifacts'],vals['nodes'],vals['links'],vals['closures'],vals['contradictions'],vals['gaps'],vals['approval'],vals['result_contract']
 for rows,key,name in [(arts,'artifact_id','artifacts'),(nodes,'trace_node_id','nodes'),(links,'link_id','links'),(closures,'closure_id','closures'),(cons,'contradiction_id','contradictions'),(gaps,'gap_id','gaps'),(vobs,'obligation_id','verification_obligations'),(vexec,'execution_id','verification_executions'),(vevid,'evidence_id','verification_evidence')]: unique(rows,key,'$.'+name,issues)
 # Upstream readiness and exact contract chain.
 if vo['gate_decision']['status']!='READY_FOR_RECONCILIATION' or vo['gate_decision']['next_state']!='RECONCILIATION': issues.append(Issue('$.verification_output','must be READY_FOR_RECONCILIATION -> RECONCILIATION'))
 if vc['status']!='PASS' or vc['verdict']['status']!='READY_FOR_RECONCILIATION': issues.append(Issue('$.verification_contract','must be PASS and READY_FOR_RECONCILIATION'))
 sb={'verification_contract_id':vc['contract_id'],'verification_bundle_digest':vc['verification_bundle_digest'],'verification_run_id':vc['verification_run_id'],'technical_review_contract_id':trc['contract_id'],'implementation_result_contract_id':ic['contract_id'],'approved_checklist_contract_id':cc['contract_id'],'repository_tree_digest':vc['repository_tree_digest']}
 if inp['source_authorization']!=sb: issues.append(Issue('$.input.source_authorization','does not match exact upstream contract chain'))
 if out['source_binding']!=sb: issues.append(Issue('$.output.source_binding','does not match exact upstream contract chain'))
 if vc['source_technical_review_contract_id']!=trc['contract_id'] or vc['source_implementation_contract_id']!=ic['contract_id'] or vc['source_checklist_contract_id']!=cc['contract_id']: issues.append(Issue('$.source_chain','verification contract IDs do not match supplied upstream contracts'))
 if vc['repository_tree_digest']!=trc['repository_after_tree_digest'] or vc['repository_tree_digest']!=ic['repository_after']['tree_digest']: issues.append(Issue('$.source_chain.repository_tree_digest','repository tree drift across implementation, technical review, and verification'))
 # Input file digests.
 for name,ref in inp['source_artifacts'].items():
  p=ROOT/ref['path'] if not Path(ref['path']).is_absolute() else Path(ref['path'])
  if not p.exists(): issues.append(Issue('$.input.source_artifacts.'+name,'path does not exist'))
  elif digest_file(p)!=ref['digest']: issues.append(Issue('$.input.source_artifacts.'+name+'.digest','does not match file'))
 # Assignment independence.
 if ass['reconciler_id'] in ass['prohibited_identity_ids']: issues.append(Issue('$.assignment.reconciler_id','must not be a prohibited upstream actor'))
 if not all(ass['independence'].values()): issues.append(Issue('$.assignment.independence','all independence assertions must be true'))
 required_comp={'TRACEABILITY','EVIDENCE_AUDIT','SOFTWARE_ARCHITECTURE','TEST_VERIFICATION','RISK_GOVERNANCE','CHANGE_MANAGEMENT'}
 if not required_comp.issubset(set(ass['declared_competencies'])): issues.append(Issue('$.assignment.declared_competencies','missing required competency'))
 if ass['reconciliation_run_id']!=inp['metadata']['reconciliation_run_id']: issues.append(Issue('$.assignment.reconciliation_run_id','run mismatch'))
 # Artifact registry integrity.
 aid={x['artifact_id']:x for x in arts}; phases={x['phase'] for x in arts if x['canonical']}
 missing=set(PHASES)-phases
 if missing: issues.append(Issue('$.artifacts','missing canonical phases: '+', '.join(sorted(missing))))
 canon_roles=Counter((x['phase'],x['artifact_role']) for x in arts if x['canonical'])
 dup=[f'{p}/{r}' for (p,r),c in canon_roles.items() if c>1]
 if dup: issues.append(Issue('$.artifacts','duplicate canonical phase/role: '+', '.join(dup)))
 for x in arts:
  if x['epistemic_status'] in ['UNKNOWN','CONFLICT'] and x['canonical']: issues.append(Issue('$.artifacts.'+x['artifact_id'],'canonical artifact cannot be UNKNOWN or CONFLICT'))
  if x['phase']=='VERIFICATION' and x['source_contract_id']!=vc['contract_id']: issues.append(Issue('$.artifacts.'+x['artifact_id'],'verification artifact must bind supplied VCON'))
  if x['phase'] in ['BOUNDED_IMPLEMENTATION','SELF_REVIEW','TECHNICAL_REVIEW','VERIFICATION'] and x['repository_tree_digest']!=vc['repository_tree_digest']: issues.append(Issue('$.artifacts.'+x['artifact_id']+'.repository_tree_digest','repository tree drift'))
 # Node and link closure.
 nid={x['trace_node_id']:x for x in nodes}; lid={x['link_id']:x for x in links}; veids={x['evidence_id'] for x in vevid}
 for x in nodes:
  if x['source_artifact_id'] not in aid: issues.append(Issue('$.nodes.'+x['trace_node_id']+'.source_artifact_id','dangling artifact'))
  if x['phase']!=aid.get(x['source_artifact_id'],{}).get('phase'): issues.append(Issue('$.nodes.'+x['trace_node_id']+'.phase','does not match source artifact phase'))
  if x['epistemic_status'] in ['UNKNOWN','CONFLICT'] and x['terminal_required']: issues.append(Issue('$.nodes.'+x['trace_node_id'],'terminal-required node cannot be UNKNOWN or CONFLICT'))
 for x in links:
  if x['from_node_id'] not in nid or x['to_node_id'] not in nid: issues.append(Issue('$.links.'+x['link_id'],'dangling endpoint'))
  if not x['evidence_ids']: issues.append(Issue('$.links.'+x['link_id']+'.evidence_ids','must not be empty'))
 adj=defaultdict(list)
 for x in links:
  if x['from_node_id'] in nid and x['to_node_id'] in nid: adj[x['from_node_id']].append(x['to_node_id'])
 terminal=[x for x in nodes if x['terminal_required'] and x['status'] not in ['SUPERSEDED','REJECTED']]
 cbyroot=defaultdict(list)
 for x in closures: cbyroot[x['root_node_id']].append(x)
 for n in terminal:
  if len(cbyroot[n['trace_node_id']])!=1: issues.append(Issue('$.closures','terminal node '+n['trace_node_id']+' must have exactly one closure obligation'))
 for c in closures:
  root=nid.get(c['root_node_id'])
  if not root: issues.append(Issue('$.closures.'+c['closure_id']+'.root_node_id','dangling root')); continue
  if root['node_type']!=c['root_type']: issues.append(Issue('$.closures.'+c['closure_id']+'.root_type','does not match root node type'))
  for t in c['observed_terminal_node_ids']:
   if t not in nid: issues.append(Issue('$.closures.'+c['closure_id']+'.observed_terminal_node_ids','dangling terminal '+t))
   elif not has_path(adj,c['root_node_id'],t): issues.append(Issue('$.closures.'+c['closure_id'],'declared terminal is not reachable from root: '+t))
  for l in c['path_link_ids']:
   if l not in lid: issues.append(Issue('$.closures.'+c['closure_id']+'.path_link_ids','dangling link '+l))
  observed_types={nid[t]['node_type'] for t in c['observed_terminal_node_ids'] if t in nid}
  if c['closure_status']=='CLOSED' and not set(c['required_terminal_types']).issubset(observed_types): issues.append(Issue('$.closures.'+c['closure_id'],'CLOSED but required terminal types are missing'))
  if c['closure_status']=='CLOSED' and c['blocking']: issues.append(Issue('$.closures.'+c['closure_id'],'closed obligation cannot be blocking'))
 # Verification-native node consistency.
 vobids={x['obligation_id'] for x in vobs}; verified_nodes={x['source_native_id'] for x in nodes if x['node_type']=='VERIFICATION_OBLIGATION'}
 if not verified_nodes.issubset(vobids): issues.append(Issue('$.nodes','verification obligation node references unknown VOB'))
 exebyob=defaultdict(list)
 for x in vexec: exebyob[x['obligation_id']].append(x)
 for vob in verified_nodes:
  if not any(e['outcome']=='PASS' for e in exebyob[vob]): issues.append(Issue('$.nodes','verification node has no PASS execution: '+vob))
 # Contradictions/gaps and evidence.
 for x in cons:
  if any(a not in aid for a in x['artifact_ids']): issues.append(Issue('$.contradictions.'+x['contradiction_id'],'dangling artifact'))
  if any(n not in nid for n in x['node_ids']): issues.append(Issue('$.contradictions.'+x['contradiction_id'],'dangling node'))
  if x['status']=='OPEN' and x['resolution'] is not None: issues.append(Issue('$.contradictions.'+x['contradiction_id'],'open contradiction cannot have resolution'))
  if x['status']=='RESOLVED' and not x['resolution']: issues.append(Issue('$.contradictions.'+x['contradiction_id'],'resolved contradiction requires resolution'))
 for x in gaps:
  if any(a not in aid for a in x['affected_artifact_ids']): issues.append(Issue('$.gaps.'+x['gap_id'],'dangling artifact'))
  if any(n not in nid for n in x['affected_node_ids']): issues.append(Issue('$.gaps.'+x['gap_id'],'dangling node'))
  if x['status']=='OPEN' and x['resolution'] is not None: issues.append(Issue('$.gaps.'+x['gap_id'],'open gap cannot have resolution'))
 # Approval.
 if approval['reconciler_id']!=ass['reconciler_id']: issues.append(Issue('$.approval.reconciler_id','does not match assignment'))
 if approval['approver_id']==ass['reconciler_id'] or approval['approver_id'] in ass['prohibited_identity_ids']: issues.append(Issue('$.approval.approver_id','must be an independent human approver'))
 accepted_risks={x['trace_node_id'] for x in nodes if x['node_type']=='RISK' and x['status']=='ACCEPTED_RISK'}
 accepted_gaps={x['gap_id'] for x in gaps if x['status']=='ACCEPTED_RISK'}; accepted_cons={x['contradiction_id'] for x in cons if x['status']=='ACCEPTED_RISK'}
 if set(approval['accepted_risk_node_ids'])!=accepted_risks: issues.append(Issue('$.approval.accepted_risk_node_ids','must exactly equal accepted-risk nodes'))
 if set(approval['accepted_gap_ids'])!=accepted_gaps: issues.append(Issue('$.approval.accepted_gap_ids','must exactly equal accepted-risk gaps'))
 if set(approval['accepted_contradiction_ids'])!=accepted_cons: issues.append(Issue('$.approval.accepted_contradiction_ids','must exactly equal accepted-risk contradictions'))
 # Expected route and result contract.
 status,next_state,blockers=expected_route(closures,cons,gaps,approval)
 expected_rc_status='RECONCILED' if status=='RECONCILED_COMPLETE' else ('AWAITING_HUMAN_APPROVAL' if status=='AWAITING_HUMAN_CLOSURE' else 'BLOCKED')
 if rc['status']!=expected_rc_status: issues.append(Issue('$.result_contract.status','inconsistent with reconciliation state'))
 if rc['verdict']['status']!=status or rc['verdict']['next_state']!=next_state: issues.append(Issue('$.result_contract.verdict','inconsistent expected route'))
 if set(rc['verdict']['blocking_ids'])!=set(blockers): issues.append(Issue('$.result_contract.verdict.blocking_ids','inconsistent blocking IDs'))
 if approval['approved_result_contract_id']!=rc['contract_id']: issues.append(Issue('$.approval.approved_result_contract_id','does not match result contract'))
 exp_bundle=bundle(ass,arts,nodes,links,closures,cons,gaps,approval,sb)
 if rc['reconciliation_bundle_digest']!=exp_bundle: issues.append(Issue('$.result_contract.reconciliation_bundle_digest','bundle digest mismatch'))
 exact_lists=[('artifact_ids',[x['artifact_id'] for x in arts]),('trace_node_ids',[x['trace_node_id'] for x in nodes]),('trace_link_ids',[x['link_id'] for x in links]),('closure_ids',[x['closure_id'] for x in closures]),('contradiction_ids',[x['contradiction_id'] for x in cons]),('gap_ids',[x['gap_id'] for x in gaps])]
 for k,v in exact_lists:
  if rc[k]!=v: issues.append(Issue('$.result_contract.'+k,'must preserve exact source order and IDs'))
 if rc['approval_id']!=approval['approval_id']: issues.append(Issue('$.result_contract.approval_id','approval ID mismatch'))
 # Output artifact files and summaries.
 pathmap={'assignment':a.assignment,'artifact_registry':a.artifacts,'traceability_nodes':a.nodes,'traceability_links':a.links,'closure_obligations':a.closures,'contradictions':a.contradictions,'residual_gaps':a.gaps,'closure_approval':a.approval,'result_contract':a.result_contract,'report':a.report}
 counts={'assignment':1,'artifact_registry':len(arts),'traceability_nodes':len(nodes),'traceability_links':len(links),'closure_obligations':len(closures),'contradictions':len(cons),'residual_gaps':len(gaps),'closure_approval':1,'result_contract':1,'report':1}
 for k,p in pathmap.items():
  rec=out['artifact_files'][k]
  if rec['digest']!=digest_file(p): issues.append(Issue('$.output.artifact_files.'+k+'.digest','does not match file'))
  if rec['record_count']!=counts[k]: issues.append(Issue('$.output.artifact_files.'+k+'.record_count','does not match records'))
 if out['artifact_summary']['total']!=len(arts) or set(out['artifact_summary']['phases_present'])!=phases: issues.append(Issue('$.output.artifact_summary','does not match artifact registry'))
 closed=sum(x['closure_status']=='CLOSED' for x in closures); accepted=sum(x['closure_status']=='ACCEPTED_RISK' for x in closures); opened=len(closures)-closed-accepted
 ts=out['traceability_summary']
 expected_ts=(len(nodes),len(links),len(terminal),len(closures),closed,accepted,opened)
 actual_ts=(ts['node_total'],ts['link_total'],ts['terminal_required_total'],ts['closure_total'],ts['closed_total'],ts['accepted_risk_total'],ts['open_total'])
 if actual_ts!=expected_ts: issues.append(Issue('$.output.traceability_summary','count mismatch'))
 cs=out['consistency_summary']; open_con=[x['contradiction_id'] for x in cons if x['status']=='OPEN' and x['blocking']]; open_gap=[x['gap_id'] for x in gaps if x['status']=='OPEN' and x['blocking']]
 if cs['contradiction_total']!=len(cons) or cs['gap_total']!=len(gaps) or cs['open_blocking_contradiction_ids']!=open_con or cs['open_blocking_gap_ids']!=open_gap: issues.append(Issue('$.output.consistency_summary','does not match contradiction/gap records'))
 expected_req='NONE' if next_state=='COMPLETED' else next_state
 if cs['required_route']!=expected_req: issues.append(Issue('$.output.consistency_summary.required_route','route mismatch'))
 if out['gate_decision']['status']!=status or out['gate_decision']['next_state']!=next_state or set(out['gate_decision']['blocking_ids'])!=set(blockers): issues.append(Issue('$.output.gate_decision','route/status mismatch'))
 if out['approval_summary']['decision']!=approval['decision'] or out['approval_summary']['approval_id']!=approval['approval_id'] or out['approval_summary']['completion_authorized']!=approval['confirmation']['authorize_completion']: issues.append(Issue('$.output.approval_summary','approval mismatch'))
 if a.require_transition_ready and status!='RECONCILED_COMPLETE': issues.append(Issue('$.gate','transition-ready requested but result is not RECONCILED_COMPLETE'))
 return issues
def main():
 p=argparse.ArgumentParser(); p.add_argument('--kind',choices=['package','file'],default='package'); p.add_argument('--schema-kind',choices=sorted(MAP)); p.add_argument('--file')
 for n in ['input','output','assignment','verification_output','verification_contract','verification_obligations','verification_executions','verification_evidence','technical_review_contract','implementation_contract','checklist_contract','artifacts','nodes','links','closures','contradictions','gaps','approval','result_contract','report']: p.add_argument('--'+n.replace('_','-'))
 p.add_argument('--require-transition-ready',action='store_true'); a=p.parse_args()
 if a.kind=='file':
  if not a.file or not a.schema_kind: p.error('--file and --schema-kind required')
  issues=structural(load(a.file),a.schema_kind)
 else:
  required=['input','output','assignment','verification_output','verification_contract','verification_obligations','verification_executions','verification_evidence','technical_review_contract','implementation_contract','checklist_contract','artifacts','nodes','links','closures','contradictions','gaps','approval','result_contract','report']
  missing=[n for n in required if not getattr(a,n)]
  if missing: p.error('missing: '+', '.join(missing))
  issues=validate_package(a)
 if issues:
  for i in issues: print(i,file=sys.stderr)
  print(f'INVALID ({len(issues)} issue(s))',file=sys.stderr); return 1
 print('VALID'); return 0
if __name__=='__main__': raise SystemExit(main())
