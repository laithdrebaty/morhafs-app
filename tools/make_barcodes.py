"""توليد ملصقات باركود EAN-13 داخلية (بادئة 200) لمنتجات غير معلّبة.

الاستخدام:  python tools/make_barcodes.py
ينتج ملف HTML ثم يطبعه PDF عبر Chrome/Edge.
"""
import html, os, subprocess, sys

ITEMS = [
    'قهوة اسبريسو', 'قهوة اسبريسو دبل', 'قهوة نسكافيه', 'قهوة نسكافيه دبل', 'قهوة غلي',
    '٣ب١', '٢ب١', 'فرنسي', 'كابتشينو', 'شاي', 'زهورات', 'كمون و ليمون', 'بابونج',
]
PREFIX = '200'  # نطاق GS1 للاستخدام الداخلي في المحل — لا يتعارض مع باركود أي منتج حقيقي
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'باركود-المشروبات.pdf')

L = ['0001101','0011001','0010011','0111101','0100011','0110001','0101111','0111011','0110111','0001011']
G = ['0100111','0110011','0011011','0100001','0011101','0111001','0000101','0010001','0001001','0010111']
R = [''.join('1' if b == '0' else '0' for b in c) for c in L]
PARITY = ['LLLLLL','LLGLGG','LLGGLG','LLGGGL','LGLLGG','LGGLLG','LGGGLL','LGLGLG','LGLGGL','LGGLGL']

def check_digit(d12):
    s = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d12))
    return str((10 - s % 10) % 10)

def ean13_bits(code):
    d = [int(c) for c in code]
    left = ''.join((L if PARITY[d[0]][i] == 'L' else G)[d[i + 1]] for i in range(6))
    right = ''.join(R[x] for x in d[7:])
    return '101' + left + '01010' + right + '101'

def svg(code, mod=0.33, h=20.0):
    """باركود بالحجم القياسي (عرض الخط 0.33 مم) مع هوامش صامتة."""
    bits, qz_l, qz_r = ean13_bits(code), 11, 7
    guard = {i for i in list(range(0, 3)) + list(range(45, 50)) + list(range(92, 95))}
    w = (qz_l + 95 + qz_r) * mod
    rects = []
    for i, b in enumerate(bits):
        if b == '1':
            bh = h + (3.2 if i in guard else 0)
            rects.append(f'<rect x="{(qz_l + i) * mod:.3f}" y="0" width="{mod:.3f}" height="{bh:.2f}"/>')
    ty = h + 3.0
    x0 = lambda m: (qz_l + m) * mod
    # كل رقم في مكانه تحت خاناته السبعة (مثل الباركود القياسي) حتى لا يتداخل مع خطوط الحماية
    digit = lambda ch, m: f'<text x="{x0(m):.2f}" y="{ty}" text-anchor="middle">{ch}</text>'
    txt = (digit(code[0], -5)
           + ''.join(digit(code[1 + i], 3 + 7 * i + 3.5) for i in range(6))
           + ''.join(digit(code[7 + i], 50 + 7 * i + 3.5) for i in range(6)))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h + 3.6:.2f}mm" viewBox="0 0 {w:.2f} {h + 3.6:.2f}">'
            f'<rect width="100%" height="100%" fill="#fff"/><g fill="#000">{"".join(rects)}</g>'
            f'<g font-family="Consolas, monospace" font-size="3.1" fill="#000">{txt}</g></svg>')

codes = []
for n, name in enumerate(ITEMS, 1):
    d12 = PREFIX + str(n).zfill(9)
    codes.append((name.strip(), d12 + check_digit(d12)))

labels = ''.join(f'''<div class="lbl"><div class="nm">{html.escape(name)}</div>{svg(code)}</div>''' for name, code in codes)
table = ''.join(f'<tr><td>{i}</td><td>{html.escape(n)}</td><td dir="ltr">{c}</td></tr>' for i, (n, c) in enumerate(codes, 1))
page = f'''<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>باركود المشروبات</title>
<style>
  @page {{ size: A4; margin: 10mm; }}
  body {{ margin: 0; font-family: Tahoma, "Segoe UI", Arial, sans-serif; color: #000; }}
  h1 {{ font-size: 15pt; text-align: center; margin: 0 0 2mm; }}
  .sub {{ text-align: center; font-size: 9pt; color: #555; margin-bottom: 5mm; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm; }}
  .lbl {{ border: 0.3mm dashed #999; border-radius: 2mm; padding: 3mm 2mm 2.5mm; text-align: center; break-inside: avoid; }}
  .nm {{ font-size: 13pt; font-weight: bold; margin-bottom: 2mm; }}
  svg {{ display: block; margin: 0 auto; }}
  .list {{ break-before: page; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11pt; }}
  td, th {{ border: 0.3mm solid #999; padding: 2mm 3mm; text-align: right; }}
  td[dir=ltr] {{ font-family: Consolas, monospace; text-align: left; letter-spacing: 0.5pt; }}
</style></head><body>
<h1>باركود المشروبات</h1>
<div class="sub">قصّ الملصقات على الخطوط المنقّطة — للطباعة اختر «الحجم الفعلي 100%» وليس «ملاءمة الصفحة»</div>
<div class="grid">{labels}</div>
<div class="list"><h1>قائمة الأرقام</h1><div class="sub">لإدخالها في التطبيق: أضف المنتج واكتب الرقم في خانة الباركود أو امسحه بالكاميرا</div>
<table><tr><th>#</th><th>المشروب</th><th>الباركود</th></tr>{table}</table></div>
</body></html>'''

html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'barcodes.html'))
open(html_path, 'w', encoding='utf-8').write(page)
out = os.path.abspath(OUT)
for browser in [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']:
    if os.path.exists(browser):
        subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={out}', 'file:///' + html_path.replace('\\', '/')], check=True, capture_output=True)
        break
for n, c in codes:
    print(c, n)
print('PDF:', out, os.path.getsize(out), 'bytes')
