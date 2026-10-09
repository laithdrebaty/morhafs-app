"""توليد ملصقات باركود EAN-13 داخلية (بادئة 200) للمشروبات، مع رسمة كاسة لكل مشروب.

الاستخدام:  python tools/make_barcodes.py
ينتج ملف HTML ثم يطبعه PDF عبر Chrome/Edge.
لإضافة مشروب جديد: أضفه في آخر القائمة ITEMS (حتى تبقى أرقام الباركود القديمة كما هي).
"""
import html, os, subprocess

# (الاسم، شكل الكاسة، الحجم، لون المشروب، الزينة فوق المشروب)
#  أشكال الكاسات: demitasse فنجان مع صحن | arabic فنجان عربي | paper كاسة كرتون | mug مَغ | wide كاسة كابتشينو | glass استكانة
#  الأحجام: S صغير | M وسط | L كبير
ITEMS = [
    ('قهوة اسبريسو',      'demitasse', 'S', '#4a2412', 'crema'),
    ('قهوة اسبريسو دبل',  'demitasse', 'M', '#4a2412', 'crema'),
    ('قهوة نسكافيه',      'paper',     'M', '#a8743f', 'foam'),
    ('قهوة نسكافيه دبل',  'paper',     'L', '#8c5a2b', 'foam'),
    ('قهوة غلي',          'arabic',    'S', '#3b1d0c', 'dots'),
    ('٣ب١',              'paper',     'M', '#c8955c', 'none'),
    ('٢ب١',              'paper',     'M', '#b07a45', 'none'),
    ('فرنسي',            'mug',       'M', '#b88a5c', 'swirl'),
    ('كابتشينو',          'wide',      'L', '#f1e3cc', 'heart'),
    ('شاي',              'glass',     'M', '#b8461b', 'none'),
    ('زهورات',            'mug',       'M', '#b8324a', 'flower'),
    ('كمون و ليمون',      'mug',       'M', '#d9a92b', 'lemon'),
    ('بابونج',            'mug',       'M', '#e2b93b', 'daisy'),
    ('شاي أخضر',          'glass',     'M', '#a9b83a', 'leaf'),
    ('اسبريسو قزاز',      'shot',      'S', '#4a2412', 'crema'),
]
SIZE_NAME = {'S': 'صغير', 'M': 'وسط', 'L': 'كبير'}
CUP_NAME = {'S': 'كاسة صغيرة', 'M': 'كاسة وسط', 'L': 'كاسة كبيرة'}
SIZE_SCALE = {'S': 0.68, 'M': 0.84, 'L': 1.0}
PREFIX = '200'  # نطاق GS1 للاستخدام الداخلي في المحل — لا يتعارض مع باركود أي منتج حقيقي
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'باركود-المشروبات-مع-رسوم.pdf')

# ======================= الباركود =======================
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

def barcode_svg(code, mod=0.33, h=12.5):
    """باركود بالعرض القياسي (خط 0.33 مم) مع هوامش صامتة."""
    bits, qz_l, qz_r = ean13_bits(code), 11, 7
    guard = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))
    w = (qz_l + 95 + qz_r) * mod
    rects = ''.join(f'<rect x="{(qz_l + i) * mod:.3f}" y="0" width="{mod:.3f}" height="{h + (2.6 if i in guard else 0):.2f}"/>'
                    for i, b in enumerate(bits) if b == '1')
    ty, x0 = h + 2.8, (lambda m: (qz_l + m) * mod)
    digit = lambda ch, m: f'<text x="{x0(m):.2f}" y="{ty}" text-anchor="middle">{ch}</text>'
    txt = (digit(code[0], -5) + ''.join(digit(code[1 + i], 3 + 7 * i + 3.5) for i in range(6))
           + ''.join(digit(code[7 + i], 50 + 7 * i + 3.5) for i in range(6)))
    return (f'<svg class="bc" xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h + 3.4:.2f}mm" viewBox="0 0 {w:.2f} {h + 3.4:.2f}">'
            f'<rect width="100%" height="100%" fill="#fff"/><g fill="#000">{rects}</g>'
            f'<g font-family="Consolas, monospace" font-size="2.9" fill="#000">{txt}</g></svg>')

