param(
    [string]$Action = "list",
    [string]$Match = ""
)

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty,
    "USART HMI(C:\Users\aziz\Desktop\sk1-hmi\hmi\sk1-hmi.HMI)")
$win = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $cond)
if ($null -eq $win) {
    Write-Output "WINDOW NOT FOUND"
    exit 1
}
Write-Output "WINDOW FOUND: $($win.Current.Name)"

$all = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants,
    [System.Windows.Automation.Condition]::TrueCondition)

Write-Output "descendants: $($all.Count)"

$found = @()
foreach ($e in $all) {
    try {
        $n = $e.Current.Name
        $ct = $e.Current.ControlType.ProgrammaticName
        if ([string]::IsNullOrWhiteSpace($n)) { continue }
        if ($Match -ne "" -and $n -notmatch $Match) { continue }
        if ($ct -match "Button|MenuItem|ToolBar|TabItem|MenuBar") {
            $found += "$ct | $n"
        }
    } catch {}
}

if ($Action -eq "list") {
    $found | Select-Object -Unique
} elseif ($Action -eq "invoke") {
    $target = $null
    foreach ($e in $all) {
        try {
            if ($e.Current.Name -eq $Match) { $target = $e; break }
        } catch {}
    }
    if ($null -eq $target) {
        Write-Output "TARGET NOT FOUND: $Match"
        $found | Select-Object -Unique
        exit 2
    }
    Write-Output "invoking: $($target.Current.Name) [$($target.Current.ControlType.ProgrammaticName)]"
    try {
        $pat = $target.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
        $pat.Invoke()
        Write-Output "INVOKED"
    } catch {
        Write-Output "INVOKE FAILED: $($_.Exception.Message)"
        try {
            $target.SetFocus()
            Write-Output "focused instead"
        } catch { Write-Output "focus failed" }
    }
}
