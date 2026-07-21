from __future__ import annotations
import subprocess, sys, tempfile, yaml
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
VAL=ROOT/'validators'/'validate.py'
E=ROOT/'examples'

class ValidatorTests(unittest.TestCase):
 def base(self):
  return {
   '--input':E/'valid-input.yaml','--output':E/'valid-output-ready.yaml','--assessments':E/'valid-assessments.jsonl',
   '--revisions':E/'empty-revision-directives.jsonl','--requests':E/'empty-evidence-requests.jsonl',
   '--approval':E/'valid-decision-approval.yaml','--contract':E/'valid-approved-solution-contract.yaml',
   '--design-output':E/'source-valid-solution-design-output.yaml','--options':E/'source-valid-options.jsonl',
   '--coverage':E/'source-valid-coverage.csv','--decision':E/'source-valid-decision.yaml','--dominance':E/'source-valid-dominance.yaml',
   '--ledger':E/'source-valid-evidence-ledger.jsonl','--elements':E/'source-valid-model-elements.jsonl','--relations':E/'source-valid-model-relations.jsonl'}
 def runpkg(self,over=None,transition=False):
  args=[sys.executable,str(VAL),'--kind','package']; data=self.base(); data.update(over or {})
  for k,v in data.items(): args += [k,str(v)]
  if transition: args.append('--require-transition-ready')
  return subprocess.run(args,text=True,capture_output=True)
 def test_transition_ready_package(self):
  r=self.runpkg(transition=True); self.assertEqual(r.returncode,0,r.stderr); self.assertIn('transition-ready',r.stdout)
 def test_investigation_route(self):
  r=self.runpkg({'--input':E/'valid-input-investigation-route.yaml','--output':E/'valid-output-investigation-route.yaml','--assessments':E/'valid-assessments-investigation-route.jsonl','--requests':E/'valid-evidence-requests-investigation-route.jsonl','--approval':E/'valid-decision-approval-pending.yaml','--contract':E/'valid-pending-solution-contract.yaml'})
  self.assertEqual(r.returncode,0,r.stderr)
 def test_investigation_route_not_transition_ready(self):
  r=self.runpkg({'--input':E/'valid-input-investigation-route.yaml','--output':E/'valid-output-investigation-route.yaml','--assessments':E/'valid-assessments-investigation-route.jsonl','--requests':E/'valid-evidence-requests-investigation-route.jsonl','--approval':E/'valid-decision-approval-pending.yaml','--contract':E/'valid-pending-solution-contract.yaml'},transition=True)
  self.assertNotEqual(r.returncode,0); self.assertIn('not transition-ready',r.stderr)
 def test_solution_design_route(self):
  r=self.runpkg({'--input':E/'valid-input-solution-design-route.yaml','--output':E/'valid-output-solution-design-route.yaml','--assessments':E/'valid-assessments-solution-design-route.jsonl','--revisions':E/'valid-revision-directives-solution-design-route.jsonl','--approval':E/'valid-decision-approval-pending.yaml','--contract':E/'valid-pending-solution-contract.yaml'})
  self.assertEqual(r.returncode,0,r.stderr)
 def test_dangling_target_rejected(self):
  r=self.runpkg({'--input':E/'invalid-input-dangling-target.yaml'}); self.assertNotEqual(r.returncode,0); self.assertIn('unknown target',r.stderr)
 def test_rejection_without_evidence_rejected(self):
  r=self.runpkg({'--assessments':E/'invalid-assessment-rejection-without-evidence.jsonl'}); self.assertNotEqual(r.returncode,0); self.assertIn('requires evidence_reviewed',r.stderr)
 def test_missing_risk_acceptance_rejected(self):
  r=self.runpkg({'--approval':E/'invalid-approval-missing-risk.yaml'}); self.assertNotEqual(r.returncode,0); self.assertIn('missing required risks',r.stderr)
 def test_contract_semantic_drift_rejected(self):
  r=self.runpkg({'--contract':E/'invalid-contract-semantic-drift.yaml'}); self.assertNotEqual(r.returncode,0); self.assertIn('must exactly match selected option',r.stderr)
 def test_ready_summary_without_approval_rejected(self):
  r=self.runpkg({'--output':E/'invalid-output-ready-without-approval.yaml'}); self.assertNotEqual(r.returncode,0); self.assertIn('must summarize decision approval exactly',r.stderr)
 def test_unassessed_critique_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'empty.jsonl'; p.write_text('',encoding='utf-8')
   r=self.runpkg({'--assessments':p}); self.assertNotEqual(r.returncode,0); self.assertIn('must contain at least one record',r.stderr)
 def test_agent_cannot_fake_human_selection(self):
  with tempfile.TemporaryDirectory() as td:
   d=yaml.safe_load((E/'valid-decision-approval.yaml').read_text()); d['approved_by']='solution-critique-skill'
   p=Path(td)/'approval.yaml'; p.write_text(yaml.safe_dump(d,sort_keys=False))
   # Schema cannot identify every agent name, but contract binding makes unilateral mutation visible.
   r=self.runpkg({'--approval':p}); self.assertNotEqual(r.returncode,0); self.assertIn('must match human approval',r.stderr)
 def test_source_gate_must_be_ready(self):
  with tempfile.TemporaryDirectory() as td:
   d=yaml.safe_load((E/'source-valid-solution-design-output.yaml').read_text()); d['gate_decision']['status']='BLOCKED'; d['gate_decision']['next_state']='SOLUTION_DESIGN'
   p=Path(td)/'design.yaml'; p.write_text(yaml.safe_dump(d,sort_keys=False))
   r=self.runpkg({'--design-output':p}); self.assertNotEqual(r.returncode,0); self.assertIn('must be READY_FOR_SOLUTION_CRITIQUE',r.stderr)

if __name__=='__main__': unittest.main()