# ======================= رسوم الكاسات =======================
INK = '#4a3426'  # لون الخطوط

def steam(cx, top, n=3, spread=11):
    out = ''
    for k in range(n):
        x = cx + (k - (n - 1) / 2) * spread
        out += (f'<path d="M{x} {top} q -5 -6 0 -12 q 5 -6 0 -12" fill="none" stroke="#b9a99a" stroke-width="2.2" '
                f'stroke-linecap="round" opacity=".8"/>')
    return out

def topping(kind, cx, cy, rx, ry):
    """زينة سطح المشروب."""
    if kind == 'crema':
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*.86}" ry="{ry*.8}" fill="#c98a45"/>'
                f'<ellipse cx="{cx-rx*.15}" cy="{cy-ry*.1}" rx="{rx*.45}" ry="{ry*.38}" fill="#dba66a" opacity=".8"/>')
    if kind == 'foam':
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*.8}" ry="{ry*.72}" fill="#e7cfae"/>'
                + ''.join(f'<circle cx="{cx+dx*rx}" cy="{cy+dy*ry}" r="{r}" fill="#f6e9d6"/>'
                          for dx, dy, r in [(-.35,-.1,1.6),(.2,.15,1.3),(.42,-.2,1),(-.05,.3,1.1),(.05,-.3,.9)]))
    if kind == 'dots':  # وش القهوة العربية
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*.85}" ry="{ry*.8}" fill="#6b3f22"/>'
                + ''.join(f'<circle cx="{cx+dx*rx}" cy="{cy+dy*ry}" r=".9" fill="#a8743f"/>'
                          for dx, dy in [(-.4,0),(-.15,-.3),(.1,.25),(.35,-.1),(.2,-.4),(-.3,.35)]))
    if kind == 'swirl':
        return (f'<path d="M{cx-rx*.55} {cy} q {rx*.3} {-ry*.9} {rx*.6} 0 t {rx*.5} 0" fill="none" stroke="#f3e6d3" stroke-width="2.4" stroke-linecap="round"/>'
                f'<path d="M{cx-rx*.3} {cy+ry*.35} q {rx*.3} {-ry*.6} {rx*.55} 0" fill="none" stroke="#f3e6d3" stroke-width="1.8" stroke-linecap="round"/>')
    if kind == 'heart':  # رسمة قلب على رغوة الكابتشينو + رشة كاكاو
        hx, hy, s = cx, cy - ry * .05, rx * .32
        return (f'<path d="M{hx} {hy+s*.85} C {hx-s*1.6} {hy-s*.1}, {hx-s*.9} {hy-s*1.2}, {hx} {hy-s*.45} '
                f'C {hx+s*.9} {hy-s*1.2}, {hx+s*1.6} {hy-s*.1}, {hx} {hy+s*.85} Z" fill="#a0673a"/>'
                + ''.join(f'<circle cx="{cx+dx*rx}" cy="{cy+dy*ry}" r=".8" fill="#6b3f22"/>'
                          for dx, dy in [(-.7,-.1),(.68,.15),(-.55,.45),(.5,-.45),(.75,-.25)]))
    if kind == 'lemon':
        lx, ly, r = cx + rx * .35, cy - ry * .1, ry * 1.1
        return (f'<circle cx="{lx}" cy="{ly}" r="{r}" fill="#f7e15a" stroke="#d9b21c" stroke-width="1.2"/>'
                + ''.join(f'<line x1="{lx}" y1="{ly}" x2="{lx + r*.85*c}" y2="{ly + r*.85*sn}" stroke="#fff6b0" stroke-width=".8"/>'
                          for c, sn in [(1,0),(.5,.87),(-.5,.87),(-1,0),(-.5,-.87),(.5,-.87)]))
    if kind == 'flower':  # زهرة كركديه/ورد للزهورات
        fx, fy = cx - rx * .2, cy
        petals = ''.join(f'<ellipse cx="{fx}" cy="{fy - 2.6}" rx="1.7" ry="2.8" fill="#f28fb0" transform="rotate({a} {fx} {fy})"/>' for a in range(0, 360, 72))
        return petals + f'<circle cx="{fx}" cy="{fy}" r="1.4" fill="#ffd34d"/>'
    if kind == 'leaf':  # ورقة شاي أخضر
        lx, ly = cx + rx * .15, cy
        return (f'<path d="M{lx-6} {ly+.6} Q{lx-1} {ly-5.5} {lx+6} {ly-.6} Q{lx+1} {ly+5} {lx-6} {ly+.6} Z" fill="#4c9a2a" stroke="#2f6b18" stroke-width=".6"/>'
                f'<path d="M{lx-5} {ly+.5} L{lx+5} {ly-.5}" stroke="#a8d97a" stroke-width=".7"/>')
    if kind == 'daisy':  # زهرة بابونج
        fx, fy = cx + rx * .15, cy
        petals = ''.join(f'<ellipse cx="{fx}" cy="{fy - 3}" rx="1.1" ry="2.6" fill="#ffffff" stroke="#e8e2c8" stroke-width=".3" transform="rotate({a} {fx} {fy})"/>' for a in range(0, 360, 36))
        return petals + f'<circle cx="{fx}" cy="{fy}" r="1.8" fill="#f2b705"/>'
    return ''

