from datetime import datetime, timedelta, date as dt_date
from pathlib import Path
from typing import Literal, Optional
import re

import swisseph as swe
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
app = FastAPI(title="ROTA Personal Astrology - Friend Mode", version="3.4.1")

# ตั้ง ayanamsa แบบ Lahiri ครั้งเดียวตอนเริ่มระบบ (ใช้กับโหมด sidereal / ระบบไทย)
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

DISCLAIMER = "ข้อมูลนี้เพื่อความบันเทิงและเป็นแนวทางประกอบการคิด ไม่ใช่คำแนะนำทางการแพทย์ กฎหมาย หรือการเงิน"

# -----------------------------------------------------------------------------
# 1. ASTROLOGICAL DATA & MAPS
# -----------------------------------------------------------------------------
PLANETS = [
    ("Sun", swe.SUN, "อาทิตย์", "☉"), ("Moon", swe.MOON, "จันทร์", "☽"),
    ("Mercury", swe.MERCURY, "พุธ", "☿"), ("Venus", swe.VENUS, "ศุกร์", "♀"),
    ("Mars", swe.MARS, "อังคาร", "♂"), ("Jupiter", swe.JUPITER, "พฤหัสบดี", "♃"),
    ("Saturn", swe.SATURN, "เสาร์", "♄"), ("Uranus", swe.URANUS, "ยูเรนัส", "♅"),
    ("Neptune", swe.NEPTUNE, "เนปจูน", "♆"), ("Pluto", swe.PLUTO, "พลูโต", "♇"),
]
PLANET_IDS = {p[0]: p[1] for p in PLANETS}
PLANET_TH = {p[0]: p[2] for p in PLANETS}
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_TH = ["เมษ", "พฤษภ", "เมถุน", "กรกฎ", "สิงห์", "กันย์", "ตุล", "พิจิก", "ธนู", "มังกร", "กุมภ์", "มีน"]
TRAD_RULER = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
HOUSE_TH = ["ตนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ", "ปัตนิ", "มรณะ", "ศุภะ", "กัมมะ", "ลาภะ", "วินาศ"]

HOUSE_TOPICS = {
    1: "ตัวตน ลุคภายนอก ภาพจำ และพลังงานส่วนตัว",
    2: "เงินในกระเป๋า ช่องทางหาเงิน ค่านิยม และของเปย์ตัวเอง",
    3: "เพื่อนสนิท คอนเนกชัน คอร์สสั้น การเดินทางใกล้ๆ และการสื่อสาร",
    4: "บ้าน ครอบครัว เซฟโซน และที่อยู่อาศัย",
    5: "ความรักกุ๊กกิ๊ก ความสุข ไฟแพชชันโปรเจกต์ใหม่ ของเล่น/สัตว์เลี้ยง",
    6: "งานประจำ รูทีนชีวิต สุขภาพ และออฟฟิศซินโดรม",
    7: "คู่แท้ หุ้นส่วน แฟน และคู่สัญญา",
    8: "เงินคนอื่น หนี้สิน สัญญา ทรัพย์สินร่วม และการเยียวยาจิตใจ",
    9: "ต่างประเทศ การเรียนต่อ โลกทัศน์ และสายมู/ความเชื่อ",
    10: "งานใหญ่ อาชีพ ชื่อเสียง ตำแหน่ง และเป้าหมายชีวิต",
    11: "เพื่อนกลุ่มใหญ่ คอนเนกชันปังๆ ความฝัน และลาภลอย",
    12: "เรื่องเบื้องหลัง การพักชาร์จแบต เซนส์ และสิ่งที่มองไม่เห็น",
}

