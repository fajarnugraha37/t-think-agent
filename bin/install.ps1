param([string[]]$Target=@("all"),[ValidateSet("copy","symlink")][string]$Mode="copy",[switch]$Force)
$ArgsList=@(); foreach($t in $Target){$ArgsList += @("--target",$t)}; $ArgsList += @("--mode",$Mode); if($Force){$ArgsList += "--force"}; python "$PSScriptRoot/install.py" @ArgsList; exit $LASTEXITCODE
