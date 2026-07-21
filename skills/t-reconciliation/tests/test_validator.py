import importlib.util, json, tempfile, unittest, yaml, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',ROOT/'validators'/'validate.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
BASE={'input': 'examples/valid-input.yaml', 'output': 'examples/valid-output-complete.yaml', 'assignment': 'examples/valid-reconciler-assignment.yaml', 'verification_output': 'examples/source-valid-verification-output.yaml', 'verification_contract': 'examples/source-valid-verification-result-contract.yaml', 'verification_obligations': 'examples/source-valid-verification-obligations.jsonl', 'verification_executions': 'examples/source-valid-verification-executions.jsonl', 'verification_evidence': 'examples/source-valid-verification-evidence.jsonl', 'technical_review_contract': 'examples/source-valid-technical-review-result-contract.yaml', 'implementation_contract': 'examples/source-valid-implementation-result-contract.yaml', 'checklist_contract': 'examples/source-valid-approved-checklist-contract.yaml', 'artifacts': 'examples/valid-artifact-registry.jsonl', 'nodes': 'examples/valid-traceability-nodes.jsonl', 'links': 'examples/valid-traceability-links.jsonl', 'closures': 'examples/valid-closure-obligations.jsonl', 'contradictions': 'examples/empty-contradictions.jsonl', 'gaps': 'examples/empty-residual-gaps.jsonl', 'approval': 'examples/valid-closure-approval.yaml', 'result_contract': 'examples/valid-reconciliation-result-contract.yaml', 'report': 'examples/valid-reconciliation-report.md'}
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
 def test_01_valid_complete(self): self.assertEqual(v.validate_package(args(ready=True)),[])
 def test_02_valid_system_model_loopback(self):
  over={'output':ROOT/'examples/valid-output-system-model-loopback.yaml','closures':ROOT/'examples/valid-closure-obligations-system-model-loopback.jsonl','gaps':ROOT/'examples/valid-residual-gaps-system-model-loopback.jsonl','approval':ROOT/'examples/valid-closure-approval-system-model-loopback.yaml','result_contract':ROOT/'examples/valid-reconciliation-result-contract-system-model-loopback.yaml','report':ROOT/'examples/valid-reconciliation-report-system-model-loopback.md'}
  self.assertEqual(v.validate_package(args(over)),[])
 def test_03_verification_not_ready(self):
  def m(o): x=v.load(o['verification_output']); x['gate_decision']['status']='BLOCKED'; dump(o['verification_output'],x)
  self.assert_bad(m)
 def test_04_verification_contract_not_pass(self):
  def m(o): x=v.load(o['verification_contract']); x['status']='FAIL'; dump(o['verification_contract'],x)
  self.assert_bad(m)
 def test_05_source_authorization_drift(self):
  def m(o): x=v.load(o['input']); x['source_authorization']['verification_bundle_digest']='sha256:'+'0'*64; dump(o['input'],x)
  self.assert_bad(m)
 def test_06_source_artifact_digest_drift(self):
  def m(o): x=v.load(o['input']); x['source_artifacts']['verification_contract']['digest']='sha256:'+'1'*64; dump(o['input'],x)
  self.assert_bad(m)
 def test_07_reconciler_prohibited(self):
  def m(o): x=v.load(o['assignment']); x['reconciler_id']=x['prohibited_identity_ids'][0]; dump(o['assignment'],x)
  self.assert_bad(m)
 def test_08_independence_false(self):
  def m(o): x=v.load(o['assignment']); x['independence']['not_verifier']=False; dump(o['assignment'],x)
  self.assert_bad(m)
 def test_09_missing_competency(self):
  def m(o): x=v.load(o['assignment']); x['declared_competencies'].remove('TRACEABILITY'); dump(o['assignment'],x)
  self.assert_bad(m)
 def test_10_missing_phase(self):
  def m(o): x=v.load(o['artifacts']); x=[r for r in x if r['phase']!='INVESTIGATION']; dump(o['artifacts'],x)
  self.assert_bad(m)
 def test_11_duplicate_canonical_role(self):
  def m(o): x=v.load(o['artifacts']); z=dict(x[0]); z['artifact_id']='ART-999'; x.append(z); dump(o['artifacts'],x)
  self.assert_bad(m)
 def test_12_artifact_repository_drift(self):
  def m(o): x=v.load(o['artifacts']); next(r for r in x if r['phase']=='VERIFICATION')['repository_tree_digest']='sha256:'+'2'*64; dump(o['artifacts'],x)
  self.assert_bad(m)
 def test_13_node_dangling_artifact(self):
  def m(o): x=v.load(o['nodes']); x[0]['source_artifact_id']='ART-999'; dump(o['nodes'],x)
  self.assert_bad(m)
 def test_14_node_phase_mismatch(self):
  def m(o): x=v.load(o['nodes']); x[0]['phase']='INVESTIGATION'; dump(o['nodes'],x)
  self.assert_bad(m)
 def test_15_link_dangling_endpoint(self):
  def m(o): x=v.load(o['links']); x[0]['to_node_id']='TN-999'; dump(o['links'],x)
  self.assert_bad(m)
 def test_16_link_without_evidence(self):
  def m(o): x=v.load(o['links']); x[0]['evidence_ids']=[]; dump(o['links'],x)
  self.assert_bad(m)
 def test_17_missing_closure(self):
  def m(o): x=v.load(o['closures']); x.pop(); dump(o['closures'],x)
  self.assert_bad(m)
 def test_18_duplicate_closure_root(self):
  def m(o): x=v.load(o['closures']); z=dict(x[0]); z['closure_id']='CLO-999'; x.append(z); dump(o['closures'],x)
  self.assert_bad(m)
 def test_19_closed_missing_terminal_type(self):
  def m(o): x=v.load(o['closures']); x[0]['required_terminal_types'].append('TEST'); dump(o['closures'],x)
  self.assert_bad(m)
 def test_20_unreachable_terminal(self):
  def m(o): x=v.load(o['closures']); x[0]['observed_terminal_node_ids']=['TN-015']; dump(o['closures'],x)
  self.assert_bad(m)
 def test_21_unknown_verification_node(self):
  def m(o): x=v.load(o['nodes']); next(r for r in x if r['node_type']=='VERIFICATION_OBLIGATION')['source_native_id']='VOB-999'; dump(o['nodes'],x)
  self.assert_bad(m)
 def test_22_verification_execution_not_pass(self):
  def m(o): x=v.load(o['verification_executions']); next(r for r in x if r['obligation_id']=='VOB-006')['outcome']='FAIL'; dump(o['verification_executions'],x)
  self.assert_bad(m)
 def test_23_contradiction_dangling_artifact(self):
  def m(o): dump(o['contradictions'],[{'contradiction_id':'CON-001','reconciliation_run_id':'REC-duplicate-event-001','artifact_ids':['ART-001','ART-999'],'node_ids':[],'category':'DIGEST_MISMATCH','description':'x','evidence_ids':['VE-001'],'severity':'HIGH','status':'OPEN','resolution':None,'required_route':'INVESTIGATION','blocking':True}])
  self.assert_bad(m)
 def test_24_gap_dangling_node(self):
  def m(o): dump(o['gaps'],[{'gap_id':'GAP-001','reconciliation_run_id':'REC-duplicate-event-001','gap_type':'MISSING_TRACE_LINK','affected_artifact_ids':['ART-001'],'affected_node_ids':['TN-999'],'description':'x','evidence_ids':['VE-001'],'severity':'HIGH','status':'OPEN','required_route':'SYSTEM_MODEL','blocking':True,'resolution':None}])
  self.assert_bad(m)
 def test_25_agent_approval(self):
  def m(o): x=v.load(o['approval']); x['approver_id']=x['reconciler_id']; dump(o['approval'],x)
  self.assert_bad(m)
 def test_26_accepted_risk_mismatch(self):
  def m(o): x=v.load(o['approval']); x['accepted_risk_node_ids']=['TN-008']; dump(o['approval'],x)
  self.assert_bad(m)
 def test_27_bundle_digest_drift(self):
  def m(o): x=v.load(o['result_contract']); x['reconciliation_bundle_digest']='sha256:'+'3'*64; dump(o['result_contract'],x)
  self.assert_bad(m)
 def test_28_result_id_order_drift(self):
  def m(o): x=v.load(o['result_contract']); x['trace_node_ids']=list(reversed(x['trace_node_ids'])); dump(o['result_contract'],x)
  self.assert_bad(m)
 def test_29_output_artifact_digest_drift(self):
  def m(o): x=v.load(o['output']); x['artifact_files']['traceability_links']['digest']='sha256:'+'4'*64; dump(o['output'],x)
  self.assert_bad(m)
 def test_30_output_summary_drift(self):
  def m(o): x=v.load(o['output']); x['traceability_summary']['closed_total']=3; dump(o['output'],x)
  self.assert_bad(m)
 def test_31_output_route_drift(self):
  def m(o): x=v.load(o['output']); x['gate_decision']['next_state']='VERIFICATION'; dump(o['output'],x)
  self.assert_bad(m)
 def test_32_ready_rejects_loopback(self):
  over={'output':ROOT/'examples/valid-output-system-model-loopback.yaml','closures':ROOT/'examples/valid-closure-obligations-system-model-loopback.jsonl','gaps':ROOT/'examples/valid-residual-gaps-system-model-loopback.jsonl','approval':ROOT/'examples/valid-closure-approval-system-model-loopback.yaml','result_contract':ROOT/'examples/valid-reconciliation-result-contract-system-model-loopback.yaml','report':ROOT/'examples/valid-reconciliation-report-system-model-loopback.md'}
  self.assertTrue(v.validate_package(args(over,ready=True)))
if __name__=='__main__': unittest.main()
