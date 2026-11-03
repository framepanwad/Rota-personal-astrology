from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import swisseph as swe
from pathlib import Path

ROOT = Path(__file__).parent
app = FastAPI(title="ROTA Personal Astrology", version="2.0.0")

PLANETS = [
    ("Sun", swe.SUN, "อาทิตย์", "☉"),
    ("Moon", swe.MOON, "จันทร์", "☽"),
    ("Mercury", swe.MERCURY, "พุธ", "☿"),
    ("Venus", swe.VENUS, "ศุกร์", "♀"),
    ("Mars", swe.MARS, "อังคาร", "♂"),
    ("Jupiter", swe.JUPITER, "พฤหัสบดี", "♃"),
    ("Saturn", swe.SATURN, "เสาร์", "♄"),
    ("Uranus", swe.URANUS, "ยูเรนัส", "♅"),
    ("Neptune", swe.NEPTUNE, "เนปจูน", "♆"),
    ("Pluto", swe.PLUTO, "พลูโต", "♇"),
]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_TH = [
    "เมษ", "พฤษภ", "เมถุน", "กรกฎ", "สิงห์", "กันย์",
    "ตุล", "พิจิก", "ธนู", "มังกร", "กุมภ์", "มีน"
]

SIGN_GLYPH = [
    "♈", "♉", "♊", "♋", "♌", "♍",
    "♎", "♏", "♐", "♑", "♒", "♓"
]

TRAD_RULER = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
]

HOUSE_TH = [
    "ตนุ", "กดุมภะ", "สหัชชะ", "พันธุ", "ปุตตะ", "อริ",
    "ปัตนิ", "มรณะ", "ศุภะ", "กัมมะ", "ลาภะ", "วินาศ"
]

ASPECTS = [
    (0, "Conjunction", "กุม"),
    (60, "Sextile", "โยค 60°"),
    (90, "Square", "ฉาก"),
    (120, "Trine", "ตรีโกณ"),
    (180, "Opposition", "เล็ง")
]

FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED


class Birth(BaseModel):
    date: str
    time: str
    place: str = "Udon Thani, Thailand"
    lat: float = Field(17.4138, ge=-90, le=90)
    lon: float = Field(102.7872, ge=-180, le=180)
    tz: float = Field(7.0, ge=-12, le=14)


class TransitRequest(Birth):
    transit_date: str


def jd_for(local_date, local_time, tz):
    dt = datetime.fromisoformat(f"{local_date}T{local_time}:00")
    utc = dt - timedelta(hours=tz)
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    return swe.julday(
        utc.year, utc.month, utc.day, hour, swe.GREG_CAL
    )


