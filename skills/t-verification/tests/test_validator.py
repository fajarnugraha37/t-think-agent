import copy, importlib.util, json, tempfile, unittest, yaml, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',ROOT/'validators'/'validate.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
BASE={'input':'examples/valid-input.yaml','output':'examples/valid-output-ready.yaml','assignment':'examples/valid-verifier-assignment.yaml','environment':'examples/valid-environment.yaml','technical_review_output':'examples/source-valid-technical-review-output.yaml','technical_review_contract':'examples/source-valid-technical-review-result-contract.yaml','implementation_contract':'examples/source-valid-implementation-result-contract.yaml','checklist_contract':'examples/source-valid-approved-checklist-contract.yaml','checklists':'examples/source-valid-checklist-items.jsonl','source_verifications':'examples/source-valid-verification-results.jsonl','repository_state':'examples/source-valid-repository-after.yaml','changes':'examples/source-valid-change-records.jsonl','source_ledger':'examples/source-valid-evidence-ledger.jsonl','obligations':'examples/valid-verification-obligations.jsonl','executions':'examples/valid-verification-executions.jsonl','falsifications':'examples/valid-falsification-attempts.jsonl','evidence':'examples/valid-verification-evidence.jsonl','findings':'examples/empty-verification-findings.jsonl','directives':'examples/empty-remediation-directives.jsonl','result_contract':'examples/valid-verification-result-contract.yaml'}
class A: pass
def args(over=None,ready=False):
 a=A()
 for k,p in BASE.items(): setattr(a,k,str(ROOT/p))
 if over:
  for k,p in over.items(): setattr(a,k,str(p))
 a.require_transition_ready=ready; return a
def dump(path,obj):
 if path.suffix=='.jsonl': path.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in obj))
 else: path.write_text(yaml.safe_dump(obj,sort_keys=False))
