#!/usr/bin/env python3
from __future__ import annotations
import copy, importlib.util, tempfile, yaml, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v',ROOT/'validators/validate.py'); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
class A: pass
def base(loop=False):
 a=A();
 vals={'input':'valid-input.yaml','bounded_output':'source-valid-bounded-output.yaml','implementation_contract':'source-valid-implementation-result-contract.yaml','checklist_contract':'source-valid-approved-checklist-contract.yaml','checklists':'source-valid-checklist-items.jsonl','executions':'source-valid-execution-records.jsonl','changes':'source-valid-change-records.jsonl','commands':'source-valid-command-results.jsonl','verifications':'source-valid-verification-results.jsonl','rollbacks':'source-valid-rollback-results.jsonl','implementation_findings':'source-valid-implementation-findings.jsonl','repository_before':'source-valid-repository-before.yaml','repository_after':'source-valid-repository-after.yaml','ledger':'source-valid-evidence-ledger.jsonl','evidence_audits':'valid-evidence-audits.jsonl'}
 if not loop: vals.update({'output':'valid-output-ready.yaml','review_checks':'valid-review-checks.jsonl','conformance_results':'valid-conformance-results.jsonl','findings':'empty-review-findings.jsonl','directives':'empty-remediation-directives.jsonl','result_contract':'valid-self-review-result-contract.yaml'})
 else: vals.update({'output':'valid-output-bounded-loopback.yaml','review_checks':'valid-review-checks-bounded-loopback.jsonl','conformance_results':'valid-conformance-results-bounded-loopback.jsonl','findings':'valid-findings-bounded-loopback.jsonl','directives':'valid-directives-bounded-loopback.jsonl','result_contract':'valid-self-review-result-contract-bounded-loopback.yaml'})
 for k,f in vals.items(): setattr(a,k,str(ROOT/'examples'/f))
 a.require_transition_ready=False
 return a
def write(tmp,name,obj,jsonl=False):
 p=Path(tmp)/name
 if jsonl: p.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in obj))
 else: p.write_text(yaml.safe_dump(obj,sort_keys=False))
 return str(p)
def expect(name,fn,valid):
 issues=fn(); ok=(not issues)==valid
 print(('PASS' if ok else 'FAIL')+': '+name+(f' ({len(issues)} issues)' if issues else ''))
 if not ok:
  for i in issues[:5]: print(' ',i)
  raise AssertionError(name)
def main():
 tests=[]
 tests.append(('all schemas valid',lambda: [v.Draft202012Validator.check_schema(json.loads(p.read_text())) for p in (ROOT/'schemas').glob('*.json')] and [],True))
 tests.append(('ready package',lambda:v.validate_package(base()),True))
 tests.append(('bounded loopback',lambda:v.validate_package(base(True)),True))
 with tempfile.TemporaryDirectory() as td:
  # 4 bad source gate
  a=base(); x=v.load(a.bounded_output); x['gate_decision']['status']='BLOCKED'; a.bounded_output=write(td,'bo.yaml',x); tests.append(('reject source gate',lambda a=a:v.validate_package(a),False))
  # 5 missing conformance
  a=base(); x=v.load(a.conformance_results)[:-1]; a.conformance_results=write(td,'c1.jsonl',x,True); tests.append(('reject missing conformance',lambda a=a:v.validate_package(a),False))
  # 6 duplicate conformance
  a=base(); x=v.load(a.conformance_results); x.append(copy.deepcopy(x[0])); x[-1]['conformance_id']='SRCNF-999'; a.conformance_results=write(td,'c2.jsonl',x,True); tests.append(('reject duplicate checklist coverage',lambda a=a:v.validate_package(a),False))
  # 7 digest drift
  a=base(); x=v.load(a.conformance_results); x[0]['source_operation_digest']='sha256:'+'0'*64; a.conformance_results=write(td,'c3.jsonl',x,True); tests.append(('reject operation digest drift',lambda a=a:v.validate_package(a),False))
  # 8 missing dimension
  a=base(); x=v.load(a.review_checks)[:-1]; a.review_checks=write(td,'r1.jsonl',x,True); tests.append(('reject missing review dimension',lambda a=a:v.validate_package(a),False))
  # 9 duplicate dimension
  a=base(); x=v.load(a.review_checks); x[-1]['dimension']=x[0]['dimension']; a.review_checks=write(td,'r2.jsonl',x,True); tests.append(('reject duplicate review dimension',lambda a=a:v.validate_package(a),False))
  # 10 empty evidence
  a=base(); x=v.load(a.review_checks); x[0]['evidence_refs']=[]; a.review_checks=write(td,'r3.jsonl',x,True); tests.append(('reject evidence-free check',lambda a=a:v.validate_package(a),False))
  # 11 fail without finding
  a=base(); x=v.load(a.review_checks); x[0]['outcome']='FAIL'; a.review_checks=write(td,'r4.jsonl',x,True); tests.append(('reject failed check without finding',lambda a=a:v.validate_package(a),False))
  # 12 dangling target
  a=base(True); x=v.load(a.findings); x[0]['target_ids'].append('CHK-999'); a.findings=write(td,'f1.jsonl',x,True); tests.append(('reject dangling finding target',lambda a=a:v.validate_package(a),False))
  # 13 finding no evidence
  a=base(True); x=v.load(a.findings); x[0]['evidence_refs']=[]; a.findings=write(td,'f2.jsonl',x,True); tests.append(('reject evidence-free finding',lambda a=a:v.validate_package(a),False))
  # 14 wrong mechanical route
  a=base(True); x=v.load(a.findings); x[0]['required_route']='IMPLEMENTATION_PLAN'; a.findings=write(td,'f3.jsonl',x,True); tests.append(('reject wrong mechanical route',lambda a=a:v.validate_package(a),False))
  # 15 missing directive
  a=base(True); a.directives=str(ROOT/'examples/empty-remediation-directives.jsonl'); tests.append(('reject missing remediation directive',lambda a=a:v.validate_package(a),False))
  # 16 applied directive
  a=base(True); x=v.load(a.directives); x[0]['applied']=True; a.directives=write(td,'d1.jsonl',x,True); tests.append(('reject applied directive in review',lambda a=a:v.validate_package(a),False))
  # 17 bundle digest drift
  a=base(); x=v.load(a.result_contract); x['self_review_bundle_digest']='sha256:'+'0'*64; a.result_contract=write(td,'rc1.yaml',x); tests.append(('reject result bundle digest drift',lambda a=a:v.validate_package(a),False))
  # 18 output summary drift
  a=base(); x=v.load(a.output); x['review_summary']['passed']-=1; a.output=write(td,'o1.yaml',x); tests.append(('reject output summary drift',lambda a=a:v.validate_package(a),False))
  # 19 repository drift
  a=base(); x=v.load(a.repository_after); x['tree_digest']='sha256:'+'1'*64; a.repository_after=write(td,'repo.yaml',x); tests.append(('reject repository drift',lambda a=a:v.validate_package(a),False))
  # 20 ready requires transition flag passes
  a=base(); a.require_transition_ready=True; tests.append(('transition-ready flag',lambda a=a:v.validate_package(a),True))
  for t in tests: expect(*t)
 print(f'{len(tests)}/{len(tests)} tests passed')
if __name__=='__main__': main()