ASC_VIBE = {
    0: "ลุคตรงไปตรงมา พลังเยอะ ดูมั่นใจ มักลุยก่อนคิดทีหลัง",
    1: "ลุคนิ่ง สุขุม ดูน่าเชื่อถือ ชอบความสบายและของมีคุณภาพ",
    2: "ลุคช่างคุย ว่องไว ดูอ่อนกว่าวัย สนใจเรื่องรอบตัวไปหมด",
    3: "ลุคอ่อนโยน ดูใจดี อ่อนไหวง่าย ผูกพันกับคนใกล้ตัว",
    4: "ลุคมีออร่า โดดเด่น ดูเป็นผู้นำ และรักศักดิ์ศรี",
    5: "ลุคเรียบร้อย ละเอียด ดูฉลาดและเป็นระเบียบ",
    6: "ลุคสุภาพ ดูดี เข้ากับคนง่าย รักความสมดุล",
    7: "ลุคลึกลับ สายตามีพลัง ไม่เปิดเผยทุกอย่างง่ายๆ",
    8: "ลุคร่าเริง ตรงไปตรงมา รักอิสระ ชอบเรียนรู้โลกกว้าง",
    9: "ลุคจริงจัง ดูมีความรับผิดชอบ โตเกินวัย",
    10: "ลุคแปลกเฉพาะตัว เป็นตัวของตัวเอง ชอบคิดนอกกรอบ",
    11: "ลุคนุ่มนวล ฝันๆ ซึมซับอารมณ์คนรอบข้างง่าย",
}

ASPECTS = [(0, "กุม"), (60, "เกื้อหนุน"), (90, "ฉาก"), (120, "ตรีโกณ"), (180, "เล็ง")]
SLOW_PLANETS = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
ASPECT_TARGETS = ["Sun", "Moon", "Mercury", "Venus", "Mars"]

BASE_FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED


def flags_for(zodiac: str) -> int:
    """sidereal = ระบบราศีแบบโหราศาสตร์ไทย/อินเดีย, tropical = แบบตะวันตก"""
    return BASE_FLAGS | swe.FLG_SIDEREAL if zodiac == "sidereal" else BASE_FLAGS


# -----------------------------------------------------------------------------
# 2. REQUEST MODELS
# -----------------------------------------------------------------------------
class Birth(BaseModel):
    name: str = "แก"
    date: str
    time: str
    place: str = "Bangkok, Thailand"
    lat: float = Field(13.7563, ge=-90, le=90)
    lon: float = Field(100.5018, ge=-180, le=180)
    tz: float = Field(7.0, ge=-12, le=14)
    zodiac: Literal["sidereal", "tropical"] = "sidereal"


class TransitRequest(Birth):
    transit_date: str
    months: int = Field(12, ge=1, le=24)


class AnnualRequest(Birth):
    # รับได้ทั้ง ค.ศ. และ พ.ศ. (ถ้า > 2400 จะลบ 543 ให้เอง)
    annual_year: int = Field(..., ge=1900, le=2800)
    # วันที่อ้างอิง (ไม่บังคับ) ถ้ายังไม่ถึงวันเกิดของปีนั้น จะใช้รอบ profection ก่อนหน้า
    as_of: Optional[str] = None


# -----------------------------------------------------------------------------
# 3. DATE / TIME HELPERS (รองรับ ค.ศ./พ.ศ./เดือนไทย)
# -----------------------------------------------------------------------------
EN_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
TH_MONTHS_FULL = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                  "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
TH_MONTHS_ABBR = ["มค", "กพ", "มีค", "เมย", "พค", "มิย", "กค", "สค", "กย", "ตค", "พย", "ธค"]


def _month_from_text(token: str) -> int:
    t = token.strip().lower().replace(".", "")
    if t[:3] in EN_MONTHS:
        return EN_MONTHS.index(t[:3]) + 1
    for i in range(12):
        if t == TH_MONTHS_FULL[i] or t == TH_MONTHS_ABBR[i]:
            return i + 1
    raise ValueError(f"อ่านชื่อเดือนไม่ออก: '{token}'")


def parse_flexible_date(date_str: str) -> dt_date:
    """
    รองรับตัวอย่าง:
      1996-01-29 | 2539-01-29 | 29/01/2539 | 29 Jan 1996 | 29 Jan BE 2539
      29 มกราคม 2539 | 29 ม.ค. พ.ศ. 2539 | 1996-01-29T00:00:00
    ปี > 2400 หรือมีคำว่า BE / พ.ศ. จะถูกแปลงเป็น ค.ศ. อัตโนมัติ
    """
    if date_str is None or not str(date_str).strip():
        raise ValueError("ไม่ได้ระบุวันที่")
    raw = str(date_str).strip().split("T")[0].strip()

    is_be = bool(re.search(r"\bBE\b|พ\.?\s?ศ\.?", raw, re.I))
    raw = re.sub(r"\bBE\b|\bCE\b|พ\.?\s?ศ\.?|ค\.?\s?ศ\.?", " ", raw, flags=re.I).strip()

    m = re.fullmatch(r"(\d{1,4})[-/.\s]+(\d{1,2})[-/.\s]+(\d{1,4})", raw)
    if m:
        a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if len(m.group(1)) == 4 or a > 31:
            year, month, day = a, b, c      # YYYY-MM-DD
        else:
            day, month, year = a, b, c      # DD/MM/YYYY
    else:
        tokens = [t for t in re.split(r"[\s,/\-]+", raw) if t]
        if len(tokens) != 3:
            raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง: '{date_str}'")
        try:
            day, month, year = int(tokens[0]), _month_from_text(tokens[1]), int(tokens[2])
        except ValueError:
            raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง: '{date_str}'")

    if is_be or year > 2400:
        year -= 543
    try:
        return dt_date(year, month, day)
    except ValueError:
        raise ValueError(f"วันที่ไม่มีอยู่จริง: '{date_str}'")


