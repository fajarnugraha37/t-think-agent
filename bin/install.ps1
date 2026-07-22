param([string[]]$Target=@("all"),[ValidateSet("copy","symlink")][string]$Mode="copy",[switch]$Force)
$Root = Split-Path -Parent $PSScriptRoot
python "$Root/scripts/generate_adapters.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$ArgsList=@(); foreach($t in $Target){$ArgsList += @("--target",$t)}; $ArgsList += @("--mode",$Mode); if($Force){$ArgsList += "--force"}; python "$PSScriptRoot/install.py" @ArgsList; exit $LASTEXITCODE
