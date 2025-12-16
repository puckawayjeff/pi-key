# Monitor the CircuitPython serial console on Windows
# Usage: ./monitor.ps1

# --- Configuration ---
$TargetPort = "COM3"  # Change this to your RP2040's COM port
$BaudRate = 115200
# ---------------------

# 1. Check if the Serial Port exists
$AvailablePorts = [System.IO.Ports.SerialPort]::GetPortNames()

if ($AvailablePorts -notcontains $TargetPort) {
    Write-Host "❌ Error: Serial port '$TargetPort' not found." -ForegroundColor Red
    Write-Host "   Available ports: $($AvailablePorts -join ', ')" -ForegroundColor Gray
    Write-Host "   Make sure the RP2040 is connected." -ForegroundColor Gray
    exit 1
}

Write-Host "📡 Connecting to CircuitPython console on $TargetPort..." -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to exit." -ForegroundColor Gray
Write-Host ""

# 2. Create and Open the Serial Connection
try {
    $Port = New-Object System.IO.Ports.SerialPort $TargetPort, $BaudRate, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One
    $Port.Open()
}
catch {
    Write-Host "❌ Error opening port: $_" -ForegroundColor Red
    exit 1
}

# 3. Read Loop (The "Monitor" phase)
#    This loops continuously, reading data from the device and printing it to the console.
try {
    while ($true) {
        if ($Port.BytesToRead -gt 0) {
            $Data = $Port.ReadExisting()
            [System.Console]::Write($Data)
        }
        
        # Brief sleep to prevent high CPU usage
        Start-Sleep -Milliseconds 10
    }
}
finally {
    # Ensure the port closes cleanly if the script is interrupted
    if ($Port.IsOpen) {
        $Port.Close()
        Write-Host "`n🔌 Connection closed." -ForegroundColor Yellow
    }
}