def planet_positions(jd):
    result = {}

    for en, pid, th, glyph in PLANETS:
        xx, ret = swe.calc_ut(jd, pid, FLAGS)
        lon, lat, dist, speed_lon = xx[:4]

        idx = int(lon // 30) % 12
        deg = lon % 30

        result[en] = {
            "name": en,
            "thai": th,
            "glyph": glyph,
            "longitude": round(lon, 6),
            "sign": SIGNS[idx],
            "sign_th": SIGN_TH[idx],
            "glyph_sign": SIGN_GLYPH[idx],
            "degree": round(deg, 2),
            "minute": int((deg % 1) * 60),
            "retrograde": speed_lon < 0,
            "speed": round(speed_lon, 5)
        }

    return result


def house_data(jd, lat, lon):
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W')

    asc = ascmc[0] % 360
    mc = ascmc[1] % 360
    asc_sign = int(asc // 30)

    houses = []

    for i in range(12):
        sign_idx = (asc_sign + i) % 12

        houses.append({
            "house": i + 1,
            "sign": SIGNS[sign_idx],
            "sign_th": SIGN_TH[sign_idx],
            "glyph": SIGN_GLYPH[sign_idx],
            "ruler": TRAD_RULER[sign_idx],
            "meaning": HOUSE_TH[i]
        })

    return {
        "asc": asc,
        "asc_sign": SIGNS[asc_sign],
        "asc_sign_th": SIGN_TH[asc_sign],
        "asc_glyph": SIGN_GLYPH[asc_sign],
        "asc_degree": round(asc % 30, 2),
        "mc": mc,
        "houses": houses
    }


def aspect_list(transits, natal, max_orb=5):
    found = []

    for tname, t in transits.items():
        for nname, n in natal.items():
            diff = abs(
                (t["longitude"] - n["longitude"] + 180) % 360 - 180
            )

            for angle, en, th in ASPECTS:
                orb = abs(diff - angle)

                if orb <= max_orb:
                    found.append({
                        "transit": tname,
                        "transit_th": t["thai"],
                        "natal": nname,
                        "natal_th": n["thai"],
                        "aspect": en,
                        "aspect_th": th,
                        "orb": round(orb, 2),
                        "separation": round(diff, 2)
                    })

    found.sort(key=lambda x: x["orb"])
    return found


def get_natal(b: Birth):
    jd = jd_for(b.date, b.time, b.tz)

    planets = planet_positions(jd)
    houses = house_data(jd, b.lat, b.lon)

    for p in planets.values():
        p["house"] = (
            int((p["longitude"] // 30) - int(houses["asc"] // 30)) % 12
        ) + 1
        p["house_th"] = HOUSE_TH[p["house"] - 1]

    return {
        "julian_day": jd,
        "planets": list(planets.values()),
        "planet_map": planets,
        "angles": houses,
        "aspects": aspect_list(planets, planets, max_orb=0.15)
    }


@app.get("/")
def index():
    return HTMLResponse(
        (ROOT / "index.html").read_text(encoding="utf-8")
    )


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "engine": "Swiss Ephemeris via Moshier",
        "version": swe.version
    }


@app.post("/api/natal")
def natal(b: Birth):
    try:
        n = get_natal(b)

        return {
            "birth": b.model_dump(),
            "chart": n,
            "engine_note": (
                "คำนวณตำแหน่งดาวด้วย Swiss Ephemeris / Moshier; "
                "Tropical zodiac; Whole Sign Houses."
            )
        }

    except Exception as e:
        raise HTTPException(400, f"คำนวณดวงไม่สำเร็จ: {e}")


@app.post("/api/transit")
def transit(req: TransitRequest):
    try:
        n = get_natal(req)

        jd = jd_for(req.transit_date, "12:00", req.tz)
        trans = planet_positions(jd)
        tomorrow = planet_positions(jd + 1)

        aspects = aspect_list(trans, n["planet_map"], 5)

        for a in aspects:
            t = a["transit"]
            natal_name = a["natal"]

            diff1 = abs(
                (
                    tomorrow[t]["longitude"]
                    - n["planet_map"][natal_name]["longitude"]
                    + 180
                ) % 360 - 180
            )

            angle = next(
                x[0] for x in ASPECTS if x[1] == a["aspect"]
            )

            orb1 = abs(diff1 - angle)

            a["motion"] = (
                "Applying" if orb1 < a["orb"]
                else "Separating" if orb1 > a["orb"]
                else "Near exact"
            )

            a["motion_th"] = {
                "Applying": "กำลังเข้าใกล้มุมสนิท",
                "Separating": "กำลังแยกออกจากมุมสนิท",
                "Near exact": "ใกล้มุมสนิท"
            }[a["motion"]]

        return {
            "date": req.transit_date,
            "transits": list(trans.values()),
            "aspects": aspects[:60],
            "natal_angles": n["angles"],
            "natal_planets": n["planet_map"],
            "engine_note": (
                "Transit positions calculated for 12:00 local time; "
                "aspect motion estimated from next-day movement."
            )
        }

    except Exception as e:
        raise HTTPException(400, f"คำนวณ Transit ไม่สำเร็จ: {e}")


class AnnualRequest(Birth):
    annual_year: int = Field(..., ge=1900, le=2200)


PLANET_MEANING = {
    "Sun": "ตัวตน ความมุ่งหมาย อำนาจ การยอมรับ และผู้มีอำนาจ",
    "Moon": "ความต้องการ ความมั่นคง บ้าน ครอบครัว และการเปลี่ยนแปลง",
    "Mercury": "การคิด การสื่อสาร การเรียนรู้ เอกสาร และการเจรจา",
    "Venus": "ความรัก ความสัมพันธ์ ความพึงพอใจ เงินที่ใช้เพื่อความสุข และการประนีประนอม",
    "Mars": "แรงผลักดัน การแข่งขัน ความขัดแย้ง การตัดสินใจ และการลงมือ",
    "Jupiter": "การเติบโต ความรู้ ความเชื่อ ผู้สนับสนุน กฎหมาย และโอกาส",
    "Saturn": "ความรับผิดชอบ ข้อจำกัด เวลา โครงสร้าง ภาระ และผลระยะยาว"
}

SIGN_STYLE = {
    "Aries": "เริ่มต้นเร็ว กล้าตัดสินใจ และต้องระวังความใจร้อน",
    "Taurus": "เน้นความมั่นคง ความต่อเนื่อง ทรัพยากร และผลที่จับต้องได้",
    "Gemini": "เน้นข้อมูล การติดต่อ การเรียนรู้ และการมีหลายทางเลือก",
    "Cancer": "เน้นความปลอดภัย ความผูกพัน บ้าน และการดูแล",
    "Leo": "เน้นความภาคภูมิใจ ความคิดสร้างสรรค์ การแสดงตัว และการยอมรับ",
    "Virgo": "เน้นรายละเอียด ระบบ งานบริการ การวิเคราะห์ และการปรับปรุง",
    "Libra": "เน้นความร่วมมือ คู่สัญญา ความยุติธรรม และการประนีประนอม",
    "Scorpio": "เน้นเรื่องลึกซึ้ง การเปลี่ยนผ่าน ทรัพยากรร่วม และการควบคุม",
    "Sagittarius": "เน้นการขยายขอบเขต การศึกษา การเดินทาง และความเชื่อ",
    "Capricorn": "เน้นเป้าหมายระยะยาว วินัย หน้าที่ และความเป็นมืออาชีพ",
    "Aquarius": "เน้นเครือข่าย กลุ่มคน ระบบ ความคิดอิสระ และการเปลี่ยนแปลง",
    "Pisces": "เน้นจินตนาการ ความเมตตา การปล่อยวาง และขอบเขตที่ชัดเจน"
}

PLANET_HOUSE = {
    1: "ตัวตน สุขภาพกาย ภาพลักษณ์ และการเริ่มต้นด้วยตนเอง",
    2: "รายได้ ทรัพย์สิน เงินเก็บ ทักษะ และคุณค่าที่ตนสร้าง",
    3: "การสื่อสาร การเรียนระยะสั้น พี่น้อง เพื่อนบ้าน และการเดินทางใกล้",
    4: "บ้าน ครอบครัว รากฐาน อสังหาริมทรัพย์ และชีวิตส่วนตัว",
    5: "ความรักแบบโรแมนติก ความสร้างสรรค์ บุตร งานอดิเรก และความเสี่ยงเพื่อความสนุก",
    6: "งานประจำ ภาระ งานบริการ ลูกน้อง สุขภาพประจำวัน และกิจวัตร",
    7: "คู่ครอง หุ้นส่วน ลูกค้า คู่สัญญา และคู่ขัดแย้งที่เปิดเผย",
    8: "เงินของผู้อื่น หนี้ ภาษี มรดก ความไว้วางใจ และเรื่องที่ต้องแบ่งปัน",
    9: "การศึกษาสูง ต่างประเทศ การเดินทางไกล กฎหมาย ศาสนา และความหมายชีวิต",
    10: "อาชีพ ชื่อเสียง สถานะ เป้าหมายสาธารณะ และผู้บังคับบัญชา",
    11: "เพื่อน เครือข่าย ผู้สนับสนุน รายได้จากอาชีพ และความหวัง",
    12: "เรื่องเบื้องหลัง การพักฟื้น ความโดดเดี่ยว ค่าใช้จ่ายแฝง และสิ่งที่ควบคุมยาก"
}

DOMICILE = {
    "Mars": ["Aries", "Scorpio"],
    "Venus": ["Taurus", "Libra"],
    "Mercury": ["Gemini", "Virgo"],
    "Moon": ["Cancer"],
    "Sun": ["Leo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn": ["Capricorn", "Aquarius"]
}

EXALTATION = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Jupiter": "Cancer",
    "Mercury": "Virgo",
    "Saturn": "Libra",
    "Mars": "Capricorn",
    "Venus": "Pisces"
}

DETRIMENT = {
    "Sun": ["Aquarius"],
    "Moon": ["Capricorn"],
    "Mercury": ["Sagittarius", "Pisces"],
    "Venus": ["Aries", "Scorpio"],
    "Mars": ["Taurus", "Libra"],
    "Jupiter": ["Gemini", "Virgo"],
    "Saturn": ["Cancer", "Leo"]
}

FALL = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Jupiter": "Capricorn",
    "Mercury": "Pisces",
    "Saturn": "Aries",
    "Mars": "Cancer",
    "Venus": "Virgo"
}


def dignity_of(planet, sign):
    if sign in DOMICILE.get(planet, []):
        return (
            "เกษตร (Domicile)",
            "ดาวอยู่ในราศีที่ตนปกครอง จึงมีศักยภาพใช้คุณสมบัติของตนได้อย่างเป็นธรรมชาติ"
        )

    if EXALTATION.get(planet) == sign:
        return (
            "อุจจ์ (Exaltation)",
            "ดาวอยู่ในตำแหน่งอุจจ์ มีศักยภาพเด่น แต่ยังต้องพิจารณาเรือนและมุมสัมพันธ์ประกอบ"
        )

    if sign in DETRIMENT.get(planet, []):
        return (
            "ประ (Detriment)",
            "ดาวอยู่ตรงข้ามราศีเกษตร จึงอาจต้องปรับวิธีใช้พลังและเผชิญเงื่อนไขมากขึ้น"
        )

    if FALL.get(planet) == sign:
        return (
            "นิจ (Fall)",
            "ดาวอยู่ตรงข้ามตำแหน่งอุจจ์ จึงควรใช้เวลาและวินัยในการพัฒนาคุณภาพของดาว"
        )

    return (
        "ไม่มี Essential Dignity หลักตามชุดที่ใช้",
        "ไม่ควรตีความว่าเสียหรือดีโดยอัตโนมัติ ต้องอ่านจากเรือน Sect และมุมสัมพันธ์ร่วมกัน"
    )


def annual_aspects(lord, planets):
    rows = []

    for name, p in planets.items():
        if name == lord:
            continue

        diff = abs(
            (planets[lord]["longitude"] - p["longitude"] + 180) % 360 - 180
        )

        for angle, en, th in ASPECTS:
            orb = abs(diff - angle)

            if orb <= 6:
                rows.append({
                    "planet": name,
                    "thai": p["thai"],
                    "aspect": en,
                    "aspect_th": th,
                    "orb": round(orb, 2)
                })

    return sorted(rows, key=lambda x: x["orb"])


def annual_reading(req, n, house_num, sign_idx, ruler, ruler_data):
    planets = n["planet_map"]
    sun = planets["Sun"]

    sect = (
        "กลางวัน (Day chart)"
        if sun["house"] in range(7, 13)
        else "กลางคืน (Night chart)"
    )

    benefic = "Jupiter" if sect.startswith("กลางวัน") else "Venus"
    malefic = "Mars" if sect.startswith("กลางวัน") else "Saturn"

    dignity, dignity_note = dignity_of(ruler, ruler_data["sign"])
    aspects = annual_aspects(ruler, planets)

    aspect_text = []

    for a in aspects:
        tone = (
            "เป็นมุมสนับสนุน"
            if a["aspect"] in ("Trine", "Sextile")
            else "เป็นมุมที่ต้องจัดการแรงตึงเครียด"
            if a["aspect"] in ("Square", "Opposition")
            else "เป็นการรวมพลัง"
        )

        aspect_text.append(
            f"{a['thai']} {a['aspect_th']} กับดาวเจ้าเรือนปี "
            f"{ruler} (orb {a['orb']}°) — {tone}"
        )

    house_topic = PLANET_HOUSE[house_num]
    ruler_topic = PLANET_HOUSE[ruler_data["house"]]
    lord_th = ruler_data["thai"]

    start = f"{req.annual_year}-{req.date[5:]}"
    end = f"{req.annual_year + 1}-{req.date[5:]}"

    overview = (
        f"ปีอายุ {req.annual_year - int(req.date[:4])} เป็นปีเรือนที่ "
        f"{house_num} ({HOUSE_TH[house_num-1]}) "
        f"ในราศี {SIGN_TH[sign_idx]} โดยมี {lord_th} เป็น Lord of the Year. "
        f"ธีมหลักจึงเริ่มจาก {house_topic} และต้องอ่านผ่านตำแหน่งกำเนิดของ "
        f"{lord_th} ซึ่งอยู่เรือนที่ {ruler_data['house']} "
        f"({ruler_data['house_th']}) — {ruler_topic}. "
        f"ราศี {ruler_data['sign_th']} เพิ่มโทนว่า{SIGN_STYLE[ruler_data['sign']]}"
    )

    sections = [
        {
            "title": "ภาพรวมและธีมหลักของปี",
            "text": overview +
            f" ช่วงเวลาที่ใช้คือ {start} ถึง {end} "
            f"(วันเกิดถึงวันเกิด) ดังนั้นนี่คือกรอบปี profection ไม่ใช่ปีปฏิทินเต็มปี."
        },
        {
            "title": "Lord of the Year — ดาวผู้คุมธีมปี",
            "text": (
                f"{lord_th} อยู่ราศี {ruler_data['sign_th']} "
                f"{ruler_data['degree']:.2f}° ในเรือนกำเนิดที่ "
                f"{ruler_data['house']} ({ruler_data['house_th']}) "
                f"และมีสถานะ{'ถอยหลัง (Rx)' if ruler_data['retrograde'] else 'เดินหน้า'}. "
                f"คุณภาพพื้นฐาน: {dignity}. {dignity_note}. "
                f"เรื่องของดาวนี้ ({PLANET_MEANING.get(ruler, 'การจัดการและการตัดสินใจ')}) "
                f"จะเป็นกลไกสำคัญที่พาเรื่องของเรือนประจำปีไปสู่เหตุการณ์จริง "
                f"โดยเรือน {ruler_data['house']} เป็นเวทีที่ควรให้ความสนใจเป็นพิเศษ."
            )
        },
        {
            "title": "Sect — พื้นดวงกลางวัน/กลางคืน",
            "text": (
                f"ดวงนี้เป็น {sect} โดยพิจารณาจากตำแหน่ง Sun ในเรือน {sun['house']}. "
                f"ดาว Benefic of Sect คือ {benefic} และดาว Malefic of Sect คือ {malefic}. "
                f"การประเมินความง่าย/ยากของดาวต้องดูเงื่อนไขทั้งดวง ไม่ใช้ Sect เพียงข้อเดียวตัดสินผลลัพธ์."
            )
        },
        {
            "title": "การงานและสถานะ",
            "text": (
                f"พิจารณาเรือนที่ 10 (กัมมะ) ควบคู่กับเรือนประจำปีที่ {house_num} "
                f"และตำแหน่ง {lord_th} ในเรือน {ruler_data['house']}. "
                f"ปีนี้ควรวางแผนเรื่องหน้าที่ ความรับผิดชอบ เป้าหมายอาชีพ "
                f"และความสัมพันธ์กับผู้มีอำนาจให้สอดคล้องกับธีม {house_topic}. "
                f"หากงานเกี่ยวข้องกับเรื่อง {ruler_topic} การเปลี่ยนแปลงในด้านนั้นอาจส่งผลต่อทิศทางงานได้มากเป็นพิเศษ."
            )
        },
        {
            "title": "การเงินและทรัพย์สิน",
            "text": (
                f"เรือนที่ 2 (กดุมภะ) สะท้อนรายได้และทรัพย์สิน ส่วนเรือนที่ 8 "
                f"(มรณะ) สะท้อนหนี้ ภาษี และทรัพยากรร่วม. "
                f"ใช้ตำแหน่ง {lord_th} ในเรือน {ruler_data['house']} "
                f"เป็นตัวเชื่อมว่าประเด็นการเงินอาจพัวพันกับ {ruler_topic}. "
                f"คำแนะนำเชิงปฏิบัติคือแยกเงินใช้ เงินสำรอง และภาระผูกพัน "
                f"ตรวจสัญญาและต้นทุนก่อนตัดสินใจลงทุน."
            )
        },
        {
            "title": "ความรักและความสัมพันธ์",
            "text": (
                f"เรือนที่ 7 (ปัตนิ) เป็นจุดหลักของคู่ครอง หุ้นส่วน ลูกค้า คู่สัญญา "
                f"และเรือนที่ 5 (ปุตตะ) ช่วยอ่านความรักเชิงโรแมนติกและความสุข. "
                f"นำธีมเรือนประจำปี {HOUSE_TH[house_num-1]} "
                f"มาพิจารณาร่วมกับตำแหน่ง {lord_th} ในเรือน {ruler_data['house']}. "
                f"ปีนี้เหมาะกับการทำความคาดหวัง ขอบเขต และข้อตกลงให้ชัด "
                f"แทนการคาดเดาความคิดของอีกฝ่าย."
            )
        },
        {
            "title": "บ้าน ครอบครัว และชีวิตส่วนตัว",
            "text": (
                f"เรือนที่ 4 (พันธุ) เกี่ยวกับบ้าน ครอบครัว รากฐาน และอสังหาริมทรัพย์. "
                f"หากเรื่องเรือนที่ 4 เชื่อมกับเรือนประจำปีหรือเรือน "
                f"{ruler_data['house']} ผ่านดาวเจ้าเรือน/มุมสัมพันธ์ "
                f"จะเป็นตัวบ่งชี้ว่าชีวิตส่วนตัวมีบทบาทต่อปีนี้. "
                f"ควรจัดระบบภาระในบ้านและวางแผนเรื่องที่อยู่อาศัยอย่างเป็นขั้นตอน."
            )
        },
        {
            "title": "สุขภาพ กิจวัตร และพลังงาน",
            "text": (
                f"เรือนที่ 6 (อริ) ใช้อ่านงานประจำ ภาระ และสุขภาพเชิงกิจวัตร "
                f"ส่วนเรือนที่ 1 ใช้อ่านร่างกายและตัวตน. "
                f"การอ่านนี้ไม่ใช่การวินิจฉัยโรค; ในทางปฏิบัติควรให้ความสำคัญกับการพักผ่อน "
                f"ตารางชีวิต และการตรวจสุขภาพตามความเหมาะสม. "
                f"อย่าใช้คำพยากรณ์แทนคำแนะนำจากบุคลากรทางการแพทย์."
            )
        },
        {
            "title": "มุมสัมพันธ์ของ Lord of the Year",
            "text": (
                "พบมุมสัมพันธ์: " + "; ".join(aspect_text)
                if aspect_text else
                "ไม่พบ Conjunction, Sextile, Square, Trine หรือ Opposition "
                "ภายใน orb 6° ระหว่าง Lord of the Year กับดาวกำเนิดดวงอื่นในชุดที่คำนวณได้ "
                "จึงไม่ควรสร้างมุมสัมพันธ์ขึ้นมาเอง."
            )
        },
        {
            "title": "แนวทางใช้ปีนี้ให้เกิดประโยชน์",
            "text": (
                f"1) ให้ความสำคัญกับเรื่อง {house_topic}. "
                f"2) จัดการเรื่อง {ruler_topic} ซึ่งเป็นตำแหน่งของดาวเจ้าเรือนปี. "
                f"3) ใช้จุดแข็งของ {lord_th} ในราศี {ruler_data['sign_th']} "
                f"คือ{SIGN_STYLE[ruler_data['sign']]}. "
                f"4) ทบทวนการตัดสินใจสำคัญจากข้อมูลจริง สัญญา และทรัพยากรที่มี "
                f"ไม่ตัดสินใจจากความกลัวหรือความคาดหวังเพียงอย่างเดียว."
            )
        }
    ]

    return {
        "sect": sect,
        "benefic_of_sect": benefic,
        "malefic_of_sect": malefic,
        "dignity": dignity,
        "dignity_note": dignity_note,
        "aspects": aspects,
        "sections": sections
    }


@app.post("/api/annual")
def annual(req: AnnualRequest):
    try:
        n = get_natal(req)

        birth_year = int(req.date[:4])
        age = req.annual_year - birth_year

        if age < 0:
            raise ValueError("ปีที่เลือกอยู่ก่อนปีเกิด")

        house_num = (age % 12) + 1

        asc_idx = SIGNS.index(n["angles"]["asc_sign"])
        sign_idx = (asc_idx + house_num - 1) % 12

        sign = SIGNS[sign_idx]
        ruler = TRAD_RULER[sign_idx]
        ruler_data = n["planet_map"][ruler]

        reading = annual_reading(
            req, n, house_num, sign_idx, ruler, ruler_data
        )

        return {
            "year": req.annual_year,
            "age": age,
            "profection_house": house_num,
            "house_th": HOUSE_TH[house_num - 1],
            "sign": sign,
            "sign_th": SIGN_TH[sign_idx],
            "sign_glyph": SIGN_GLYPH[sign_idx],
            "lord_of_year": ruler,
            "lord_position": ruler_data,
            "ascendant": n["angles"],
            "natal_planets": n["planets"],
            "annual_period": {
                "start": f"{req.annual_year}-{req.date[5:]}",
                "end": f"{req.annual_year + 1}-{req.date[5:]}"
            },
            "reading": reading
        }

    except Exception as e:
        raise HTTPException(
            400, f"คำนวณ Annual Profection ไม่สำเร็จ: {e}"
        )


@app.post("/api/ask")
def ask(payload: dict):
    try:
        b = Birth(**payload["birth"])
        question = str(payload.get("question", "")).strip()

        if not question:
            raise ValueError("กรุณาพิมพ์คำถาม")

        n = get_natal(b)
        asc = n["angles"]
        planets = n["planet_map"]

        lord = TRAD_RULER[SIGNS.index(asc["asc_sign"])]
        lord_data = planets[lord]

        focus = (
            "การงาน"
            if any(x in question for x in ["งาน", "อาชีพ", "ธุรกิจ", "career", "work"])
            else "การเงิน"
            if any(x in question for x in ["เงิน", "การเงิน", "รายได้", "ทรัพย์", "finance", "money"])
            else "ความสัมพันธ์"
            if any(x in question for x in ["รัก", "คู่", "แฟน", "ความสัมพันธ์", "relationship", "love"])
            else "ภาพรวมชีวิต"
        )

        answer = (
            f"ข้อมูลพื้นดวงที่ใช้ประกอบคำถาม: ลัคนา {asc['asc_sign_th']} "
            f"({asc['asc_sign']}) องศา {asc['asc_degree']}° "
            f"และดาวเจ้าเรือนลัคนาคือ {lord} อยู่ราศี {lord_data['sign_th']} "
            f"เรือนที่ {lord_data['house']} ({lord_data['house_th']}).\n\n"
            f"หัวข้อที่ระบบจัดกลุ่ม: {focus}\n\n"
            "นี่เป็นการสรุปข้อเท็จจริงจากตำแหน่งดาวและโครงสร้างเรือนที่คำนวณได้ "
            "ยังไม่ใช่คำพยากรณ์จาก AI"
        )

        return {
            "question": question,
            "answer": answer,
            "facts": {
                "ascendant": asc,
                "asc_ruler": lord,
                "ruler_position": lord_data
            }
        }

    except Exception as e:
        raise HTTPException(
            400, f"ประมวลผลคำถามไม่สำเร็จ: {e}"
        )


app.mount("/static", StaticFiles(directory=ROOT), name="static")
