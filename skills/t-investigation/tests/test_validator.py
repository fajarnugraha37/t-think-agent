import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VALIDATOR=ROOT/'validators'/'validate.py'

def run(*args):
    return subprocess.run([sys.executable,str(VALIDATOR),*map(str,args)],cwd=ROOT,text=True,capture_output=True)

class InvestigationValidatorTests(unittest.TestCase):
    def test_valid_input(self):
        r=run('--kind','input','--file',ROOT/'examples'/'valid-input.yaml')
        self.assertEqual(r.returncode,0,r.stderr)

    def test_valid_ledger(self):
        r=run('--kind','ledger','--file',ROOT/'examples'/'valid-evidence-ledger.jsonl')
        self.assertEqual(r.returncode,0,r.stderr)

    def test_valid_transition_ready_output(self):
        r=run('--kind','output','--file',ROOT/'examples'/'valid-output-ready.yaml','--ledger',ROOT/'examples'/'valid-evidence-ledger.jsonl','--require-transition-ready')
        self.assertEqual(r.returncode,0,r.stderr)

    def test_reject_context_hint_as_system_fact(self):
        r=run('--kind','ledger','--file',ROOT/'examples'/'invalid-ledger-context-as-fact.jsonl')
        self.assertEqual(r.returncode,1)
        self.assertIn('DIRECT ACTUAL_SYSTEM',r.stderr)

    def test_reject_premature_transition(self):
        r=run('--kind','output','--file',ROOT/'examples'/'invalid-output-premature-ready.yaml','--ledger',ROOT/'examples'/'valid-evidence-ledger.jsonl','--require-transition-ready')
        self.assertEqual(r.returncode,1)
        self.assertIn('required dimension is incomplete',r.stderr)

    def test_reject_unknown_inference_reference(self):
        records=(ROOT/'examples'/'valid-evidence-ledger.jsonl').read_text().splitlines()
        obj=json.loads(records[3]); obj['supporting_claim_ids']=['F-404']
        records[3]=json.dumps(obj)
        with tempfile.NamedTemporaryFile('w',suffix='.jsonl',delete=False) as f:
            f.write('\n'.join(records)+'\n'); name=f.name
        r=run('--kind','ledger','--file',name)
        self.assertEqual(r.returncode,1)
        self.assertIn('unknown claim ID',r.stderr)

    def test_reject_ledger_count_mismatch(self):
        text=(ROOT/'examples'/'valid-output-ready.yaml').read_text()
        text=text.replace('record_count: 5','record_count: 99')
        with tempfile.NamedTemporaryFile('w',suffix='.yaml',delete=False) as f:
            f.write(text); name=f.name
        r=run('--kind','output','--file',name,'--ledger',ROOT/'examples'/'valid-evidence-ledger.jsonl')
        self.assertEqual(r.returncode,1)
        self.assertIn('expected 5 from ledger',r.stderr)

if __name__=='__main__': unittest.main()
