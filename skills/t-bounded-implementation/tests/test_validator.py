import argparse, copy, json, sys, tempfile, unittest, yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'validators'))
import validate as V
class Tests(unittest.TestCase):
 def args(self, **overrides):
  base=dict(input=str(ROOT/'examples/valid-input.yaml'),output=str(ROOT/'examples/valid-output-ready.yaml'),checklist_contract=str(ROOT/'examples/source-valid-approved-checklist-contract.yaml'),critique_output=str(ROOT/'examples/source-valid-checklist-critique-output.yaml'),plan_contract=str(ROOT/'examples/source-valid-approved-plan-contract.yaml'),checklists=str(ROOT/'examples/source-valid-checklist-items.jsonl'),batches=str(ROOT/'examples/source-valid-execution-batches.jsonl'),ledger=str(ROOT/'examples/source-valid-evidence-ledger.jsonl'),executions=str(ROOT/'examples/valid-execution-records.jsonl'),changes=str(ROOT/'examples/valid-change-records.jsonl'),commands=str(ROOT/'examples/valid-command-results.jsonl'),verifications=str(ROOT/'examples/valid-verification-results.jsonl'),rollbacks=str(ROOT/'examples/valid-rollback-results.jsonl'),findings=str(ROOT/'examples/empty-implementation-findings.jsonl'),repository_before=str(ROOT/'examples/valid-repository-before.yaml'),repository_after=str(ROOT/'examples/valid-repository-after.yaml'),result_contract=str(ROOT/'examples/valid-implementation-result-contract.yaml'),require_transition_ready=False)
  base.update(overrides); return argparse.Namespace(**base)
 def mutate_yaml(self,path,fn):
  d=yaml.safe_load(Path(path).read_text()); fn(d); f=tempfile.NamedTemporaryFile('w',suffix='.yaml',delete=False); yaml.safe_dump(d,f,sort_keys=False); f.close(); return f.name
 def mutate_jsonl(self,path,fn):
  rows=[json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]; fn(rows); f=tempfile.NamedTemporaryFile('w',suffix='.jsonl',delete=False); f.write(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in rows)); f.close(); return f.name
 def assert_bad(self,args,needle):
  issues=V.validate_package(args); self.assertTrue(issues); self.assertTrue(any(needle.lower() in str(x).lower() for x in issues),[str(x) for x in issues])
 def test_01_valid_ready(self): self.assertEqual([],V.validate_package(self.args(require_transition_ready=True)))
 def test_02_schema_valid(self):
  from jsonschema import Draft202012Validator
  for p in (ROOT/'schemas').glob('*.json'): Draft202012Validator.check_schema(json.loads(p.read_text()))
 def test_03_checklist_loopback_valid(self):
  a=self.args(output=str(ROOT/'examples/valid-output-checklist-loopback.yaml'),executions=str(ROOT/'examples/valid-execution-records-checklist-loopback.jsonl'),changes=str(ROOT/'examples/valid-change-records-checklist-loopback.jsonl'),commands=str(ROOT/'examples/valid-command-results-checklist-loopback.jsonl'),verifications=str(ROOT/'examples/valid-verification-results-checklist-loopback.jsonl'),findings=str(ROOT/'examples/valid-findings-checklist-loopback.jsonl'),repository_after=str(ROOT/'examples/valid-repository-after-checklist-loopback.yaml'),result_contract=str(ROOT/'examples/valid-implementation-result-contract-checklist-loopback.yaml'))
  self.assertEqual([],V.validate_package(a))
 def test_04_reject_source_gate(self):
  p=self.mutate_yaml(self.args().critique_output,lambda d:d['gate_decision'].update(status='BLOCKED')); self.assert_bad(self.args(critique_output=p),'not ready')
 def test_05_reject_contract_digest_drift(self):
  p=self.mutate_yaml(self.args().checklist_contract,lambda d:d['operation_bindings'][0].update(checklist_item_digest='sha256:'+'0'*64)); self.assert_bad(self.args(checklist_contract=p),'digest drift')
 def test_06_reject_missing_execution(self):
  p=self.mutate_jsonl(self.args().executions,lambda r:r.pop()); self.assert_bad(self.args(executions=p),'exactly one execution')
 def test_07_reject_execution_order(self):
  p=self.mutate_jsonl(self.args().executions,lambda r:r.__setitem__(slice(0,2),[r[1],r[0]])); self.assert_bad(self.args(executions=p),'execution order')
 def test_08_reject_scope_expansion(self):
  p=self.mutate_jsonl(self.args().changes,lambda r:r[0].update(path='unapproved/secret.txt')); self.assert_bad(self.args(changes=p),'outside approved')
 def test_09_reject_semantic_decision(self):
  p=self.mutate_jsonl(self.args().changes,lambda r:r[0].update(semantic_decision_introduced=True)); self.assert_bad(self.args(changes=p),'False was expected')
 def test_10_reject_missing_human_gate(self):
  p=self.mutate_jsonl(self.args().executions,lambda r:next(x for x in r if x['checklist_id']=='CHK-015').update(human_authorization=None)); self.assert_bad(self.args(executions=p),'human gate')
 def test_11_reject_failed_dependency(self):
  def f(r):
   r[0]['status']='FAILED'; r[0]['failure']={'category':'COMMAND_FAILURE','message':'x','blocking':True,'finding_ids':['IFND-999']}; r[0]['next_action']='STOP_AND_ROUTE'
  p=self.mutate_jsonl(self.args().executions,f); self.assert_bad(self.args(executions=p),'dependency')
 def test_12_reject_command_exit_mismatch(self):
  p=self.mutate_jsonl(self.args().commands,lambda r:r[0].update(exit_code=7)); self.assert_bad(self.args(commands=p),'exit_code')
 def test_13_reject_verification_mapping(self):
  p=self.mutate_jsonl(self.args().verifications,lambda r:r[0].update(checklist_ids=['CHK-017'])); self.assert_bad(self.args(verifications=p),'expected')
 def test_14_reject_result_digest(self):
  p=self.mutate_yaml(self.args().result_contract,lambda d:d.update(implementation_bundle_digest='sha256:'+'0'*64)); self.assert_bad(self.args(result_contract=p),'expected sha256')
 def test_15_reject_repository_paths(self):
  p=self.mutate_yaml(self.args().repository_after,lambda d:d['changed_paths'].append('unknown.file')); self.assert_bad(self.args(repository_after=p),'exact union')
 def test_16_reject_failure_budget(self):
  p=self.mutate_jsonl(ROOT/'examples/valid-findings-checklist-loopback.jsonl',lambda r:r[0].update(remediation_attempts=99)); a=self.args(output=str(ROOT/'examples/valid-output-checklist-loopback.yaml'),executions=str(ROOT/'examples/valid-execution-records-checklist-loopback.jsonl'),changes=str(ROOT/'examples/valid-change-records-checklist-loopback.jsonl'),commands=str(ROOT/'examples/valid-command-results-checklist-loopback.jsonl'),verifications=str(ROOT/'examples/empty-verification-results.jsonl'),findings=p,repository_after=str(ROOT/'examples/valid-repository-after-checklist-loopback.yaml'),result_contract=str(ROOT/'examples/valid-implementation-result-contract-checklist-loopback.yaml')); self.assert_bad(a,'failure budget')
 def test_17_reject_transition_ready_on_loopback(self):
  a=self.args(output=str(ROOT/'examples/valid-output-checklist-loopback.yaml'),executions=str(ROOT/'examples/valid-execution-records-checklist-loopback.jsonl'),changes=str(ROOT/'examples/valid-change-records-checklist-loopback.jsonl'),commands=str(ROOT/'examples/valid-command-results-checklist-loopback.jsonl'),verifications=str(ROOT/'examples/valid-verification-results-checklist-loopback.jsonl'),findings=str(ROOT/'examples/valid-findings-checklist-loopback.jsonl'),repository_after=str(ROOT/'examples/valid-repository-after-checklist-loopback.yaml'),result_contract=str(ROOT/'examples/valid-implementation-result-contract-checklist-loopback.yaml'),require_transition_ready=True); self.assert_bad(a,'not transition-ready')
if __name__=='__main__': unittest.main(verbosity=2)
