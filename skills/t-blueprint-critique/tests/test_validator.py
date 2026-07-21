from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('v',R/'validators/validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class T(unittest.TestCase):
 def base(self):return v.load(R/'examples/valid-input.yaml'),v.load(R/'examples/valid-output.yaml')
 def test_valid(self):i,o=self.base();self.assertEqual([],v.validate(i,o))
 def test_missing_track(self):i,o=self.base();i['tracks'].pop();o['tracks']=i['tracks'];self.assertTrue(v.validate(i,o))
 def test_duplicate_invocation(self):i,o=self.base();i['tracks'][1]['invocation_id']=i['tracks'][0]['invocation_id'];o['tracks']=i['tracks'];self.assertTrue(v.validate(i,o))
 def test_wrong_agent(self):i,o=self.base();i['tracks'][0]['agent']='t-wrong';o['tracks']=i['tracks'];self.assertTrue(v.validate(i,o))
 def test_invalid_success_status(self):i,o=self.base();i['tracks'][0]['status']='PASS';o['tracks']=i['tracks'];self.assertTrue(v.validate(i,o))
 def test_failure_blocks(self):i,o=self.base();i['tracks'][0]['status']='CHANGES_REQUIRED';o['tracks']=i['tracks'];self.assertTrue(v.validate(i,o))
if __name__=='__main__':unittest.main()