class TestValidator(unittest.TestCase):
 def assert_bad(self,mutator):
  with tempfile.TemporaryDirectory() as td:
   td=Path(td); over={}
   for k,p in BASE.items():
    src=ROOT/p; dst=td/(k+src.suffix); dst.write_bytes(src.read_bytes()); over[k]=dst
   mutator(over); self.assertTrue(v.validate_package(args(over)))
 def test_01_valid_ready(self): self.assertEqual(v.validate_package(args(ready=True)),[])
 def test_02_valid_bounded_loopback(self):
  over={'output':ROOT/'examples/valid-output-bounded-loopback.yaml','executions':ROOT/'examples/valid-verification-executions-bounded-loopback.jsonl','falsifications':ROOT/'examples/valid-falsification-attempts-bounded-loopback.jsonl','findings':ROOT/'examples/valid-findings-bounded-loopback.jsonl','directives':ROOT/'examples/valid-directives-bounded-loopback.jsonl','result_contract':ROOT/'examples/valid-verification-result-contract-bounded-loopback.yaml'}
  self.assertEqual(v.validate_package(args(over)),[])
 def test_03_technical_review_not_ready(self):
  def m(o): x=v.load(o['technical_review_output']); x['gate_decision']['status']='BLOCKED'; dump(o['technical_review_output'],x)
  self.assert_bad(m)
 def test_04_contract_not_pass(self):
  def m(o): x=v.load(o['technical_review_contract']); x['status']='FAIL'; dump(o['technical_review_contract'],x)
  self.assert_bad(m)
 def test_05_verifier_prohibited(self):
  def m(o): x=v.load(o['assignment']); x['verifier_id']=x['prohibited_identity_ids'][0]; dump(o['assignment'],x)
  self.assert_bad(m)
 def test_06_independence_false(self):
  def m(o): x=v.load(o['assignment']); x['independence']['not_technical_reviewer']=False; dump(o['assignment'],x)
  self.assert_bad(m)
 def test_07_missing_competency(self):
  def m(o): x=v.load(o['assignment']); x['declared_competencies'].remove('SECURITY'); dump(o['assignment'],x)
  self.assert_bad(m)
 def test_08_environment_tree_drift(self):
  def m(o): x=v.load(o['environment']); x['repository']['tree_digest']='sha256:'+'0'*64; dump(o['environment'],x)
  self.assert_bad(m)
 def test_09_dependency_unavailable(self):
  def m(o): x=v.load(o['environment']); x['dependencies'][0]['availability']='UNAVAILABLE'; dump(o['environment'],x)
  self.assert_bad(m)
 def test_10_missing_obligation(self):
  def m(o): x=v.load(o['obligations']); x.pop(); dump(o['obligations'],x)
  self.assert_bad(m)
 def test_11_duplicate_source_item(self):
  def m(o): x=v.load(o['obligations']); x[-1]['source_verification_item_id']=x[0]['source_verification_item_id']; dump(o['obligations'],x)
  self.assert_bad(m)
 def test_12_dangling_source_result(self):
  def m(o): x=v.load(o['obligations']); x[0]['source_verification_result_id']='VRES-999'; dump(o['obligations'],x)
  self.assert_bad(m)
 def test_13_checklist_coverage_drift(self):
  def m(o): x=v.load(o['obligations']); x[0]['checklist_ids']=[x[0]['checklist_ids'][0]]; dump(o['obligations'],x)
  self.assert_bad(m)
 def test_14_missing_source_evidence(self):
  def m(o): x=v.load(o['obligations']); x[0]['source_evidence_ids']=['F-999']; dump(o['obligations'],x)
  self.assert_bad(m)
 def test_15_high_risk_without_falsification_flag(self):
  def m(o): x=v.load(o['obligations']); z=next(r for r in x if r['criticality']=='HIGH'); z['falsification_required']=False; dump(o['obligations'],x)
  self.assert_bad(m)
 def test_16_missing_execution(self):
  def m(o): x=v.load(o['executions']); x.pop(); dump(o['executions'],x)
  self.assert_bad(m)
 def test_17_repository_drift(self):
  def m(o): x=v.load(o['executions']); x[0]['repository_tree_after']='sha256:'+'1'*64; dump(o['executions'],x)
  self.assert_bad(m)
 def test_18_pass_nonzero_exit(self):
  def m(o): x=v.load(o['executions']); x[0]['exit_code']=1; dump(o['executions'],x)
  self.assert_bad(m)
 def test_19_dangling_execution_evidence(self):
  def m(o): x=v.load(o['executions']); x[0]['evidence_ids']=['VE-999']; dump(o['executions'],x)
  self.assert_bad(m)
 def test_20_missing_required_falsification(self):
  def m(o): x=v.load(o['falsifications']); x.pop(); dump(o['falsifications'],x)
  self.assert_bad(m)
 def test_21_refuted_without_finding(self):
  def m(o): x=v.load(o['falsifications']); x[0]['resolution']='REFUTED'; x[0]['impact']='BLOCKING'; dump(o['falsifications'],x)
  self.assert_bad(m)
 def test_22_failed_execution_without_finding(self):
  def m(o): x=v.load(o['executions']); x[0]['outcome']='FAIL'; x[0]['exit_code']=1; dump(o['executions'],x)
  self.assert_bad(m)
 def test_23_finding_dangling_target(self):
  def m(o): shutil.copy(ROOT/'examples/invalid-finding-dangling-target.jsonl',o['findings'])
  self.assert_bad(m)
 def test_24_directive_applied(self):
  def m(o):
   shutil.copy(ROOT/'examples/valid-findings-bounded-loopback.jsonl',o['findings']); x=v.load(ROOT/'examples/valid-directives-bounded-loopback.jsonl'); x[0]['applied']=True; dump(o['directives'],x)
  self.assert_bad(m)
 def test_25_directive_wrong_route(self):
  def m(o):
   shutil.copy(ROOT/'examples/valid-findings-bounded-loopback.jsonl',o['findings']); x=v.load(ROOT/'examples/valid-directives-bounded-loopback.jsonl'); x[0]['target_state']='IMPLEMENTATION_PLAN'; dump(o['directives'],x)
  self.assert_bad(m)
 def test_26_bundle_digest_drift(self):
  def m(o): x=v.load(o['result_contract']); x['verification_bundle_digest']='sha256:'+'2'*64; dump(o['result_contract'],x)
  self.assert_bad(m)
 def test_27_output_artifact_digest_drift(self):
  def m(o): x=v.load(o['output']); x['artifact_files']['executions']['digest']='sha256:'+'3'*64; dump(o['output'],x)
  self.assert_bad(m)
 def test_28_source_artifact_digest_drift(self):
  def m(o): x=v.load(o['input']); x['source_artifacts']['technical_review_contract']['digest']='sha256:'+'4'*64; dump(o['input'],x)
  self.assert_bad(m)
 def test_29_ready_summary_failure(self):
  def m(o): x=v.load(o['output']); x['obligation_summary']['failed']=1; dump(o['output'],x)
  self.assert_bad(m)
 def test_30_ready_required_rejects_loopback(self):
  over={'output':ROOT/'examples/valid-output-bounded-loopback.yaml','executions':ROOT/'examples/valid-verification-executions-bounded-loopback.jsonl','falsifications':ROOT/'examples/valid-falsification-attempts-bounded-loopback.jsonl','findings':ROOT/'examples/valid-findings-bounded-loopback.jsonl','directives':ROOT/'examples/valid-directives-bounded-loopback.jsonl','result_contract':ROOT/'examples/valid-verification-result-contract-bounded-loopback.yaml'}
  self.assertTrue(v.validate_package(args(over,ready=True)))
if __name__=='__main__': unittest.main()
