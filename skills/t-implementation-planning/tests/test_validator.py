from __future__ import annotations
import json, subprocess, sys, tempfile, unittest, yaml
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
PYTHON=sys.executable
VALIDATOR=ROOT/'validators'/'validate.py'

class ValidatorTests(unittest.TestCase):
    def run_pkg(self, *, output='valid-output-ready.yaml', plans='valid-plan-items.jsonl', deps='valid-dependency-edges.jsonl', coverage='valid-coverage.csv', findings='empty-planning-findings.jsonl', contract='source-valid-approved-solution-contract.yaml', input_file='valid-input.yaml', transition=False):
        cmd=[PYTHON,str(VALIDATOR),'--kind','package',
             '--input',str(ROOT/'examples'/input_file),
             '--output',str(ROOT/'examples'/output),
             '--contract',str(ROOT/'examples'/contract),
             '--critique-output',str(ROOT/'examples'/'source-valid-solution-critique-output.yaml'),
             '--targets',str(ROOT/'examples'/'valid-planning-targets.jsonl'),
             '--plans',str(ROOT/'examples'/plans),
             '--dependencies',str(ROOT/'examples'/deps),
             '--coverage',str(ROOT/'examples'/coverage),
             '--verifications',str(ROOT/'examples'/'valid-verification-plan.jsonl'),
             '--rollbacks',str(ROOT/'examples'/'valid-rollback-plan.jsonl'),
             '--findings',str(ROOT/'examples'/findings),
             '--ledger',str(ROOT/'examples'/'source-valid-evidence-ledger.jsonl'),
             '--elements',str(ROOT/'examples'/'source-valid-model-elements.jsonl'),
             '--relations',str(ROOT/'examples'/'source-valid-model-relations.jsonl')]
        if transition: cmd.append('--require-transition-ready')
        return subprocess.run(cmd,text=True,capture_output=True)

    def run_pkg_paths(self, **overrides):
        defaults={
          'input':ROOT/'examples'/'valid-input.yaml','output':ROOT/'examples'/'valid-output-ready.yaml',
          'contract':ROOT/'examples'/'source-valid-approved-solution-contract.yaml','critique-output':ROOT/'examples'/'source-valid-solution-critique-output.yaml',
          'targets':ROOT/'examples'/'valid-planning-targets.jsonl','plans':ROOT/'examples'/'valid-plan-items.jsonl',
          'dependencies':ROOT/'examples'/'valid-dependency-edges.jsonl','coverage':ROOT/'examples'/'valid-coverage.csv',
          'verifications':ROOT/'examples'/'valid-verification-plan.jsonl','rollbacks':ROOT/'examples'/'valid-rollback-plan.jsonl',
          'findings':ROOT/'examples'/'empty-planning-findings.jsonl','ledger':ROOT/'examples'/'source-valid-evidence-ledger.jsonl',
          'elements':ROOT/'examples'/'source-valid-model-elements.jsonl','relations':ROOT/'examples'/'source-valid-model-relations.jsonl'}
        defaults.update(overrides)
        cmd=[PYTHON,str(VALIDATOR),'--kind','package']
        for k,v in defaults.items(): cmd += ['--'+k,str(v)]
        return subprocess.run(cmd,text=True,capture_output=True)

    def test_all_json_schemas_are_valid(self):
        for p in sorted((ROOT/'schemas').glob('*.json')):
            Draft202012Validator.check_schema(json.loads(p.read_text()))

    def test_transition_ready_example(self):
        r=self.run_pkg(transition=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('transition-ready for PLAN_CRITIQUE',r.stdout)

    def test_investigation_route_is_valid(self):
        r=self.run_pkg(output='valid-output-investigation-route.yaml',findings='valid-findings-investigation-route.jsonl')
        self.assertEqual(r.returncode,0,r.stderr)

    def test_solution_design_route_is_valid(self):
        r=self.run_pkg(output='valid-output-solution-design-route.yaml',plans='invalid-plan-new-semantic-decision.jsonl',findings='valid-findings-solution-design-route.jsonl')
        self.assertEqual(r.returncode,0,r.stderr)

    def test_dependency_cycle_is_rejected(self):
        r=self.run_pkg(deps='invalid-dependency-cycle.jsonl')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('cycle',r.stderr)

    def test_partial_mandatory_coverage_is_rejected(self):
        r=self.run_pkg(coverage='invalid-coverage-partial.csv')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('mandatory target must be FULL',r.stderr)

    def test_dangling_evidence_is_rejected(self):
        r=self.run_pkg(plans='invalid-plan-dangling-evidence.jsonl')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('F-999',r.stderr)

    def test_new_semantic_decision_cannot_use_ready_output(self):
        r=self.run_pkg(plans='invalid-plan-new-semantic-decision.jsonl')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('RETURN_TO_SOLUTION_DESIGN',r.stderr)

    def test_missing_required_rollback_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'plans.jsonl'
            rows=[json.loads(x) for x in (ROOT/'examples'/'valid-plan-items.jsonl').read_text().splitlines() if x.strip()]
            rows[0]['rollback_item_ids']=[]
            p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
            r=self.run_pkg_paths(plans=p)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('rollback is required',r.stderr)

    def test_nonapproved_contract_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'contract.yaml'
            obj=yaml.safe_load((ROOT/'examples'/'source-valid-approved-solution-contract.yaml').read_text())
            obj['status']='PENDING'
            p.write_text(yaml.safe_dump(obj,sort_keys=False))
            r=self.run_pkg_paths(contract=p)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('must be APPROVED by HUMAN',r.stderr)

    def test_source_record_count_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.yaml'
            obj=yaml.safe_load((ROOT/'examples'/'valid-input.yaml').read_text())
            obj['source_artifacts']['evidence_ledger']['record_count']=999
            p.write_text(yaml.safe_dump(obj,sort_keys=False))
            r=self.run_pkg_paths(input=p)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('expected 5',r.stderr)

    def test_unreconciled_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'plans.jsonl'
            rows=[json.loads(x) for x in (ROOT/'examples'/'valid-plan-items.jsonl').read_text().splitlines() if x.strip()]
            rows[0]['affected_files_or_artifacts'].append('src/main/java/example/UnapprovedSemanticAdapter.java')
            p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
            r=self.run_pkg_paths(plans=p)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('unreconciled artifact',r.stderr)

if __name__=='__main__': unittest.main()
