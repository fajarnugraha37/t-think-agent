#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SKILLS=ROOT/'skills';REPORTS=ROOT/'reports'
SIMPLE={'t-implementation-blueprint','t-blueprint-critique','t-bounded-implementation','t-implementation-review','t-self-review','t-technical-review','t-security-review','t-breaking-review','t-verification','t-reconciliation'}
COMMANDS={
 't-problem-alignment':{'validate':[['python3','validators/validate.py','--kind','input','--file','examples/valid-input.yaml'],['python3','validators/validate.py','--kind','output','--file','examples/valid-output-approved.yaml','--require-transition-ready']],'test':[['python3','-m','unittest','discover','-s','tests','-v']]},
 't-investigation':{'validate':[['make','validate']],'test':[['make','test']]},'t-system-modeling':{'validate':[['make','validate']],'test':[['make','test']]},'t-model-critique':{'validate':[['make','validate']],'test':[['make','test']]},
 't-solution-design':{'validate':[['make','validate-transition'],['make','validate-single']],'test':[['make','test']]},'t-solution-critique':{'validate':[['make','schemas'],['make','validate-example']],'test':[['make','test']]},
 't-implementation-planning':{'validate':[['make','schemas'],['make','validate-example'],['make','validate-routes']],'test':[['make','test']]},'t-plan-critique':{'validate':[['make','validate-schemas'],['make','validate-example']],'test':[['make','test']]},
 't-checklist-builder':{'validate':[['make','validate']],'test':[['make','test']]},'t-checklist-critique':{'validate':[['make','schema'],['make','validate'],['make','validate-routes']],'test':[['make','test']]}}
for name in SIMPLE:COMMANDS[name]={'validate':[['make','validate']],'test':[['make','test']]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['validate','test'],required=True);p.add_argument('--skill',action='append');p.add_argument('--timeout',type=int,default=600);p.add_argument('--report-name');a=p.parse_args();selected=a.skill or sorted(COMMANDS);unknown=sorted(set(selected)-set(COMMANDS))
 if unknown:print(f'Unknown skills: {unknown}',file=sys.stderr);return 2
 REPORTS.mkdir(exist_ok=True);results=[];failed=False
 for skill in selected:
  for command in COMMANDS[skill][a.mode]:
   print(f'[{a.mode}] {skill}: {" ".join(command)}',flush=True);start=time.monotonic();proc=subprocess.run(command,cwd=SKILLS/skill,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=a.timeout);print(proc.stdout,end='');results.append({'skill':skill,'mode':a.mode,'command':command,'exit_code':proc.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'output':proc.stdout})
   if proc.returncode:failed=True;break
  if failed:break
 report=REPORTS/(a.report_name or f'{a.mode}-report.json');report.write_text(json.dumps({'status':'FAIL' if failed else 'PASS','results':results},indent=2)+'\n');print(f'{a.mode.upper()} {"FAIL" if failed else "PASS"}: {len(results)} command(s) across {len(set(x["skill"] for x in results))} skill(s)');return 1 if failed else 0
if __name__=='__main__':raise SystemExit(main())
