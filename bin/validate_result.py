#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from tthink_runtime import load_data,validate_delegation,validate_result
p=argparse.ArgumentParser(); p.add_argument('--delegation',type=Path,required=True); p.add_argument('--result',type=Path,required=True); p.add_argument('--boundary',type=Path,required=True); a=p.parse_args()
packet=load_data(a.delegation); errors=validate_delegation(packet); errors+=validate_result(load_data(a.result),packet,load_data(a.boundary))
print(json.dumps({'status':'FAIL' if errors else 'PASS','errors':errors},indent=2)); raise SystemExit(1 if errors else 0)
