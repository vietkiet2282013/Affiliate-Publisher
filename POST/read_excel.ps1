$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

function Read-Xlsx($path) {
    Write-Host "=== $path ==="
    $wb = $excel.Workbooks.Open($path)
    $sheet = $wb.Sheets.Item(1)
    $used = $sheet.UsedRange
    $rows = $used.Rows.Count
    $cols = $used.Columns.Count
    for ($r = 1; $r -le $rows; $r++) {
        $rowVal = @()
        for ($c = 1; $c -le $cols; $c++) {
            $rowVal += $sheet.Cells.Item($r, $c).Text
        }
        Write-Host ($rowVal -join " | ")
    }
    $wb.Close($false)
}

Read-Xlsx "C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\YouTube\Tập 3.xlsx"
Read-Xlsx "C:\Affiliate\Góc Tập Luyện\Link customed\YouTube\Tập 3.xlsx"
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
