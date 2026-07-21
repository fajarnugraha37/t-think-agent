from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('v',R/'validators/validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class T(unittest.TestCase):
 def b(self):return v.load(R/'examples/valid-input.yaml'),v.load(R/'examples/valid-output.yaml')
 def test_valid(self):i,o=self.b();self.assertEqual([],v.validate(i,o))
 def test_missing_phase(self):i,o=self.b();i['phase_artifacts'].pop();self.assertTrue(v.validate(i,o))
 def test_unsatisfied(self):i,o=self.b();i['acceptance_criteria'][0]['status']='UNSATISFIED';self.assertTrue(v.validate(i,o))
 def test_blocking(self):i,o=self.b();i['open_blocking_findings']=['F-1'];self.assertTrue(v.validate(i,o))
if __name__=='__main__':unittest.main()
