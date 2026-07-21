from __future__ import annotations
import importlib.util, json, tempfile, unittest, yaml
from pathlib import Path
from types import SimpleNamespace
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checklist_validator',ROOT/'validators'/'validate.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class Tests(unittest.TestCase):
    def args(self,**o):
        d={
          'input':'valid-input.yaml','output':'valid-output-ready.yaml','plan_contract':'source-valid-approved-plan-contract.yaml',
          'plan_critique_output':'source-valid-plan-critique-output.yaml','planning_output':'source-valid-planning-output.yaml',
          'targets':'source-valid-planning-targets.jsonl','plans':'source-valid-plan-items.jsonl',
          'plan_dependencies':'source-valid-plan-dependencies.jsonl','plan_coverage':'source-valid-plan-coverage.csv',
          'verifications':'source-valid-verification-plan.jsonl','rollbacks':'source-valid-rollback-plan.jsonl',
          'planning_findings':'source-empty-planning-findings.jsonl','solution_contract':'source-valid-approved-solution-contract.yaml',
          'ledger':'source-valid-evidence-ledger.jsonl','elements':'source-valid-model-elements.jsonl','relations':'source-valid-model-relations.jsonl',
          'checklists':'valid-checklist-items.jsonl','dependencies':'valid-checklist-dependencies.jsonl',
          'coverage':'valid-checklist-coverage.csv','batches':'valid-execution-batches.jsonl','findings':'empty-checklist-findings.jsonl',
          'require_transition_ready':False}
        d.update(o)
        for k,v in list(d.items()):
            if k!='require_transition_ready' and not isinstance(v,Path): d[k]=ROOT/'examples'/v
        return SimpleNamespace(**d)
    def validate(self,**o): return mod.validate_package(self.args(**o))
    def messages(self,issues): return '\n'.join(str(x) for x in issues)

    def test_01_schemas(self):
        for p in (ROOT/'schemas').glob('*.json'): Draft202012Validator.check_schema(json.loads(p.read_text()))
    def test_02_transition_ready(self):
        self.assertEqual([],self.validate(require_transition_ready=True))
    def test_03_investigation_route(self):
        self.assertEqual([],self.validate(output='valid-output-investigation-route.yaml',findings='valid-findings-investigation-route.jsonl'))
    def test_04_implementation_plan_route(self):
        self.assertEqual([],self.validate(output='valid-output-implementation-plan-route.yaml',findings='valid-findings-implementation-plan-route.jsonl'))
    def test_05_cycle_rejected(self):
        m=self.messages(self.validate(dependencies='invalid-checklist-dependency-cycle.jsonl')); self.assertIn('cycle',m)
    def test_06_partial_coverage_rejected(self):
        m=self.messages(self.validate(coverage='invalid-checklist-coverage-partial.csv')); self.assertIn('must be FULL',m)
    def test_07_duplicate_coverage_rejected(self):
        m=self.messages(self.validate(coverage='invalid-checklist-coverage-duplicate.csv')); self.assertIn('must be FULL',m)
    def test_08_dangling_verification_rejected(self):
        m=self.messages(self.validate(checklists='invalid-checklist-dangling-verification.jsonl')); self.assertIn('TST-999',m)
    def test_09_semantic_decision_rejected(self):
        m=self.messages(self.validate(checklists='invalid-checklist-new-semantic-decision.jsonl')).lower(); self.assertIn('semantic',m)
    def test_10_source_operation_drift_rejected(self):
        m=self.messages(self.validate(checklists='invalid-checklist-source-operation-drift.jsonl')).lower(); self.assertIn('source operation',m)
    def test_11_batch_drift_rejected(self):
        m=self.messages(self.validate(batches='invalid-execution-batches-drift.jsonl')).lower(); self.assertIn('batches',m)
    def test_12_pending_contract_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'c.yaml'; x=yaml.safe_load((ROOT/'examples/source-valid-approved-plan-contract.yaml').read_text()); x['status']='PENDING'; p.write_text(yaml.safe_dump(x,sort_keys=False))
            self.assertIn('APPROVED',self.messages(self.validate(plan_contract=p)))
    def test_13_bundle_digest_drift_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'c.yaml'; x=yaml.safe_load((ROOT/'examples/source-valid-approved-plan-contract.yaml').read_text()); x['plan_bundle_digest']='sha256:'+'0'*64; p.write_text(yaml.safe_dump(x,sort_keys=False))
            self.assertIn('expected sha256:',self.messages(self.validate(plan_contract=p)))
    def test_14_source_count_drift_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'i.yaml'; x=yaml.safe_load((ROOT/'examples/valid-input.yaml').read_text()); x['source_artifacts']['plan_items']['record_count']=999; p.write_text(yaml.safe_dump(x,sort_keys=False))
            self.assertIn('expected 8',self.messages(self.validate(input=p)))
    def test_15_scope_expansion_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'c.jsonl'; rows=[json.loads(x) for x in (ROOT/'examples/valid-checklist-items.jsonl').read_text().splitlines() if x.strip()]; rows[0]['scope']['files_or_artifacts'].append('unapproved.file'); p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
            self.assertIn('scope expansion',self.messages(self.validate(checklists=p)))
    def test_16_output_count_drift_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'o.yaml'; x=yaml.safe_load((ROOT/'examples/valid-output-ready.yaml').read_text()); x['artifact_files']['checklist_items']['record_count']=999; p.write_text(yaml.safe_dump(x,sort_keys=False))
            self.assertIn('expected 17',self.messages(self.validate(output=p)))

if __name__=='__main__': unittest.main()