def cup_svg(style, size, liquid, top):
    """رسمة كاسة بحجم يتغيّر حسب الصغير/الوسط/الكبير، ثابتة القاعدة في أسفل الرسمة."""
    k = SIZE_SCALE[size]
    parts = ['<ellipse cx="50" cy="104" rx="40" ry="4.5" fill="#000" opacity=".08"/>']
    if style == 'paper':
        parts += [
            f'<path d="M18 30 L82 30 L74 100 Q50 104 26 100 Z" fill="#fbf8f3" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>',
            f'<path d="M22 58 L78 58 L75.6 80 Q50 83 24.4 80 Z" fill="#9b6a3f" stroke="{INK}" stroke-width="1.6"/>',
            '<circle cx="50" cy="69" r="6" fill="#f6eadb"/><path d="M47 66 q3 3 0 6 M53 66 q-3 3 0 6" stroke="#9b6a3f" stroke-width="1.2" fill="none"/>',
            f'<ellipse cx="50" cy="30" rx="32" ry="6.5" fill="#fbf8f3" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="30.8" rx="28.5" ry="5" fill="{liquid}"/>',
            topping(top, 50, 30.8, 28.5, 5), steam(50, 18)]
    elif style == 'demitasse':
        parts += [
            f'<ellipse cx="50" cy="97" rx="42" ry="8" fill="#ffffff" stroke="{INK}" stroke-width="2"/>',
            f'<ellipse cx="50" cy="95.5" rx="22" ry="3.4" fill="#ece6de"/>',
            f'<path d="M74 58 q16 0 14 13 q-2 11 -17 12" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>',
            f'<path d="M74 58 q16 0 14 13 q-2 11 -17 12" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round"/>',
            f'<path d="M22 52 L78 52 Q78 92 50 94 Q22 92 22 52 Z" fill="#ffffff" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="52" rx="28" ry="6" fill="#ffffff" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="52.8" rx="24.5" ry="4.6" fill="{liquid}"/>',
            topping(top, 50, 52.8, 24.5, 4.6), steam(50, 40, 2, 12)]
    elif style == 'arabic':  # فنجان قهوة صغير مزخرف
        parts += [
            f'<ellipse cx="50" cy="98" rx="38" ry="7" fill="#f4ead7" stroke="{INK}" stroke-width="2"/>',
            f'<path d="M24 56 L76 56 Q74 90 50 94 Q26 90 24 56 Z" fill="#f7f0e2" stroke="{INK}" stroke-width="2.2"/>',
            '<path d="M27 66 L73 66" stroke="#c4952f" stroke-width="2.5"/><path d="M29 72 L71 72" stroke="#2e7d6b" stroke-width="1.6"/>',
            ''.join(f'<circle cx="{x}" cy="79" r="1.4" fill="#c4952f"/>' for x in range(34, 70, 6)),
            f'<ellipse cx="50" cy="56" rx="26" ry="5.6" fill="#f7f0e2" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="56.8" rx="22.5" ry="4.3" fill="{liquid}"/>',
            topping(top, 50, 56.8, 22.5, 4.3), steam(50, 44, 2, 10)]
    elif style == 'mug':
        parts += [
            f'<path d="M76 46 q20 0 18 20 q-2 17 -20 17" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>',
            f'<path d="M76 46 q20 0 18 20 q-2 17 -20 17" fill="none" stroke="#e9f1f7" stroke-width="3.6" stroke-linecap="round"/>',
            f'<path d="M22 34 L78 34 L77 96 Q50 101 23 96 Z" fill="#e9f1f7" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>',
            f'<path d="M23.4 44 L76.6 44 L76.2 94 Q50 99 23.8 94 Z" fill="{liquid}" opacity=".55"/>',
            '<path d="M30 48 L30 88" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".7"/>',
            f'<ellipse cx="50" cy="34" rx="28" ry="6" fill="#e9f1f7" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="35" rx="24.5" ry="4.6" fill="{liquid}"/>',
            topping(top, 50, 35, 24.5, 4.6), steam(50, 22)]
    elif style == 'wide':  # كاسة كابتشينو عريضة مع صحن
        parts += [
            f'<ellipse cx="50" cy="97" rx="46" ry="8" fill="#ffffff" stroke="{INK}" stroke-width="2"/>',
            f'<path d="M84 52 q14 2 10 14 q-4 9 -16 8" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>',
            f'<path d="M84 52 q14 2 10 14 q-4 9 -16 8" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round"/>',
            f'<path d="M12 46 L88 46 Q86 90 50 93 Q14 90 12 46 Z" fill="#ffffff" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="46" rx="38" ry="7.5" fill="#ffffff" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="46.8" rx="34" ry="6" fill="#8c5a2b"/>',
            f'<ellipse cx="50" cy="46.8" rx="30" ry="5" fill="{liquid}"/>',
            topping(top, 50, 46.8, 30, 5), steam(50, 34)]
    elif style == 'shot':  # كاسة اسبريسو قزاز شفافة (بلا كاسة كرتون) — تظهر القهوة والكريما من خلال الزجاج
        parts += [
            f'<ellipse cx="50" cy="98" rx="34" ry="6.5" fill="#ffffff" stroke="{INK}" stroke-width="2"/>',
            f'<path d="M73 56 q14 1 12 13 q-2 10 -14 10" fill="none" stroke="#b9d6e6" stroke-width="5" stroke-linecap="round"/>',
            f'<path d="M73 56 q14 1 12 13 q-2 10 -14 10" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round" opacity=".6"/>',
            f'<path d="M26 44 L74 44 L70 93 Q50 97 30 93 Z" fill="#eaf5fb" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round" opacity=".95"/>',
            f'<path d="M28.6 62 L71.4 62 L69.6 91.5 Q50 95.5 30.4 91.5 Z" fill="{liquid}"/>',
            f'<path d="M28.6 62 L71.4 62 L71 67 L29 67 Z" fill="#c98a45"/>',
            '<path d="M34 50 L36 88" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".85"/>',
            '<path d="M64 52 L63 60" stroke="#ffffff" stroke-width="2" stroke-linecap="round" opacity=".7"/>',
            f'<ellipse cx="50" cy="44" rx="24" ry="5" fill="#f4fafd" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="62" rx="21.4" ry="3.6" fill="#c98a45"/>',
            topping(top, 50, 62, 21.4, 3.6), steam(50, 32, 2, 10)]
    elif style == 'glass':  # استكانة شاي
        parts += [
            f'<ellipse cx="50" cy="98" rx="30" ry="6" fill="#ffffff" stroke="{INK}" stroke-width="2"/>',
            f'<path d="M30 36 Q40 62 33 92 Q50 97 67 92 Q60 62 70 36 Z" fill="#eef6fb" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>',
            f'<path d="M31.5 44 Q40 64 34 91 Q50 95.5 66 91 Q60 64 68.5 44 Z" fill="{liquid}" opacity=".9"/>',
            '<path d="M38 48 Q42 64 38 86" stroke="#ffffff" stroke-width="2.2" fill="none" stroke-linecap="round" opacity=".6"/>',
            f'<ellipse cx="50" cy="36" rx="20" ry="4.2" fill="#eef6fb" stroke="{INK}" stroke-width="2.2"/>',
            f'<ellipse cx="50" cy="44" rx="18.5" ry="3" fill="{liquid}"/>', topping(top, 50, 44, 18.5, 3), steam(50, 26, 2, 10)]
    inner = ''.join(parts)
    return (f'<svg class="art" xmlns="http://www.w3.org/2000/svg" viewBox="0 -2 110 110">'
            f'<g transform="translate(50 106) scale({k}) translate(-50 -106)">{inner}</g></svg>')

