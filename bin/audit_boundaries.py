#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from tthink_runtime import load_data,dump_data,audit_boundaries,validate_schema
p=argparse.ArgumentParser(); p.add_argument('--delegation',type=Path,required=True); p.add_argument('--activity',type=Path,required=True); p.add_argument('--out',type=Path); a=p.parse_args()
report=audit_boundaries(load_data(a.delegation),load_data(a.activity)); schema_errors=validate_schema(report,'boundary-report.schema.json'); report['violations'].extend(schema_errors); report['status']='FAIL' if report['violations'] else 'PASS'
if a.out: a.out.parent.mkdir(parents=True,exist_ok=True); dump_data(a.out,report)
print(json.dumps(report,indent=2)); raise SystemExit(1 if report['status']=='FAIL' else 0)
