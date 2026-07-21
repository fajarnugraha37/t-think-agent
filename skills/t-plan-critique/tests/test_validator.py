from __future__ import annotations
import json, subprocess, sys, tempfile, unittest, yaml
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
PYTHON=sys.executable
VALIDATOR=ROOT/'validators'/'validate.py'

class ValidatorTests(unittest.TestCase):
    def defaults(self):
        e=ROOT/'examples'
        return {
          'input':e/'valid-input.yaml','output':e/'valid-output-ready.yaml','planning-output':e/'source-valid-planning-output.yaml',
          'targets':e/'source-valid-planning-targets.jsonl','plans':e/'source-valid-plan-items.jsonl','dependencies':e/'source-valid-dependency-edges.jsonl',
          'coverage':e/'source-valid-coverage.csv','verifications':e/'source-valid-verification-plan.jsonl','rollbacks':e/'source-valid-rollback-plan.jsonl',
          'findings':e/'source-empty-planning-findings.jsonl','solution-contract':e/'source-valid-approved-solution-contract.yaml',
          'ledger':e/'source-valid-evidence-ledger.jsonl','elements':e/'source-valid-model-elements.jsonl','relations':e/'source-valid-model-relations.jsonl',
          'assessments':e/'valid-assessments.jsonl','revisions':e/'empty-revision-directives.jsonl','requests':e/'empty-evidence-requests.jsonl',
          'approval':e/'valid-plan-approval.yaml','plan-contract':e/'valid-approved-plan-contract.yaml'}

    def run_pkg(self, transition=False, **overrides):
        d=self.defaults(); d.update(overrides)
        cmd=[PYTHON,str(VALIDATOR),'--kind','package']
        for k,v in d.items(): cmd += ['--'+k,str(v)]
        if transition: cmd.append('--require-transition-ready')
        return subprocess.run(cmd,text=True,capture_output=True)

    def test_all_json_schemas_are_valid(self):
        for p in sorted((ROOT/'schemas').glob('*.json')):
            Draft202012Validator.check_schema(json.loads(p.read_text()))

    def test_transition_ready_example(self):
        r=self.run_pkg(transition=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('transition-ready for IMPLEMENTATION_CHECKLIST',r.stdout)

    def test_plan_revision_route_is_valid(self):
        e=ROOT/'examples'
        r=self.run_pkg(input=e/'valid-input-plan-revision-route.yaml',output=e/'valid-output-plan-revision-route.yaml',assessments=e/'valid-assessments-plan-revision-route.jsonl',revisions=e/'valid-revision-directives-plan-revision-route.jsonl',approval=e/'valid-plan-approval-pending.yaml',**{'plan-contract':e/'valid-pending-plan-contract.yaml'})
        self.assertEqual(r.returncode,0,r.stderr)

    def test_investigation_route_is_valid(self):
        e=ROOT/'examples'
        r=self.run_pkg(input=e/'valid-input-investigation-route.yaml',output=e/'valid-output-investigation-route.yaml',assessments=e/'valid-assessments-investigation-route.jsonl',requests=e/'valid-evidence-requests-investigation-route.jsonl',approval=e/'valid-plan-approval-pending.yaml',**{'plan-contract':e/'valid-pending-plan-contract.yaml'})
        self.assertEqual(r.returncode,0,r.stderr)

    def test_solution_design_route_is_valid(self):
        e=ROOT/'examples'
        r=self.run_pkg(input=e/'valid-input-solution-design-route.yaml',output=e/'valid-output-solution-design-route.yaml',assessments=e/'valid-assessments-solution-design-route.jsonl',revisions=e/'valid-revision-directives-solution-design-route.jsonl',approval=e/'valid-plan-approval-pending.yaml',**{'plan-contract':e/'valid-pending-plan-contract.yaml'})
        self.assertEqual(r.returncode,0,r.stderr)

    def test_dangling_critique_target_is_rejected(self):
        r=self.run_pkg(input=ROOT/'examples'/'invalid-input-dangling-target.yaml')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('PLN-999',r.stderr)

    def test_rejection_without_evidence_is_rejected(self):
        r=self.run_pkg(assessments=ROOT/'examples'/'invalid-assessment-rejection-without-evidence.jsonl')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('REJECTED_WITH_EVIDENCE requires evidence_reviewed',r.stderr)

    def test_ready_output_without_approval_is_rejected(self):
        r=self.run_pkg(output=ROOT/'examples'/'invalid-output-ready-without-approval.yaml')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('approval_readiness',r.stderr)

    def test_agent_self_approval_is_rejected(self):
        r=self.run_pkg(approval=ROOT/'examples'/'invalid-agent-self-approval.yaml')
        self.assertNotEqual(r.returncode,0)
        self.assertIn('cannot approve its own',r.stderr)

    def test_contract_digest_drift_is_rejected(self):
        r=self.run_pkg(**{'plan-contract':ROOT/'examples'/'invalid-contract-digest.yaml'})
        self.assertNotEqual(r.returncode,0)
        self.assertIn('plan_bundle_digest',r.stderr)

    def test_unresolved_revision_cannot_use_ready_output(self):
        e=ROOT/'examples'
        r=self.run_pkg(input=e/'valid-input-plan-revision-route.yaml',output=e/'valid-output-ready.yaml',assessments=e/'valid-assessments-plan-revision-route.jsonl',revisions=e/'valid-revision-directives-plan-revision-route.jsonl',approval=e/'valid-plan-approval-pending.yaml',**{'plan-contract':e/'valid-pending-plan-contract.yaml'})
        self.assertNotEqual(r.returncode,0)
        self.assertIn('RETURN_TO_IMPLEMENTATION_PLAN',r.stderr)

    def test_missing_plan_risk_acceptance_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'approval.yaml'
            obj=yaml.safe_load((ROOT/'examples'/'valid-plan-approval.yaml').read_text())
            obj['accepted_residual_risk_ids']=[]
            p.write_text(yaml.safe_dump(obj,sort_keys=False))
            r=self.run_pkg(approval=p)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('unaccepted plan risks',r.stderr)

    def test_source_record_count_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.yaml'
            obj=yaml.safe_load((ROOT/'examples'/'valid-input.yaml').read_text())
            obj['source_artifacts']['plan_items']['record_count']=999
            p.write_text(yaml.safe_dump(obj,sort_keys=False))
            r=self.run_pkg(input=p)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('expected 8',r.stderr)

    def test_execution_order_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'contract.yaml'
            obj=yaml.safe_load((ROOT/'examples'/'valid-approved-plan-contract.yaml').read_text())
            obj['execution_order'][0],obj['execution_order'][1]=obj['execution_order'][1],obj['execution_order'][0]
            p.write_text(yaml.safe_dump(obj,sort_keys=False))
            r=self.run_pkg(**{'plan-contract':p})
            self.assertNotEqual(r.returncode,0)
            self.assertIn('execution_order',r.stderr)

    def test_missing_assessment_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'assessments.jsonl'; p.write_text('')
            r=self.run_pkg(assessments=p)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('must contain at least one record',r.stderr)

if __name__=='__main__': unittest.main()