# ======================= الصفحة =======================
codes = []
for n, (name, style, size, liquid, top) in enumerate(ITEMS, 1):
    d12 = PREFIX + str(n).zfill(9)
    codes.append((name.strip(), d12 + check_digit(d12), style, size, liquid, top))

SIZE_CLR = {'S': '#e7f3e2;color:#3c7a22', 'M': '#e3effc;color:#1f5f9e', 'L': '#fbe7d9;color:#a14a12'}
labels = ''.join(f'''<div class="lbl">
  <div class="cup">{cup_svg(style, size, liquid, top)}</div>
  <div class="info"><div class="nm">{html.escape(name)}</div>
    <div class="sz" style="background:{SIZE_CLR[size]}">{CUP_NAME[size]}</div>{barcode_svg(code)}</div>
</div>''' for name, code, style, size, liquid, top in codes)
table = ''.join(f'<tr><td>{i}</td><td>{html.escape(n)}</td><td>{SIZE_NAME[sz]}</td><td dir="ltr">{c}</td></tr>'
                for i, (n, c, st, sz, lq, tp) in enumerate(codes, 1))
page = f'''<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>باركود المشروبات</title>
<style>
  @page {{ size: A4; margin: 8mm; }}
  body {{ margin: 0; font-family: Tahoma, "Segoe UI", Arial, sans-serif; color: #2b2b2b; }}
  h1 {{ font-size: 15pt; text-align: center; margin: 0 0 0.5mm; color: #4a3426; }}
  .sub {{ text-align: center; font-size: 8pt; color: #777; margin-bottom: 2.5mm; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2.2mm; }}
  .lbl {{ display: flex; align-items: center; gap: 3mm; border: 0.3mm dashed #b8a99a; border-radius: 3mm;
          padding: 1.2mm 3mm; break-inside: avoid; background: #fffdf9; }}
  .cup {{ width: 25mm; height: 25mm; flex: none; display: flex; align-items: flex-end; justify-content: center; }}
  .cup .art {{ width: 25mm; height: 25mm; }}
  .info {{ flex: 1; display: flex; flex-direction: column; align-items: center; }}
  .nm {{ font-size: 12pt; font-weight: bold; color: #3a2a1e; }}
  .sz {{ font-size: 8pt; font-weight: bold; border-radius: 10mm; padding: 0.4mm 3mm; margin: 0.4mm 0 0.8mm; }}
  .bc {{ display: block; }}
  .list {{ break-before: page; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11pt; }}
  td, th {{ border: 0.3mm solid #999; padding: 2mm 3mm; text-align: right; }}
  td[dir=ltr] {{ font-family: Consolas, monospace; text-align: left; letter-spacing: 0.5pt; }}
</style></head><body>
<h1>☕ باركود المشروبات</h1>
<div class="sub">قصّ الملصقات على الخطوط المنقّطة — للطباعة اختر «الحجم الفعلي 100%» وليس «ملاءمة الصفحة» — الأرقام نفسها كما في النسخة السابقة</div>
<div class="grid">{labels}</div>
<div class="list"><h1>قائمة الأرقام</h1><div class="sub">لإدخالها في التطبيق: من صفحة «آلة القهوة» ← «➕ مشروب» واكتب الرقم في خانة الباركود أو امسحه بالكاميرا</div>
<table><tr><th>#</th><th>المشروب</th><th>الحجم</th><th>الباركود</th></tr>{table}</table></div>
</body></html>'''

html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'barcodes.html'))
open(html_path, 'w', encoding='utf-8').write(page)
out = os.path.abspath(OUT)
for browser in [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']:
    if os.path.exists(browser):
        subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                        f'--print-to-pdf={out}', 'file:///' + html_path.replace('\\', '/')], check=True, capture_output=True)
        break
for n, c, *_ in codes:
    print(c, n)
print('PDF:', out, os.path.getsize(out), 'bytes')