def parse_time(time_str: str):
    """รองรับ HH:MM, HH:MM:SS, HH.MM และต่อท้ายด้วย 'น.' ได้"""
    m = re.fullmatch(r"\s*(\d{1,2})[:.](\d{2})(?:[:.](\d{2}))?\s*(?:น\.?)?\s*", str(time_str))
    if not m:
        raise ValueError(f"รูปแบบเวลาไม่ถูกต้อง: '{time_str}' (ใช้ HH:MM)")
    h, mi, se = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    if h > 23 or mi > 59 or se > 59:
        raise ValueError(f"เวลาไม่ถูกต้อง: '{time_str}'")
    return h, mi, se


def normalize_year(y: int) -> int:
    return y - 543 if y > 2400 else y


def safe_date(year: int, month: int, day: int) -> dt_date:
    """กันกรณีเกิด 29 ก.พ. แล้วปีนั้นไม่ใช่ปีอธิกวาร"""
    try:
        return dt_date(year, month, day)
    except ValueError:
        return dt_date(year, month, 28)


def jd_for(local_date: str, local_time: str = "12:00", tz: float = 7.0) -> float:
    d = parse_flexible_date(local_date)
    h, mi, se = parse_time(local_time)
    utc = datetime(d.year, d.month, d.day, h, mi, se) - timedelta(hours=tz)
    return swe.julday(utc.year, utc.month, utc.day,
                      utc.hour + utc.minute / 60 + utc.second / 3600, swe.GREG_CAL)


# -----------------------------------------------------------------------------
# 4. ASTROLOGY CALCULATIONS
# -----------------------------------------------------------------------------
def sign_index(lon): return int((lon % 360) // 30)
def house_of(lon, asc_sign_idx): return ((sign_index(lon) - asc_sign_idx) % 12) + 1


def planet_positions(jd, flags):
    out = {}
    for en, pid, th, glyph in PLANETS:
        xx, _ = swe.calc_ut(jd, pid, flags)
        lon, speed = xx[0], xx[3]
        si = sign_index(lon)
        out[en] = {
            "name": en, "thai": th, "glyph": glyph,
            "longitude": round(lon % 360, 6),
            "sign": SIGNS[si], "sign_th": SIGN_TH[si],
            "degree": round(lon % 30, 2),
            "retrograde": speed < 0,
        }
    return out


def house_data(jd, lat, lon, flags):
    # whole sign house ('W') ส่ง flags เพื่อให้ลัคนาเป็นระบบเดียวกับดาว (sidereal/tropical)
    _, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)
    asc = ascmc[0] % 360
    ai = sign_index(asc)
    return {"asc": asc, "asc_sign": SIGNS[ai], "asc_sign_th": SIGN_TH[ai], "asc_sign_index": ai}


def get_natal(b: Birth):
    flags = flags_for(b.zodiac)
    jd = jd_for(b.date, b.time, b.tz)
    planets = planet_positions(jd, flags)
    angles = house_data(jd, b.lat, b.lon, flags)
    ai = angles["asc_sign_index"]
    for p in planets.values():
        p["house"] = house_of(p["longitude"], ai)
        p["house_th"] = HOUSE_TH[p["house"] - 1]
    return {"julian_day": jd, "zodiac": b.zodiac, "planets": planets, "angles": angles}


def ruler_of_house(n, h):
    """ผู้ครองเรือนที่ h (whole sign) และข้อมูลดาวนั้นในดวงกำเนิด"""
    si = (n["angles"]["asc_sign_index"] + h - 1) % 12
    r = TRAD_RULER[si]
    return r, n["planets"][r]


