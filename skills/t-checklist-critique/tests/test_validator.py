#!/usr/bin/env python3
from __future__ import annotations
import copy,importlib.util,sys,tempfile,json,yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v',ROOT/'validators/validate.py'); v=importlib.util.module_from_spec(spec); sys.modules['v']=v; spec.loader.exec_module(v)
BASE={
 'input':ROOT/'examples/valid-input.yaml','output':ROOT/'examples/valid-output-ready.yaml','builder_output':ROOT/'examples/source-valid-checklist-builder-output.yaml','checklists':ROOT/'examples/source-valid-checklist-items.jsonl','dependencies':ROOT/'examples/source-valid-checklist-dependencies.jsonl','coverage':ROOT/'examples/source-valid-checklist-coverage.csv','batches':ROOT/'examples/source-valid-execution-batches.jsonl','findings':ROOT/'examples/source-empty-checklist-findings.jsonl','plan_contract':ROOT/'examples/source-valid-approved-plan-contract.yaml','plan_critique_output':ROOT/'examples/source-valid-plan-critique-output.yaml','ledger':ROOT/'examples/source-valid-evidence-ledger.jsonl','elements':ROOT/'examples/source-valid-model-elements.jsonl','relations':ROOT/'examples/source-valid-model-relations.jsonl','assessments':ROOT/'examples/valid-assessments.jsonl','revisions':ROOT/'examples/empty-revision-directives.jsonl','requests':ROOT/'examples/empty-evidence-requests.jsonl','approval':ROOT/'examples/valid-checklist-approval.yaml','checklist_contract':ROOT/'examples/valid-approved-checklist-contract.yaml'}
class Args:
 require_transition_ready=False
def run(paths=None,ready=False):
 a=Args(); a.require_transition_ready=ready
 for k,p in (paths or BASE).items(): setattr(a,k,str(p))
 return v.validate(a)
def mutate_yaml(base,fn,tmp,name):
 d=yaml.safe_load(Path(base).read_text()); fn(d); p=tmp/name; p.write_text(yaml.safe_dump(d,sort_keys=False)); return p
def mutate_jsonl(base,fn,tmp,name):
 rows=[json.loads(x) for x in Path(base).read_text().splitlines() if x.strip()]; fn(rows); p=tmp/name; p.write_text(''.join(json.dumps(x)+'\n' for x in rows)); return p
def expect_ok(name,paths=None,ready=False):
 e=run(paths,ready)
 if e: raise AssertionError(name+' expected valid: '+'; '.join(str(x) for x in e[:5]))
def expect_bad(name,paths):
 e=run(paths)
 if not e: raise AssertionError(name+' expected invalid')
def main():
 n=0
 expect_ok('ready',ready=True); n+=1
 with tempfile.TemporaryDirectory() as td:
  t=Path(td)
  p=dict(BASE); p['input']=mutate_yaml(BASE['input'],lambda d:d['human_critiques'][0].update(target_ids=['CDEP-999']),t,'x.yaml'); expect_bad('dangling target',p); n+=1
  p=dict(BASE); p['assessments']=mutate_jsonl(BASE['assessments'],lambda r:(r[0].update(evidence_reviewed=[]),r[0].update(contradicting_findings=[])),t,'a.jsonl'); expect_bad('rejection evidence',p); n+=1
  p=dict(BASE); p['assessments']=mutate_jsonl(BASE['assessments'],lambda r:r.append(copy.deepcopy(r[0])),t,'dup.jsonl'); expect_bad('duplicate assessment',p); n+=1
  p=dict(BASE); p['approval']=mutate_yaml(BASE['approval'],lambda d:d.update(approved_by='checklist-critique-skill'),t,'app.yaml'); expect_bad('self approval',p); n+=1
  p=dict(BASE); p['approval']=mutate_yaml(BASE['approval'],lambda d:d.update(accepted_residual_risk_ids=[]),t,'risk.yaml'); expect_bad('risk acceptance',p); n+=1
  p=dict(BASE); p['approval']=mutate_yaml(BASE['approval'],lambda d:d.update(accepted_human_gate_batch_ids=[]),t,'gate.yaml'); expect_bad('human gates',p); n+=1
  p=dict(BASE); p['checklist_contract']=mutate_yaml(BASE['checklist_contract'],lambda d:d.update(checklist_bundle_digest='sha256:'+'0'*64),t,'dig.yaml'); expect_bad('bundle digest',p); n+=1
  p=dict(BASE); p['checklist_contract']=mutate_yaml(BASE['checklist_contract'],lambda d:d['operation_bindings'][0].update(checklist_item_digest='sha256:'+'1'*64),t,'bind.yaml'); expect_bad('item binding',p); n+=1
  p=dict(BASE); p['checklist_contract']=mutate_yaml(BASE['checklist_contract'],lambda d:d['execution_order'].reverse(),t,'ord.yaml'); expect_bad('order drift',p); n+=1
  p=dict(BASE); p['checklist_contract']=mutate_yaml(BASE['checklist_contract'],lambda d:d['change_surface']['components'].append('unauthorized'),t,'scope.yaml'); expect_bad('scope drift',p); n+=1
  p=dict(BASE); p['output']=mutate_yaml(BASE['output'],lambda d:d['artifact_files']['assessments'].update(record_count=2),t,'cnt.yaml'); expect_bad('count drift',p); n+=1
  p=dict(BASE); p['approval']=ROOT/'examples/valid-checklist-approval-pending.yaml'; p['checklist_contract']=ROOT/'examples/valid-pending-checklist-contract.yaml'; expect_bad('ready without approval',p); n+=1
  p=dict(BASE); p.update({'input':ROOT/'examples/valid-input-checklist-revision-route.yaml','output':ROOT/'examples/valid-output-checklist-revision-route.yaml','assessments':ROOT/'examples/valid-assessments-checklist-revision-route.jsonl','revisions':ROOT/'examples/valid-revision-directives-checklist-route.jsonl','requests':ROOT/'examples/empty-evidence-requests.jsonl','approval':ROOT/'examples/valid-checklist-approval-pending.yaml','checklist_contract':ROOT/'examples/valid-pending-checklist-contract.yaml'}); expect_ok('checklist route',p); n+=1
  p=dict(BASE); p.update({'input':ROOT/'examples/valid-input-investigation-route.yaml','output':ROOT/'examples/valid-output-investigation-route.yaml','assessments':ROOT/'examples/valid-assessments-investigation-route.jsonl','revisions':ROOT/'examples/empty-revision-directives.jsonl','requests':ROOT/'examples/valid-evidence-requests-investigation-route.jsonl','approval':ROOT/'examples/valid-checklist-approval-pending.yaml','checklist_contract':ROOT/'examples/valid-pending-checklist-contract.yaml'}); expect_ok('investigation route',p); n+=1
  p=dict(BASE); p['checklist_contract']=mutate_yaml(BASE['checklist_contract'],lambda d:d['execution_policy'].update(on_ambiguity='GUESS'),t,'amb.yaml'); expect_bad('ambiguity guard',p); n+=1
 print(f'{n}/{n} tests passed')
if __name__=='__main__': main()
