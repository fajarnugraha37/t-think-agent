from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('v',R/'validators/validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class T(unittest.TestCase):
 def b(self):return v.load(R/'examples/valid-input.yaml'),v.load(R/'examples/valid-output.yaml')
 def test_valid(self):i,o=self.b();self.assertEqual([],v.validate(i,o))
 def test_missing(self):i,o=self.b();o['results']=[];self.assertTrue(v.validate(i,o))
 def test_failed(self):i,o=self.b();o['results'][0]['status']='FAIL';self.assertTrue(v.validate(i,o))
 def test_command_drift(self):i,o=self.b();o['results'][0]['command']='other';self.assertTrue(v.validate(i,o))
if __name__=='__main__':unittest.main()
