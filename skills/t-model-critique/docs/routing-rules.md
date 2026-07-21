# Routing Rules

| Condition | Route |
|---|---|
| Human intent or intended behavior is ambiguous | `PROBLEM_ALIGNMENT` |
| Missing actual-system evidence blocks assessment | `INVESTIGATION` |
| Existing evidence is sufficient but model must change | `SYSTEM_MODEL` |
| No model change is required and approval is pending | `MODEL_CRITIQUE` |
| Human approved the reviewed model and all critiques are resolved | `SOLUTION_DESIGN` |
| Invalid references or unsafe package | `NONE` / blocked |
