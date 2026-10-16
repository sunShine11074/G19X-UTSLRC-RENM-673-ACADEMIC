# Recalcula un libro con Excel (instancia propia, invisible) y lo guarda en su lugar.
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File recalc_excel.ps1 <ruta.xlsx>
# Imprime JSON: ruta, fórmulas con error (#DIV/0!, #N/A, #NAME?, #REF!, #VALUE!, #NUM!, #NULL!).
param([Parameter(Mandatory = $true)][string]$Ruta)
$ErrorActionPreference = 'Stop'
$ruta = (Resolve-Path $Ruta).Path
$xl = New-Object -ComObject Excel.Application
try {
    $xl.Visible = $false
    $xl.DisplayAlerts = $false
    $xl.ScreenUpdating = $false
    $wb = $xl.Workbooks.Open($ruta, 0, $false)
    $xl.CalculateFull()
    $errores = @()
    foreach ($ws in $wb.Worksheets) {
        $usado = $ws.UsedRange
        foreach ($celda in $usado.Cells) {
            if ($celda.HasFormula -and ($celda.Text -match '^#(DIV/0!|N/A|NAME\?|REF!|VALUE!|NUM!|NULL!|SPILL!|CALC!)')) {
                $errores += ('{0}!{1}: {2}' -f $ws.Name, $celda.Address($false, $false), $celda.Text)
            }
        }
    }
    $wb.Save()
    $wb.Close($false)
    [pscustomobject]@{ ruta = $ruta; errores = $errores.Count; detalle = ($errores | Select-Object -First 50) } | ConvertTo-Json -Compress
}
finally {
    $xl.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
