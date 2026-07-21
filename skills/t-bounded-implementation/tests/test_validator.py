from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('v',R/'validators/validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class T(unittest.TestCase):
 def b(self):return v.load(R/'examples/valid-input.yaml'),v.load(R/'examples/valid-output.yaml')
 def test_valid(self):i,o=self.b();self.assertEqual([],v.validate(i,o))
 def test_unapproved(self):i,o=self.b();o['source_changes']=['other/x'];self.assertTrue(v.validate(i,o))
 def test_missing_task(self):i,o=self.b();o['task_results']=[];self.assertTrue(v.validate(i,o))
 def test_semantic_decision(self):i,o=self.b();o['new_semantic_decision']=True;self.assertTrue(v.validate(i,o))
if __name__=='__main__':unittest.main()
