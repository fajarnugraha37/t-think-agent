from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('v',R/'validators/validate.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class T(unittest.TestCase):
 def base(self):return v.load(R/'examples/valid-input.yaml'),v.load(R/'examples/valid-output.yaml')
 def test_valid(self):i,o=self.base();self.assertEqual([],v.validate(i,o))
 def test_identity(self):i,o=self.base();o['invocation_id']='X';self.assertTrue(v.validate(i,o))
 def test_missing_category(self):i,o=self.base();o['checks'].pop();self.assertTrue(v.validate(i,o))
 def test_fail_without_finding(self):i,o=self.base();o['checks'][0]['status']='FAIL';o['status']='CHANGES_REQUIRED';o['recommended_route']='BOUNDED_IMPLEMENTATION';self.assertTrue(v.validate(i,o))
 def test_pass_with_finding(self):i,o=self.base();o['findings']=[{'finding_id':'FND-001','severity':'HIGH','category':o['checks'][0]['category'],'summary':'Material problem exists','evidence_refs':['e'],'required_route':'BOUNDED_IMPLEMENTATION'}];self.assertTrue(v.validate(i,o))
 def test_fresh_context(self):i,o=self.base();o['context_fresh']=False;self.assertTrue(v.validate(i,o))
if __name__=='__main__':unittest.main()
