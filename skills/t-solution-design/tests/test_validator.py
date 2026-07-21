import subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'validators'/'validate.py'
E=ROOT/'examples'
BASE=[sys.executable,str(V),'--kind','package','--input',str(E/'valid-input.yaml'),'--critique-output',str(E/'source-valid-model-critique-output.yaml'),'--elements',str(E/'source-valid-model-elements.jsonl'),'--relations',str(E/'source-valid-model-relations.jsonl'),'--ledger',str(E/'source-valid-evidence-ledger.jsonl')]

def run(extra,ok=True):
 p=subprocess.run(BASE+extra,capture_output=True,text=True)
 if ok and p.returncode!=0: raise AssertionError(p.stderr)
 if not ok and p.returncode==0: raise AssertionError('expected failure')
 return p

class ValidatorTests(unittest.TestCase):
 def test_valid_multi_option_transition(self):
  run(['--output',str(E/'valid-output.yaml'),'--options',str(E/'valid-options.jsonl'),'--coverage',str(E/'valid-coverage.csv'),'--decision',str(E/'valid-decision.yaml'),'--dominance',str(E/'valid-dominance.yaml'),'--require-transition-ready'])
 def test_valid_single_option_with_dominance(self):
  run(['--output',str(E/'single-valid-output.yaml'),'--options',str(E/'single-valid-options.jsonl'),'--coverage',str(E/'single-valid-coverage.csv'),'--decision',str(E/'single-valid-decision.yaml'),'--dominance',str(E/'single-valid-dominance.yaml'),'--require-transition-ready'])
 def test_missing_coverage_row_rejected(self):
  run(['--output',str(E/'invalid-output-premature-ready.yaml'),'--options',str(E/'valid-options.jsonl'),'--coverage',str(E/'invalid-coverage-missing-row.csv'),'--decision',str(E/'valid-decision.yaml'),'--dominance',str(E/'valid-dominance.yaml')],False)
 def test_duplicate_semantic_options_rejected(self):
  run(['--output',str(E/'valid-output.yaml'),'--options',str(E/'invalid-options-duplicate.jsonl'),'--coverage',str(E/'valid-coverage.csv'),'--decision',str(E/'valid-decision.yaml'),'--dominance',str(E/'valid-dominance.yaml')],False)
 def test_single_option_without_dominance_rejected(self):
  run(['--output',str(E/'single-valid-output.yaml'),'--options',str(E/'single-valid-options.jsonl'),'--coverage',str(E/'single-valid-coverage.csv'),'--decision',str(E/'single-valid-decision.yaml'),'--dominance',str(E/'valid-dominance.yaml')],False)
 def test_blocking_assumption_prevents_ready(self):
  run(['--output',str(E/'single-valid-output.yaml'),'--options',str(E/'invalid-options-blocking-assumption.jsonl'),'--coverage',str(E/'single-valid-coverage.csv'),'--decision',str(E/'single-valid-decision.yaml'),'--dominance',str(E/'single-valid-dominance.yaml')],False)
 def test_dangling_evidence_rejected(self):
  p=E/'tmp-dangling.jsonl'; text=(E/'single-valid-options.jsonl').read_text().replace('"F-001"','"F-999"',1); p.write_text(text)
  try: run(['--output',str(E/'single-valid-output.yaml'),'--options',str(p),'--coverage',str(E/'single-valid-coverage.csv'),'--decision',str(E/'single-valid-decision.yaml'),'--dominance',str(E/'single-valid-dominance.yaml')],False)
  finally: p.unlink(missing_ok=True)
 def test_approved_decision_schema_rejected(self):
  p=E/'tmp-approved.yaml'; p.write_text((E/'valid-decision.yaml').read_text().replace('status: DRAFT','status: APPROVED',1))
  try: run(['--output',str(E/'valid-output.yaml'),'--options',str(E/'valid-options.jsonl'),'--coverage',str(E/'valid-coverage.csv'),'--decision',str(p),'--dominance',str(E/'valid-dominance.yaml')],False)
  finally: p.unlink(missing_ok=True)
 def test_output_count_mismatch_rejected(self):
  p=E/'tmp-count.yaml'; p.write_text((E/'valid-output.yaml').read_text().replace('record_count: 6','record_count: 5',1))
  try: run(['--output',str(p),'--options',str(E/'valid-options.jsonl'),'--coverage',str(E/'valid-coverage.csv'),'--decision',str(E/'valid-decision.yaml'),'--dominance',str(E/'valid-dominance.yaml')],False)
  finally: p.unlink(missing_ok=True)
 def test_individual_schemas(self):
  for kind,file in [('input','valid-input.yaml'),('output','valid-output.yaml'),('option','valid-options.jsonl'),('coverage','valid-coverage.csv'),('decision','valid-decision.yaml'),('dominance','valid-dominance.yaml')]:
   p=subprocess.run([sys.executable,str(V),'--kind',kind,'--file',str(E/file)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr)

if __name__=='__main__': unittest.main()
