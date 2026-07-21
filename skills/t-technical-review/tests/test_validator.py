import copy, importlib.util, json, tempfile, unittest, yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',ROOT/'validators'/'validate.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
BASE={
'input':'examples/valid-input.yaml','output':'examples/valid-output-ready.yaml','assignment':'examples/valid-review-assignment.yaml','self_review_output':'examples/source-valid-self-review-output.yaml','self_review_contract':'examples/source-valid-self-review-result-contract.yaml','bounded_output':'examples/source-valid-bounded-output.yaml','implementation_contract':'examples/source-valid-implementation-result-contract.yaml','checklist_contract':'examples/source-valid-approved-checklist-contract.yaml','checklists':'examples/source-valid-checklist-items.jsonl','changes':'examples/source-valid-change-records.jsonl','verifications':'examples/source-valid-verification-results.jsonl','repository_after':'examples/source-valid-repository-after.yaml','ledger':'examples/source-valid-evidence-ledger.jsonl','self_review_checks':'examples/source-valid-self-review-checks.jsonl','self_review_conformance':'examples/source-valid-self-review-conformance.jsonl','self_review_audits':'examples/source-valid-self-review-audits.jsonl','self_review_findings':'examples/source-valid-self-review-findings.jsonl','self_review_directives':'examples/source-valid-self-review-directives.jsonl','technical_checks':'examples/valid-technical-review-checks.jsonl','change_assessments':'examples/valid-change-assessments.jsonl','evidence_challenges':'examples/valid-evidence-challenges.jsonl','findings':'examples/empty-review-findings.jsonl','directives':'examples/empty-remediation-directives.jsonl','result_contract':'examples/valid-technical-review-result-contract.yaml'}
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
    src=ROOT/p; dst=td/src.name; dst.write_bytes(src.read_bytes()); over[k]=dst
   mutator(over)
   self.assertTrue(v.validate_package(args(over)))
 def test_01_valid_ready(self): self.assertEqual(v.validate_package(args(ready=True)),[])
 def test_02_valid_loopback(self):
  over={'output':ROOT/'examples/valid-output-bounded-loopback.yaml','technical_checks':ROOT/'examples/valid-technical-review-checks-bounded-loopback.jsonl','change_assessments':ROOT/'examples/valid-change-assessments-bounded-loopback.jsonl','evidence_challenges':ROOT/'examples/valid-evidence-challenges-bounded-loopback.jsonl','findings':ROOT/'examples/valid-findings-bounded-loopback.jsonl','directives':ROOT/'examples/valid-directives-bounded-loopback.jsonl','result_contract':ROOT/'examples/valid-technical-review-result-contract-bounded-loopback.yaml'}
  self.assertEqual(v.validate_package(args(over)),[])
 def test_03_self_review_not_ready(self):
  def m(o): x=v.load(o['self_review_output']); x['gate_decision']['status']='BLOCKED'; dump(o['self_review_output'],x)
  self.assert_bad(m)
 def test_04_self_review_contract_not_pass(self):
  def m(o): x=v.load(o['self_review_contract']); x['status']='FAIL'; dump(o['self_review_contract'],x)
  self.assert_bad(m)
 def test_05_reviewer_same_as_implementer(self):
  def m(o): x=v.load(o['assignment']); x['reviewer_id']='bounded-implementation-skill'; dump(o['assignment'],x)
  self.assert_bad(m)
 def test_06_reviewer_same_as_self_reviewer(self):
  def m(o): x=v.load(o['assignment']); x['reviewer_id']='self-review-skill'; dump(o['assignment'],x)
  self.assert_bad(m)
 def test_07_independence_false(self):
  def m(o): x=v.load(o['assignment']); x['independence']['not_self_reviewer']=False; dump(o['assignment'],x)
  self.assert_bad(m)
 def test_08_missing_competency(self):
  def m(o): x=v.load(o['assignment']); x['declared_competencies'].remove('SECURITY'); dump(o['assignment'],x)
  self.assert_bad(m)
 def test_09_missing_dimension(self):
  def m(o): x=v.load(o['technical_checks']); x.pop(); dump(o['technical_checks'],x)
  self.assert_bad(m)
 def test_10_duplicate_dimension(self):
  def m(o): x=v.load(o['technical_checks']); x[-1]['dimension']=x[0]['dimension']; dump(o['technical_checks'],x)
  self.assert_bad(m)
 def test_11_missing_self_review_claim_coverage(self):
  def m(o):
   x=v.load(o['technical_checks']); target=x[0]['source_self_review_check_ids'][0]
   for r in x:
    r['source_self_review_check_ids']=[z for z in r['source_self_review_check_ids'] if z!=target]
   dump(o['technical_checks'],x)
  self.assert_bad(m)
 def test_12_duplicate_change_assessment(self):
  def m(o): x=v.load(o['change_assessments']); x.append(copy.deepcopy(x[0])); x[-1]['assessment_id']='TRCA-999'; dump(o['change_assessments'],x)
  self.assert_bad(m)
 def test_13_missing_change_assessment(self):
  def m(o): x=v.load(o['change_assessments']); x.pop(); dump(o['change_assessments'],x)
  self.assert_bad(m)
 def test_14_diff_digest_drift(self):
  def m(o): x=v.load(o['change_assessments']); x[0]['source_diff_digest']='sha256:'+'0'*64; dump(o['change_assessments'],x)
  self.assert_bad(m)
 def test_15_approve_with_semantic_false(self):
  def m(o): x=v.load(o['change_assessments']); x[0]['semantic_conformance']=False; dump(o['change_assessments'],x)
  self.assert_bad(m)
 def test_16_no_evidence_challenge(self):
  def m(o): dump(o['evidence_challenges'],[])
  self.assert_bad(m)
 def test_17_refuted_challenge_without_finding(self):
  def m(o): x=v.load(o['evidence_challenges']); x[0]['resolution']='REFUTED'; x[0]['impact']='NONE'; dump(o['evidence_challenges'],x)
  self.assert_bad(m)
 def test_18_dangling_challenge_target(self):
  def m(o): x=v.load(o['evidence_challenges']); x[0]['target_id']='SRCHK-999'; dump(o['evidence_challenges'],x)
  self.assert_bad(m)
 def test_19_dangling_finding_target(self):
  def m(o): shutil=__import__('shutil'); shutil.copy(ROOT/'examples/invalid-finding-dangling-target.jsonl',o['findings'])
  self.assert_bad(m)
 def test_20_directive_applied(self):
  def m(o):
   shutil=__import__('shutil'); shutil.copy(ROOT/'examples/valid-findings-bounded-loopback.jsonl',o['findings']); x=v.load(ROOT/'examples/valid-directives-bounded-loopback.jsonl'); x[0]['applied']=True; dump(o['directives'],x)
  self.assert_bad(m)
 def test_21_result_contract_digest_drift(self):
  def m(o): x=v.load(o['result_contract']); x['technical_review_bundle_digest']='sha256:'+'1'*64; dump(o['result_contract'],x)
  self.assert_bad(m)
 def test_22_output_artifact_digest_drift(self):
  def m(o): x=v.load(o['output']); x['artifact_files']['technical_checks']['digest']='sha256:'+'2'*64; dump(o['output'],x)
  self.assert_bad(m)
 def test_23_source_artifact_digest_drift(self):
  def m(o): x=v.load(o['input']); x['source_artifacts']['change_records']['digest']='sha256:'+'3'*64; dump(o['input'],x)
  self.assert_bad(m)
 def test_24_ready_required_rejects_loopback(self):
  over={'output':ROOT/'examples/valid-output-bounded-loopback.yaml','technical_checks':ROOT/'examples/valid-technical-review-checks-bounded-loopback.jsonl','change_assessments':ROOT/'examples/valid-change-assessments-bounded-loopback.jsonl','evidence_challenges':ROOT/'examples/valid-evidence-challenges-bounded-loopback.jsonl','findings':ROOT/'examples/valid-findings-bounded-loopback.jsonl','directives':ROOT/'examples/valid-directives-bounded-loopback.jsonl','result_contract':ROOT/'examples/valid-technical-review-result-contract-bounded-loopback.yaml'}
  self.assertTrue(v.validate_package(args(over,ready=True)))
if __name__=='__main__': unittest.main()