def angle_diff(a, b):
    return abs(((a - b + 180) % 360) - 180)


def find_aspects(trans_lon, natal_points, orb=3.0):
    found = []
    for nname, nlon in natal_points.items():
        diff = angle_diff(trans_lon, nlon)
        for ang, aname in ASPECTS:
            if abs(diff - ang) <= orb:
                found.append({"to": nname, "aspect": aname, "angle": ang, "orb": round(abs(diff - ang), 2)})
    return found


# -----------------------------------------------------------------------------
# 5. FRIENDLY NARRATIVE GENERATOR
# -----------------------------------------------------------------------------
def get_friendly_name(name):
    name = (name or "").strip()
    return name if name and name != "แก" else "แก"


def retro_note(p):
    return " (ถอยหลัง ต้องทบทวนซ้ำก่อนลงมือ)" if p.get("retrograde") else ""


def with_story_alias(sections):
    """
    ใส่คีย์ story / text ให้ทุก section ให้ครบทั้งคู่
    เพื่อให้ frontend ที่อ่าน s.story หรือ s.text ก็ได้ ไม่เกิด 'undefined is not an object'
    """
    out = []
    for s in sections:
        s = dict(s)
        body = s.get("story") or s.get("text") or ""
        s["story"] = body
        s["text"] = body
        s.setdefault("title", "")
        out.append(s)
    return out


def build_natal_friendly_reading(n, client_name=""):
    fname = get_friendly_name(client_name)
    pm = n["planets"]
    ai = n["angles"]["asc_sign_index"]

    asc_sign = n["angles"]["asc_sign_th"]
    asc_ruler = pm[TRAD_RULER[ai]]
    moon, merc, ven, mar = pm["Moon"], pm["Mercury"], pm["Venus"], pm["Mars"]

    _, r2 = ruler_of_house(n, 2)
    r10_en, r10 = ruler_of_house(n, 10)

    if r2["house"] in (2, 6, 10, 11):
        money_note = "ช่องทางหาเงินค่อนข้างเป็นรูปธรรมและต่อเนื่องเมื่อลงแรงกับเรื่องนี้"
    elif r2["house"] in (8, 12):
        money_note = "เงินมีจังหวะขึ้นลงตามเรื่องส่วนรวมหรือเรื่องเบื้องหลัง ควรมีเงินสำรองแยกไว้"
    else:
        money_note = "เงินเดินตามความสนใจและการลงมือทำในเรื่องนี้เป็นหลัก"

    sections = [
        {
            "title": "🧠 1. ตัวตน & Vibe ที่คนอื่นเห็น (Mental & Outer Vibe)",
            "text": (
                f"ลัคนาราศี{asc_sign}: {ASC_VIBE[ai]}. "
                f"เจ้าเรือนลัคนาคือดาว{asc_ruler['thai']} ไปสถิตเรือน {asc_ruler['house']} ({asc_ruler['house_th']})"
                f"{retro_note(asc_ruler)} "
                f"หัวใจหลักของ {fname} ในชีวิตนี้จึงวนอยู่กับเรื่อง **{HOUSE_TOPICS[asc_ruler['house']]}**"
            ),
        },
        {
            "title": "💖 2. โลกภายใน อารมณ์ & วิธีฮีลใจเวลาเครียด",
            "text": (
                f"จันทร์สถิตราศี{moon['sign_th']} เรือน {moon['house']}. "
                f"ความรู้สึกปลอดภัยของ {fname} ผูกกับเรื่อง **{HOUSE_TOPICS[moon['house']]}** "
                f"ทิป: เวลาเหนื่อยหรือนอยด์ ให้ถอยมาชาร์จในพื้นที่ส่วนตัว พักให้พอ แล้วค่อยกลับไปจัดการสิ่งที่ควบคุมได้"
            ),
        },
        {
            "title": "🗣️ 3. สไตล์การคิด การพูด & การตัดสินใจ",
            "text": (
                f"พุธอยู่ราศี{merc['sign_th']} เรือน {merc['house']}{retro_note(merc)}. "
                f"ความคิดและการสื่อสารของ {fname} จะเด่นในเรื่อง **{HOUSE_TOPICS[merc['house']]}** "
                f"ทิป: เวลาโกรธให้เว้นก่อนพิมพ์หรือพูดสัก 5 นาที จะช่วยลดคำพูดที่ทำร้ายใจคนฟัง"
            ),
        },
        {
            "title": "🥰 4. เวลารักใครเป็นยังไง & สเปกที่แพ้ทาง",
            "text": (
                f"ศุกร์อยู่ราศี{ven['sign_th']} เรือน {ven['house']}{retro_note(ven)} และอังคารอยู่เรือน {mar['house']}. "
                f"{fname} แสดงความรักผ่านเรื่อง **{HOUSE_TOPICS[ven['house']]}** "
                f"ส่วนแรงดึงดูดและความอยากเอาชนะ (อังคาร) ผูกกับเรื่อง **{HOUSE_TOPICS[mar['house']]}** "
                f"คนที่เข้ามาแชร์เรื่องเหล่านี้กับแกได้ มักทำให้ใจสั่นเป็นพิเศษ"
            ),
        },
        {
            "title": "💰 5. พื้นดวงการเงิน & จุดที่ต้องระวัง",
            "text": (
                f"เจ้าเรือน 2 (เรือนเงิน) คือดาว{r2['thai']} อยู่เรือน {r2['house']} ({r2['house_th']}){retro_note(r2)}. "
                f"เงินของ {fname} วนอยู่กับเรื่อง **{HOUSE_TOPICS[r2['house']]}** — {money_note}. "
                f"ทิป: ได้เงินมาแล้วแยกบัญชีเก็บทันที จะช่วยกันเงินรั่วตามอารมณ์"
            ),
        },
        {
            "title": "💼 6. การงาน อาชีพ & คนรอบตัวในที่ทำงาน",
            "text": (
                f"เจ้าเรือน 10 (เรือนการงาน) คือดาว{r10['thai']} อยู่เรือน {r10['house']} ({r10['house_th']}){retro_note(r10)}. "
                f"งานที่ใช้ศักยภาพของ {fname} ได้เต็มที่จะเกี่ยวกับเรื่อง **{HOUSE_TOPICS[r10['house']]}** "
                f"เรื่องคนรอบตัว ให้ดูดาวที่อยู่เรือน 6 และ 7 ประกอบเพิ่มเติมเมื่อต้องการลงลึก"
            ),
        },
    ]
    return with_story_alias(sections)


