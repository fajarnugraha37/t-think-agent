from __future__ import annotations
import subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; V=ROOT/'validators'/'validate.py'; E=ROOT/'examples'
def run(*args): return subprocess.run([sys.executable,str(V),*args],cwd=ROOT,text=True,capture_output=True)
def package(output='valid-output-ready.yaml',ass='valid-assessments.jsonl',inp='valid-input.yaml',req='empty-evidence-requests.jsonl',rev='empty-revision-directives.jsonl',transition=True):
 args=['--kind','package','--input',str(E/inp),'--output',str(E/output),'--assessments',str(E/ass),'--revisions',str(E/rev),'--requests',str(E/req),'--model-output',str(E/'source-valid-output-ready.yaml'),'--elements',str(E/'source-valid-model-elements.jsonl'),'--relations',str(E/'source-valid-model-relations.jsonl'),'--traceability',str(E/'source-valid-traceability-matrix.csv'),'--ledger',str(E/'source-valid-evidence-ledger.jsonl')]
 if transition: args.append('--require-transition-ready')
 return run(*args)
class Tests(unittest.TestCase):
 def test_valid_input(self):
  r=run('--kind','input','--file',str(E/'valid-input.yaml')); self.assertEqual(r.returncode,0,r.stderr)
 def test_ready_package(self):
  r=package(); self.assertEqual(r.returncode,0,r.stderr); self.assertIn('transition-ready',r.stdout)
 def test_valid_investigation_route(self):
  r=package(output='valid-output-investigation-route.yaml',ass='valid-assessments-investigation-route.jsonl',inp='valid-input-investigation-route.yaml',req='valid-evidence-requests-investigation-route.jsonl',transition=False); self.assertEqual(r.returncode,0,r.stderr)
 def test_valid_system_model_route(self):
  r=package(output='valid-output-system-model-route.yaml',ass='valid-assessments-system-model-route.jsonl',inp='valid-input-system-model-route.yaml',rev='valid-revision-directives-system-model-route.jsonl',transition=False); self.assertEqual(r.returncode,0,r.stderr)
 def test_investigation_route_not_change_ready(self):
  r=package(output='valid-output-investigation-route.yaml',ass='valid-assessments-investigation-route.jsonl',inp='valid-input-investigation-route.yaml',req='valid-evidence-requests-investigation-route.jsonl',transition=True); self.assertEqual(r.returncode,1); self.assertIn('not transition-ready',r.stderr)
 def test_reject_without_evidence(self):
  r=package(ass='invalid-assessment-rejection-without-evidence.jsonl'); self.assertEqual(r.returncode,1); self.assertIn('requires evidence_reviewed',r.stderr)
 def test_dangling_target(self):
  r=package(ass='invalid-assessment-dangling-target.jsonl'); self.assertEqual(r.returncode,1); self.assertIn('MDL-999',r.stderr)
 def test_ready_without_approval(self):
  r=package(output='invalid-output-ready-without-approval.yaml'); self.assertEqual(r.returncode,1); self.assertIn('requires APPROVED',r.stderr)
 def test_unassessed_rejected(self):
  r=package(output='invalid-output-unassessed.yaml'); self.assertEqual(r.returncode,1); self.assertIn('expected 0, got 1',r.stderr)
 def test_input_critique_dangling_target(self):
  r=package(inp='invalid-input-dangling-target.yaml'); self.assertEqual(r.returncode,1); self.assertIn('MDL-999',r.stderr)
 def test_individual_assessment(self):
  r=run('--kind','assessment','--file',str(E/'valid-assessments.jsonl')); self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__': unittest.main()
