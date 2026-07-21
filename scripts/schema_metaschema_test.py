#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
def main():
    issues=[]; files=sorted(ROOT.rglob('*.schema.json'))
    for path in files:
        try:
            schema=json.loads(path.read_text())
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            issues.append(f'{path.relative_to(ROOT)}: {exc}')
    report={'status':'FAIL' if issues else 'PASS','schemas':len(files),'issues':issues}
    (ROOT/'reports/schema-metaschema-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
