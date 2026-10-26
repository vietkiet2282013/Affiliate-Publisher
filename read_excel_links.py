import sys
import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

excel_path = r'C:\Affiliate\Chăm Da Tiết Kiệm\Link customed\Facebook\cây lăn massage mắt.xlsx'
wb = openpyxl.load_workbook(excel_path)
sheet = wb.active
for i, row in enumerate(sheet.iter_rows(values_only=True), 1):
    if i > 1 and len(row) > 2 and row[2]:
        print(f"{i-1}. {row[1]} -> {row[2]}")
