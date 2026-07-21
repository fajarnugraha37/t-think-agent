#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from tthink_runtime import load_data,validate_delegation
p=argparse.ArgumentParser(); p.add_argument('--file',type=Path,required=True); a=p.parse_args()
errors=validate_delegation(load_data(a.file)); print(json.dumps({'status':'FAIL' if errors else 'PASS','errors':errors},indent=2)); raise SystemExit(1 if errors else 0)