# -----------------------------------------------------------------------------
# 6. API ENDPOINTS
# -----------------------------------------------------------------------------
@app.get("/")
def index():
    if (ROOT / "index.html").exists():
        return HTMLResponse((ROOT / "index.html").read_text(encoding="utf-8"))
    return {"message": "ROTA Astrology API Ready!"}


@app.get("/api/health")
def health():
    return {"ok": True, "engine": "Swiss Ephemeris", "mode": "Friend Conversational", "version": app.version}


@app.post("/api/natal")
def natal(b: Birth):
    try:
        n = get_natal(b)
        sections = build_natal_friendly_reading(n, b.name)
        return {
            "client_name": b.name,
            "chart_info": {
                "zodiac": b.zodiac,
                "asc_sign": n["angles"]["asc_sign_th"],
                "sun_sign": n["planets"]["Sun"]["sign_th"],
                "moon_sign": n["planets"]["Moon"]["sign_th"],
            },
            "chart": n,
            "sections": sections,
            "disclaimer": DISCLAIMER,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(422, f"ข้อมูลไม่ถูกต้อง: {e}")
    except Exception as e:
        raise HTTPException(500, f"คำนวณดวงไม่สำเร็จ (ข้อผิดพลาดภายในระบบ): {e}")


@app.post("/api/annual")
def annual(req: AnnualRequest):
    try:
        n = get_natal(req)
        fname = get_friendly_name(req.name)

        bd = parse_flexible_date(req.date)
        year = normalize_year(req.annual_year)

        # รอบ profection เริ่มตั้งแต่วันเกิดของปี annual_year
        age = year - bd.year
        if age < 0:
            raise ValueError("ปีที่เลือกอยู่ก่อนปีเกิด")
        if req.as_of:
            as_of = parse_flexible_date(req.as_of)
            if as_of < safe_date(bd.year + age, bd.month, bd.day):
                age -= 1
                if age < 0:
                    raise ValueError("วันที่อ้างอิงอยู่ก่อนวันเกิด")

        period_start = safe_date(bd.year + age, bd.month, bd.day)
        period_end = safe_date(bd.year + age + 1, bd.month, bd.day) - timedelta(days=1)

        house_num = (age % 12) + 1
        asc_idx = n["angles"]["asc_sign_index"]
        sign_idx = (asc_idx + house_num - 1) % 12
        ruler = TRAD_RULER[sign_idx]
        rd = n["planets"][ruler]

        planets_in_house = [p["thai"] for p in n["planets"].values() if p["house"] == house_num]
        planets_txt = (
            "ดาวกำเนิดที่อยู่ในเรือนนี้: " + ", ".join(planets_in_house) + " (จะถูกกระตุ้นเป็นพิเศษ)"
            if planets_in_house else "เรือนนี้ไม่มีดาวกำเนิดอยู่ ให้ดูผ่านดาวผู้ครองปีเป็นหลัก"
        )

        overview = (
            f"รอบปีนี้ {fname} อายุ {age} ปี (รอบ {period_start.isoformat()} ถึง {period_end.isoformat()}) "
            f"เรือนที่ถูกเปิดคือ **เรือนที่ {house_num} ({HOUSE_TH[house_num - 1]}) ราศี{SIGN_TH[sign_idx]}**\n\n"
            f"🎯 **ธีมใหญ่ของปี:** พลังงานชีวิตไปกระจุกที่เรื่อง **'{HOUSE_TOPICS[house_num]}'**\n\n"
            f"🪐 **ดาวผู้ครองปี (Lord of the Year):** ดาว **{PLANET_TH[ruler]}** อยู่เรือนกำเนิดที่ {rd['house']} ({HOUSE_TH[rd['house'] - 1]}){retro_note(rd)}\n\n"
            f"💡 **สแนปชอต:** เรื่อง **{HOUSE_TOPICS[house_num]}** จะเชื่อมโยงกับเรื่อง **{HOUSE_TOPICS[rd['house']]}** ตลอดปีนี้\n\n"
            f"🔎 {planets_txt}"
        )

        r10_en, r10 = ruler_of_house(n, 10)
        r2_en, r2 = ruler_of_house(n, 2)
        r7_en, r7 = ruler_of_house(n, 7)

        work_focus = "ปีนี้เรื่องงานเป็นประเด็นเด่นโดยตรง" if house_num in (6, 10) else "เรื่องงานไม่ใช่ธีมหลักของปีนี้ แต่ยังได้รับอิทธิพลผ่านดาวผู้ครองปี"
        money_focus = "ปีนี้เรื่องเงินเป็นประเด็นเด่นโดยตรง" if house_num in (2, 8, 11) else "เรื่องเงินไม่ใช่ธีมหลักของปีนี้ ให้ดูผ่านการลงมือในเรื่องของเรือนที่เปิด"
        love_focus = "ปีนี้เรื่องความรักและคู่เป็นประเด็นเด่นโดยตรง" if house_num in (5, 7) else "เรื่องความรักไม่ใช่ธีมหลักของปีนี้ แต่ยังเกิดขึ้นได้ผ่านสิ่งที่เรือนปีนี้พาไป"

        sections = with_story_alias([
            {"title": "✨ ภาพรวม & Focus หลักของปีนี้", "text": overview},
            {
                "title": "💼 การงาน & การเรียนปีนี้",
                "text": (
                    f"{work_focus}. เจ้าเรือน 10 ในดวงกำเนิดคือดาว{r10['thai']} อยู่เรือน {r10['house']} "
                    f"จึงต้องดูเรื่อง **{HOUSE_TOPICS[r10['house']]}** ประกอบ "
                    f"ก่อนเซ็นสัญญาหรือเปลี่ยนงาน ควรตรวจรายละเอียดให้รอบคอบ"
                ),
            },
            {
                "title": "💰 การเงิน & โชคลาภปีนี้",
                "text": (
                    f"{money_focus}. เจ้าเรือน 2 คือดาว{r2['thai']} อยู่เรือน {r2['house']} "
                    f"เงินจึงเดินตามเรื่อง **{HOUSE_TOPICS[r2['house']]}** และอย่าลืมกันรายจ่ายแทรกซ้อนจากความเกรงใจ"
                ),
            },
            {
                "title": "❤️ ความรัก & ความสัมพันธ์ปีนี้",
                "text": (
                    f"{love_focus}. เจ้าเรือน 7 คือดาว{r7['thai']} อยู่เรือน {r7['house']} "
                    f"ความสัมพันธ์ปีนี้จึงเกี่ยวกับเรื่อง **{HOUSE_TOPICS[r7['house']]}** "
                    f"ทั้งคนมีคู่และคนโสดควรสังเกตคนที่เข้ามาผ่านเรื่องเหล่านี้"
                ),
            },
        ])

        return {
            "client_name": req.name,
            "annual_year": year,
            "age": age,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "profection_house": house_num,
            "house_th": HOUSE_TH[house_num - 1],
            "sign_th": SIGN_TH[sign_idx],
            "lord_of_year": PLANET_TH[ruler],
            "sections": sections,
            "disclaimer": DISCLAIMER,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(422, f"ข้อมูลไม่ถูกต้อง: {e}")
    except Exception as e:
        raise HTTPException(500, f"คำนวณ Annual Profection ไม่สำเร็จ (ข้อผิดพลาดภายในระบบ): {e}")


@app.post("/api/transit")
def transit(req: TransitRequest):
    try:
        n = get_natal(req)
        fname = get_friendly_name(req.name)
        flags = flags_for(req.zodiac)
        asc_idx = n["angles"]["asc_sign_index"]

        start = parse_flexible_date(req.transit_date)
        trans = planet_positions(jd_for(start.isoformat(), "12:00", req.tz), flags)

        natal_points = {PLANET_TH[k]: n["planets"][k]["longitude"] for k in ASPECT_TARGETS}
        natal_points["ลัคนา"] = n["angles"]["asc"]

        highlights = []
        for p in SLOW_PLANETS:
            t = trans[p]
            h = house_of(t["longitude"], asc_idx)
            aspects = find_aspects(t["longitude"], natal_points)
            retro = " (ถอยหลัง)" if t["retrograde"] else ""
            story = (
                f"ดาว{PLANET_TH[p]}{retro} กำลังเดินผ่านเรือน {h} ({HOUSE_TH[h - 1]}) ของ {fname} "
                f"→ ช่วงนี้เรื่อง **'{HOUSE_TOPICS[h]}'** จะมีบททดสอบหรือโอกาสใหม่ให้จัดการเป็นพิเศษ"
            )
            if aspects:
                txt = ", ".join(f"{a['aspect']}{a['to']}ในดวงกำเนิด (ห่าง {a['orb']}°)" for a in aspects)
                story += f" และทำมุม: {txt}"
            highlights.append({
                "planet": PLANET_TH[p],
                "house": h,
                "house_th": HOUSE_TH[h - 1],
                "topic": HOUSE_TOPICS[h],
                "retrograde": t["retrograde"],
                "aspects": aspects,
                "story": story,
                "text": story,
            })

        # ไทม์ไลน์การย้ายเรือนของดาวใหญ่ตลอด months เดือน (สุ่มตรวจทุก 10 วัน)
        step = 10
        steps = (req.months * 30) // step
        prev, timeline = {}, []
        for i in range(steps + 1):
            d = start + timedelta(days=i * step)
            pos = planet_positions(jd_for(d.isoformat(), "12:00", req.tz), flags)
            for p in SLOW_PLANETS:
                h = house_of(pos[p]["longitude"], asc_idx)
                if p in prev and prev[p] != h:
                    timeline.append({
                        "date_approx": d.isoformat(),
                        "planet": PLANET_TH[p],
                        "from_house": prev[p],
                        "to_house": h,
                        "topic": HOUSE_TOPICS[h],
                        "note": "วันที่โดยประมาณ ±10 วัน",
                    })
                prev[p] = h

        return {
            "client_name": req.name,
            "transit_date": start.isoformat(),
            "months": req.months,
            "overview": f"เช็กดวงดาวจร ณ วันที่ {start.isoformat()} สำหรับ {fname}! ดาวใหญ่ตอนนี้อยู่ตำแหน่งดังนี้:",
            "highlights": highlights,
            "timeline": timeline,
            "disclaimer": DISCLAIMER,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(422, f"ข้อมูลไม่ถูกต้อง: {e}")
    except Exception as e:
        raise HTTPException(500, f"คำนวณ Transit ไม่สำเร็จ (ข้อผิดพลาดภายในระบบ): {e}")


if (ROOT / "static").exists():
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
