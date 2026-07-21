param([switch]$RestoreBackups)
$ArgsList=@(); if($RestoreBackups){$ArgsList += "--restore-backups"}; python "$PSScriptRoot/uninstall.py" @ArgsList; exit $LASTEXITCODE
