param([ValidateSet("all","opencode","codex","claude","cursor")][string]$Target="all")
python "$PSScriptRoot/doctor.py" --target $Target; exit $LASTEXITCODE
