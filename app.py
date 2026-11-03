
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import swisseph as swe
from pathlib import Path

ROOT = Path(__file__).parent
app = FastAPI(title="ROTA Personal Astrology", version="3.0.0")

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

PLANET_IDS = {p[0]: p[1] for p in PLANETS}
PLANET_TH = {p[0]: p[2] for p in PLANETS}
PLANET_GLYPH = {p[0]: p[3] for p in PLANETS}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn",
    "Aquarius", "Pisces"
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

HOUSE_TOPICS = {
    1: "ตัวตน ร่างกาย ภาพลักษณ์ และการเริ่มต้นด้วยตัวเอง",
    2: "รายได้ เงินเก็บ ทรัพย์สิน และคุณค่าที่เราสร้าง",
    3: "การสื่อสาร เอกสาร การเรียนระยะสั้น พี่น้อง และการเดินทางใกล้",
    4: "บ้าน ครอบครัว ที่อยู่อาศัย และรากฐานชีวิต",
    5: "ความรักแบบโรแมนติก ความสนุก งานสร้างสรรค์ และบุตร",
    6: "งานประจำ ภาระ ตารางชีวิต สุขภาพประจำวัน และงานบริการ",
    7: "คู่ครอง หุ้นส่วน ลูกค้า สัญญา และคู่ขัดแย้งที่เปิดเผย",
    8: "เงินร่วม หนี้ ภาษี มรดก ภาระของอีกฝ่าย และความไว้วางใจ",
    9: "ต่างประเทศ การเดินทางไกล การศึกษาสูง กฎหมาย และความเชื่อ",
    10: "อาชีพ ตำแหน่ง ชื่อเสียง เป้าหมาย และผู้บังคับบัญชา",
    11: "รายได้จากอาชีพ เครือข่าย เพื่อน ผู้สนับสนุน และเป้าหมายระยะยาว",
    12: "เรื่องเบื้องหลัง การพักฟื้น ความโดดเดี่ยว ค่าใช้จ่ายแฝง และสิ่งที่ควบคุมยาก"
}

PLANET_MEANING = {
    "Sun": "ตัวตน ความมุ่งหมาย อำนาจ การยอมรับ และผู้มีอำนาจ",
    "Moon": "ความต้องการ ความมั่นคง บ้าน ครอบครัว และความเปลี่ยนแปลง",
    "Mercury": "การคิด การสื่อสาร การเรียนรู้ เอกสาร และการเจรจา",
    "Venus": "ความรัก ความสัมพันธ์ ความพึงพอใจ เงินที่ใช้เพื่อความสุข และการประนีประนอม",
    "Mars": "แรงผลักดัน การแข่งขัน ความขัดแย้ง การตัดสินใจ และการลงมือ",
    "Jupiter": "การเติบโต โอกาส ความรู้ ผู้สนับสนุน และการขยายขอบเขต",
    "Saturn": "ความรับผิดชอบ ข้อจำกัด เวลา โครงสร้าง ภาระ และผลระยะยาว",
    "Uranus": "การเปลี่ยนแปลงฉับพลัน อิสรภาพ เทคโนโลยี และการหลุดจากรูปแบบเดิม",
    "Neptune": "อุดมคติ จินตนาการ ความคลุมเครือ ความเมตตา และสิ่งที่ยังมองไม่ชัด",
    "Pluto": "อำนาจ การควบคุม การเปลี่ยนแปลงเชิงลึก และการปิดฉากเพื่อเริ่มใหม่"
}

SIGN_STYLE = {
    "Aries": "ตรงไปตรงมา เร็ว กล้าเริ่ม และต้องระวังความใจร้อน",
    "Taurus": "ค่อยเป็นค่อยไป เน้นความมั่นคง ทรัพยากร และผลที่จับต้องได้",
    "Gemini": "เน้นข้อมูล การติดต่อ การเรียนรู้ และการมีหลายทางเลือก",
    "Cancer": "เน้นความปลอดภัย บ้าน ครอบครัว และความผูกพัน",
    "Leo": "เน้นความภาคภูมิใจ การแสดงตัว ความคิดสร้างสรรค์ และการยอมรับ",
    "Virgo": "เน้นรายละเอียด ระบบ งานบริการ การวิเคราะห์ และการปรับปรุง",
    "Libra": "เน้นความร่วมมือ คู่สัญญา ความยุติธรรม และการประนีประนอม",
    "Scorpio": "เน้นเรื่องลึกซึ้ง ทรัพยากรร่วม ความไว้ใจ และการเปลี่ยนผ่าน",
    "Sagittarius": "เน้นการขยายขอบเขต การศึกษา ต่างประเทศ และความเชื่อ",
    "Capricorn": "เน้นเป้าหมายระยะยาว วินัย หน้าที่ และความเป็นมืออาชีพ",
    "Aquarius": "เน้นเครือข่าย กลุ่มคน ระบบ ความคิดอิสระ และการเปลี่ยนแปลง",
    "Pisces": "เน้นจินตนาการ ความเมตตา การปล่อยวาง และขอบเขตที่ต้องชัดเจน"
}

ASPECTS = [
    (0, "Conjunction", "กุม"),
    (60, "Sextile", "โยค 60°"),
    (90, "Square", "ฉาก"),
    (120, "Trine", "ตรีโกณ"),
    (180, "Opposition", "เล็ง")
]

FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED
SLOW_PLANETS = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


class Birth(BaseModel):
    date: str
    time: str
    place: str = "Udon Thani, Thailand"
    lat: float = Field(17.4138, ge=-90, le=90)
    lon: float = Field(102.7872, ge=-180, le=180)
    tz: float = Field(7.0, ge=-12, le=14)


class TransitRequest(Birth):
    transit_date: str
    months: int = Field(12, ge=1, le=24)


class AnnualRequest(Birth):
    annual_year: int = Field(..., ge=1900, le=2200)


def jd_for(local_date, local_time="12:00", tz=7.0):
    dt = datetime.fromisoformat(f"{local_date}T{local_time}:00")
    utc = dt - timedelta(hours=tz)
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60 + utc.second / 3600,
        swe.GREG_CAL
    )


def wrapdiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def sign_index(lon):
    return int((lon % 360) // 30)


def house_of(lon, asc_sign_idx):
    return ((sign_index(lon) - asc_sign_idx) % 12) + 1


def fmt_date(d):
    return d.strftime("%d %b %Y")


def planet_positions(jd):
    out = {}

    for en, pid, th, glyph in PLANETS:
        xx, _ = swe.calc_ut(jd, pid, FLAGS)
        lon, lat, dist, speed = xx[:4]

        si = sign_index(lon)
        deg = lon % 30

        out[en] = {
            "name": en,
            "thai": th,
            "glyph": glyph,
            "longitude": round(lon % 360, 6),
            "sign": SIGNS[si],
            "sign_th": SIGN_TH[si],
            "glyph_sign": SIGN_GLYPH[si],
            "degree": round(deg, 2),
            "minute": int((deg % 1) * 60),
            "retrograde": speed < 0,
            "speed": round(speed, 6)
        }

    return out


def house_data(jd, lat, lon):
    _, ascmc = swe.houses_ex(jd, lat, lon, b'W')

    asc = ascmc[0] % 360
    mc = ascmc[1] % 360
    ai = sign_index(asc)

    houses = []

    for i in range(12):
        si = (ai + i) % 12

        houses.append({
            "house": i + 1,
            "sign": SIGNS[si],
            "sign_th": SIGN_TH[si],
            "glyph": SIGN_GLYPH[si],
            "ruler": TRAD_RULER[si],
            "meaning": HOUSE_TH[i],
            "topic": HOUSE_TOPICS[i + 1]
        })

    return {
        "asc": asc,
        "asc_sign": SIGNS[ai],
        "asc_sign_th": SIGN_TH[ai],
        "asc_glyph": SIGN_GLYPH[ai],
        "asc_degree": round(asc % 30, 2),
        "mc": mc,
        "houses": houses,
        "asc_sign_index": ai
    }


def aspect_list(transits, natal, max_orb=5, skip_same=False):
    found = []

    for tn, t in transits.items():
        for nn, n in natal.items():
            if skip_same and tn == nn:
                continue

            diff = wrapdiff(t["longitude"], n["longitude"])

            for angle, en, th in ASPECTS:
                orb = abs(diff - angle)

                if orb <= max_orb:
                    found.append({
                        "transit": tn,
                        "transit_th": t["thai"],
                        "natal": nn,
                        "natal_th": n["thai"],
                        "aspect": en,
                        "aspect_th": th,
                        "angle": angle,
                        "orb": round(orb, 3),
                        "separation": round(diff, 3)
                    })

    return sorted(found, key=lambda x: x["orb"])


def get_natal(b):
    jd = jd_for(b.date, b.time, b.tz)
    planets = planet_positions(jd)
    angles = house_data(jd, b.lat, b.lon)
    ai = angles["asc_sign_index"]

    for p in planets.values():
        p["house"] = house_of(p["longitude"], ai)
        p["house_th"] = HOUSE_TH[p["house"] - 1]

    aspects = aspect_list(planets, planets, 5, skip_same=True)

    return {
        "julian_day": jd,
        "planets": list(planets.values()),
        "planet_map": planets,
        "angles": angles,
        "aspects": aspects
    }


def sect_data(n):
    sun = n["planet_map"]["Sun"]
    is_day = sun["house"] in range(7, 13)

    return {
        "name": "กลางวัน (Day chart)" if is_day else "กลางคืน (Night chart)",
        "is_day": is_day,
        "benefic": "Jupiter" if is_day else "Venus",
        "malefic": "Mars" if is_day else "Saturn"
    }


def dignity_of(planet, sign):
    domicile = {
        "Mars": ["Aries", "Scorpio"],
        "Venus": ["Taurus", "Libra"],
        "Mercury": ["Gemini", "Virgo"],
        "Moon": ["Cancer"],
        "Sun": ["Leo"],
        "Jupiter": ["Sagittarius", "Pisces"],
        "Saturn": ["Capricorn", "Aquarius"]
    }

    exalt = {
        "Sun": "Aries",
        "Moon": "Taurus",
        "Jupiter": "Cancer",
        "Mercury": "Virgo",
        "Saturn": "Libra",
        "Mars": "Capricorn",
        "Venus": "Pisces"
    }

    detr = {
        "Sun": ["Aquarius"],
        "Moon": ["Capricorn"],
        "Mercury": ["Sagittarius", "Pisces"],
        "Venus": ["Aries", "Scorpio"],
        "Mars": ["Taurus", "Libra"],
        "Jupiter": ["Gemini", "Virgo"],
        "Saturn": ["Cancer", "Leo"]
    }

    fall = {
        "Sun": "Libra",
        "Moon": "Scorpio",
        "Jupiter": "Capricorn",
        "Mercury": "Pisces",
        "Saturn": "Aries",
        "Mars": "Cancer",
        "Venus": "Virgo"
    }

    if sign in domicile.get(planet, []):
        return "เกษตร (Domicile)", "มีความถนัดตามธรรมชาติในเรื่องที่ดาวดวงนี้เป็นตัวแทน"

    if exalt.get(planet) == sign:
        return "อุจจ์ (Exaltation)", "มีศักยภาพโดดเด่น แต่ต้องดูเรือนและมุมสัมพันธ์ประกอบ"

    if sign in detr.get(planet, []):
        return "ประ (Detriment)", "ต้องปรับวิธีใช้พลังของดาว และอาจเจอเงื่อนไขที่ทำให้เรื่องนี้ไม่ไหลลื่น"

    if fall.get(planet) == sign:
        return "นิจ (Fall)", "ต้องใช้เวลาและวินัยพัฒนาคุณภาพของดาว ไม่ได้แปลว่าจะเกิดเรื่องร้ายโดยอัตโนมัติ"

    return (
        "ไม่มี Essential Dignity หลัก",
        "ประเมินจากเรือน Sect และมุมสัมพันธ์ร่วมกัน ไม่ตัดสินว่าดีหรือเสียจากราศีอย่างเดียว"
    )


def natal_summary(n):
    a = n["angles"]
    pm = n["planet_map"]
    sect = sect_data(n)

    asc_ruler = TRAD_RULER[a["asc_sign_index"]]
    rd = pm[asc_ruler]
    dignote = dignity_of(asc_ruler, rd["sign"])

    story = (
        f"ลัคนา{a['asc_sign_th']} ทำให้ดาวเจ้าเรือนลัคนาคือ"
        f"{PLANET_TH[asc_ruler]} ({asc_ruler}) เป็นตัวตั้งต้นในการอ่านชีวิต "
        f"ดาวดวงนี้ไปอยู่เรือน{rd['house']} ({HOUSE_TH[rd['house']-1]}) "
        f"ในราศี{rd['sign_th']} ดังนั้นเรื่องตัวตนและการตัดสินใจมักพัวพันกับ"
        f"{HOUSE_TOPICS[rd['house']]}. "
        "นี่เป็นจุดเชื่อมหลักที่ต้องอ่านร่วมกับดาวอื่น ไม่ใช่คำตัดสินบุคลิกจากลัคนาเพียงอย่างเดียว."
    )

    return {
        "ascendant": a,
        "asc_ruler": asc_ruler,
        "ruler_position": rd,
        "sect": sect,
        "ruler_dignity": dignote,
        "story": story
    }


def transit_orb(planet, aspect):
    if planet in ("Jupiter", "Saturn"):
        return 2.0 if aspect in ("Conjunction", "Opposition", "Square") else 1.5
    if planet in ("Uranus", "Neptune", "Pluto"):
        return 2.0
    if planet == "Mars":
        return 1.0
    return 0.8


def event_story(tname, nname, aspect, house, orb, motion, sect):
    pmeaning = PLANET_MEANING[tname]
    nmeaning = PLANET_MEANING[nname]
    topic = HOUSE_TOPICS[house]

    aspect_tone = {
        "Conjunction": "เรื่องนี้ถูกดึงขึ้นมาอยู่ตรงหน้า ต้องรับมือหรือเริ่มต้นบางอย่าง",
        "Sextile": "มีช่องทางหรือคนช่วย แต่ต้องเป็นฝ่ายหยิบโอกาสและลงมือ",
        "Trine": "เรื่องมีแนวโน้มไหลลื่นขึ้น ได้แรงสนับสนุนหรือเห็นทางออกง่ายขึ้น",
        "Square": "มีแรงกดดันให้แก้ปัญหา จัดลำดับความสำคัญ หรือเปลี่ยนวิธีเดิม",
        "Opposition": "ต้องหาจุดสมดุลระหว่างสองฝ่ายหรือสองความต้องการที่ดึงกันคนละทาง"
    }[aspect]

    timing = (
        "กำลังเข้าใกล้จุดพีก" if motion == "Applying"
        else "ผ่านจุดพีกแล้ว แต่ผลยังค่อย ๆ คลี่คลาย"
        if motion == "Separating"
        else "อยู่ใกล้จุดพีก"
    )

    examples = {
        "Jupiter": "ตัวอย่างเช่น มีคนแนะนำโอกาสใหม่ ได้เรียนรู้สิ่งที่ต่อยอดงาน หรือมีช่องทางที่ทำให้เรื่องนี้ขยายตัว แต่ควรดูต้นทุนและความคาดหวังให้สมจริง",
        "Saturn": "ตัวอย่างเช่น ต้องรับผิดชอบงานหรือข้อตกลงมากขึ้น ต้องวางแผนระยะยาว หรือพบว่าบางอย่างต้องใช้เวลาและวินัยกว่าจะเห็นผล",
        "Uranus": "ตัวอย่างเช่น ตารางหรือแผนเดิมเปลี่ยนกะทันหัน มีข้อเสนอที่ไม่คาดคิด หรือเริ่มอยากหลุดจากวิธีเดิม ๆ ควรเผื่อแผนสำรอง",
        "Neptune": "ตัวอย่างเช่น เรื่องที่เคยคิดว่าชัดอาจยังมีข้อมูลไม่ครบ หรือมีความคาดหวังสูงกว่าความจริง ควรถามให้ชัดและตรวจรายละเอียดก่อนตกลง",
        "Pluto": "ตัวอย่างเช่น ประเด็นเรื่องอำนาจ การควบคุม หรือความไว้ใจที่เคยเลี่ยงอาจต้องคุยกันจริงจัง เป็นช่วงปรับโครงสร้างมากกว่าการแก้ผิวเผิน",
        "Mars": "ตัวอย่างเช่น มีเรื่องเร่งให้ตัดสินใจ แข่งขัน หรือเผชิญหน้ากับปัญหาที่ค้างอยู่ ควรระวังการตอบโต้เร็วเกินไป",
        "Venus": "ตัวอย่างเช่น มีการเจรจาเรื่องความสัมพันธ์ เงิน หรือความพึงพอใจ อาจเป็นจังหวะปรับความเข้าใจหรือทบทวนสิ่งที่ให้คุณค่า",
        "Mercury": "ตัวอย่างเช่น มีข่าว เอกสาร นัดหมาย การพูดคุย หรือการตัดสินใจที่ต้องใช้ข้อมูล ควรตรวจวันเวลาและรายละเอียดให้ครบ",
        "Sun": "ตัวอย่างเช่น เรื่องนี้กลายเป็นจุดสนใจ ต้องแสดงจุดยืน รับผิดชอบ หรือได้รับการมองเห็นมากขึ้น",
        "Moon": "ตัวอย่างเช่น อารมณ์ ความต้องการเรื่องความมั่นคง หรือเรื่องบ้านและครอบครัวทำให้ต้องปรับแผนในช่วงนั้น"
    }[tname]

    return (
        f"ดาวจร{PLANET_TH[tname]} ({tname}) ซึ่งแทนเรื่อง{pmeaning} "
        f"กำลังทำมุม{dict((x[1], x[2]) for x in ASPECTS)[aspect]} "
        f"กับดาวกำเนิด{PLANET_TH[nname]} ({nname}) ที่แทนเรื่อง{nmeaning}. "
        f"จุดนี้ไปกระตุ้นเรือนที่ {house} ซึ่งเกี่ยวกับ{topic}. "
        f"{aspect_tone} {examples} ตอนนี้{timing} (orb {orb:.2f}°) "
        "จึงควรจับตาประเด็นนี้เป็นพิเศษ แต่ไม่ได้หมายความว่าเหตุการณ์จะเกิดแบบเดียวกันกับทุกคน "
        "ต้องดูบริบทชีวิตจริงประกอบ"
    )


def event_intensity(orb, planet, aspect):
    if orb <= 0.25:
        return "สูงมาก"
    if orb <= 0.75:
        return "สูง"
    if orb <= 1.5:
        return "ปานกลางถึงสูง"
    return "กำลังทำงาน"


def exact_aspect_events(transits, natal, asc_idx, sect):
    rows = []

    for tname in SLOW_PLANETS + ["Mars", "Venus", "Mercury", "Sun"]:
        t = transits[tname]

        for nname, n in natal["planet_map"].items():
            diff = wrapdiff(t["longitude"], n["longitude"])

            for angle, asp, asp_th in ASPECTS:
                orb = abs(diff - angle)
                limit = transit_orb(tname, asp)

                if orb <= limit:
                    house = house_of(n["longitude"], asc_idx)

                    rows.append({
                        "planet": tname,
                        "planet_th": PLANET_TH[tname],
                        "natal_planet": nname,
                        "natal_planet_th": PLANET_TH[nname],
                        "aspect": asp,
                        "aspect_th": asp_th,
                        "orb": round(orb, 3),
                        "house": house,
                        "intensity": event_intensity(orb, tname, asp),
                        "story": event_story(
                            tname, nname, asp, house, orb, "Applying", sect
                        )
                    })

    rows.sort(
        key=lambda x: (
            x["orb"],
            SLOW_PLANETS.index(x["planet"])
            if x["planet"] in SLOW_PLANETS else 9
        )
    )

    return rows


def daily_planet(jd, planet):
    xx, _ = swe.calc_ut(jd, PLANET_IDS[planet], FLAGS)
    return xx[0] % 360, xx[3]


def find_ingresses_and_stations(start_date, months, tz):
    start = datetime.fromisoformat(start_date).date()
    end = start + timedelta(days=round(months * 30.436875))
    events = []

    for planet in SLOW_PLANETS + ["Mars", "Venus", "Mercury"]:
        prev_date = start
        prev_jd = jd_for(prev_date.isoformat(), "12:00", tz)
        prev_lon, prev_speed = daily_planet(prev_jd, planet)
        prev_sign = sign_index(prev_lon)
        prev_retro = prev_speed < 0

        d = start + timedelta(days=1)

        while d <= end:
            jd = jd_for(d.isoformat(), "12:00", tz)
            lon, speed = daily_planet(jd, planet)

            si = sign_index(lon)
            retro = speed < 0

            if si != prev_sign:
                lo = jd - 1
                hi = jd

                for _ in range(24):
                    mid = (lo + hi) / 2
                    mlon, _ = daily_planet(mid, planet)

                    if prev_speed >= 0:
                        boundary = (prev_sign + 1) * 30
                        unwrapped = mlon

                        while unwrapped < prev_lon - 180:
                            unwrapped += 360

                        if unwrapped < boundary:
                            lo = mid
                        else:
                            hi = mid
                    else:
                        boundary = prev_sign * 30
                        unwrapped = mlon

                        while unwrapped > prev_lon + 180:
                            unwrapped -= 360

                        if unwrapped > boundary:
                            lo = mid
                        else:
                            hi = mid

                moment = (lo + hi) / 2
                y, m, day, hour = swe.revjul(moment, swe.GREG_CAL)
                utc = datetime(y, m, day) + timedelta(hours=hour)
                local = utc + timedelta(hours=tz)

                events.append({
                    "date": local.strftime("%Y-%m-%d"),
                    "date_label": fmt_date(local),
                    "planet": planet,
                    "planet_th": PLANET_TH[planet],
                    "type": "ingress",
                    "title": f"{PLANET_TH[planet]} ย้ายเข้าราศี{SIGN_TH[si]}",
                    "from_sign": SIGN_TH[prev_sign],
                    "to_sign": SIGN_TH[si],
                    "description": (
                        f"ดาว{PLANET_TH[planet]}ย้ายจากราศี"
                        f"{SIGN_TH[prev_sign]} เข้าราศี{SIGN_TH[si]} "
                        "พลังของดาวจึงเปลี่ยนโทน และย้ายไปเน้นเรื่องเรือนใหม่ตามลัคนาของคุณ"
                    )
                })

            if retro != prev_retro:
                lo = jd - 1
                hi = jd

                for _ in range(24):
                    mid = (lo + hi) / 2
                    _, ms = daily_planet(mid, planet)

                    if (ms < 0) == prev_retro:
                        lo = mid
                    else:
                        hi = mid

                moment = (lo + hi) / 2
                y, m, day, hour = swe.revjul(moment, swe.GREG_CAL)
                local = datetime(y, m, day) + timedelta(hours=hour)
                local += timedelta(hours=tz)

                typ = "retrograde" if retro else "direct"

                events.append({
                    "date": local.strftime("%Y-%m-%d"),
                    "date_label": fmt_date(local),
                    "planet": planet,
                    "planet_th": PLANET_TH[planet],
                    "type": typ,
                    "title": (
                        f"{PLANET_TH[planet]} เริ่มถอยหลัง"
                        if retro else f"{PLANET_TH[planet]} กลับมาเดินหน้า"
                    ),
                    "description": (
                        f"ดาว{PLANET_TH[planet]} เปลี่ยนทิศทางการเคลื่อนที่ "
                        "ช่วงนี้เหมาะกับการทบทวนหรือเดินหน้าเรื่องที่เกี่ยวข้องอย่างมีสติ "
                        "ไม่ได้แปลว่าทุกเรื่องจะหยุดหรือเกิดปัญหาแน่นอน"
                    )
                })

            prev_date = d
            prev_jd = jd
            prev_lon = lon
            prev_speed = speed
            prev_sign = si
            prev_retro = retro

            d += timedelta(days=1)

    events.sort(key=lambda x: x["date"])
    return events


def transit_house_stories(transits, asc_idx):
    rows = []

    for p in SLOW_PLANETS:
        x = transits[p]
        h = house_of(x["longitude"], asc_idx)

        rows.append({
            "planet": p,
            "planet_th": PLANET_TH[p],
            "sign": x["sign"],
            "sign_th": x["sign_th"],
            "degree": x["degree"],
            "house": h,
            "retrograde": x["retrograde"],
            "topic": HOUSE_TOPICS[h],
            "meaning": PLANET_MEANING[p],
            "story": (
                f"ดาว{PLANET_TH[p]}อยู่เรือน {h} ({HOUSE_TH[h-1]}) "
                f"ซึ่งเป็นเรื่อง{HOUSE_TOPICS[h]} "
                f"เมื่อรวมกับความหมายของดาวที่เกี่ยวกับ{PLANET_MEANING[p]} "
                "จึงเป็นธีมระยะยาวที่ควรสังเกต ไม่ใช่เหตุการณ์เฉพาะวัน"
            )
        })

    return rows


def natal_event_links(n, transit_aspects):
    asc_idx = n["angles"]["asc_sign_index"]
    out = []

    for a in transit_aspects:
        natal_p = n["planet_map"][a["natal"]]
        natal_house = natal_p["house"]

        ruled = []

        for i, r in enumerate(TRAD_RULER):
            if r == a["natal"]:
                ruled.append(i + 1)

        out.append({
            **a,
            "planet": a["transit"],
            "planet_th": a["transit_th"],
            "natal_planet": a["natal"],
            "natal_planet_house": natal_house,
            "natal_planet_house_topic": HOUSE_TOPICS[natal_house],
            "ruled_houses": ruled,
            "linked_topics": [HOUSE_TOPICS[h] for h in ruled]
        })

    return out


@app.get("/")
def index():
    return HTMLResponse((ROOT / "index.html").read_text(encoding="utf-8"))


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "engine": "Swiss Ephemeris via Moshier",
        "version": swe.version,
        "rota_version": "3.0.0"
    }


@app.post("/api/natal")
def natal(b: Birth):
    try:
        n = get_natal(b)
        s = natal_summary(n)

        return {
            "birth": b.model_dump(),
            "chart": n,
            "interpretation": s,
            "engine_note": (
                "Swiss Ephemeris / Moshier; Tropical Zodiac; "
                "Whole Sign Houses; traditional rulers."
            )
        }

    except Exception as e:
        raise HTTPException(400, f"คำนวณดวงไม่สำเร็จ: {e}")


@app.post("/api/annual")
def annual(req: AnnualRequest):
    try:
        n = get_natal(req)
        age = req.annual_year - int(req.date[:4])

        if age < 0:
            raise ValueError("ปีที่เลือกอยู่ก่อนปีเกิด")

        house_num = (age % 12) + 1
        asc_idx = n["angles"]["asc_sign_index"]
        sign_idx = (asc_idx + house_num - 1) % 12

        ruler = TRAD_RULER[sign_idx]
        rd = n["planet_map"][ruler]
        sect = sect_data(n)

        dign, dignote = dignity_of(ruler, rd["sign"])
        ruler_house = rd["house"]
        ruler_house_topic = HOUSE_TOPICS[ruler_house]
        sign_th = SIGN_TH[sign_idx]
        house_topic = HOUSE_TOPICS[house_num]

        natal_aspects = []

        for p in n["planet_map"].values():
            if p["name"] == ruler:
                continue

            diff = wrapdiff(rd["longitude"], p["longitude"])

            for angle, asp, asp_th in ASPECTS:
                orb = abs(diff - angle)

                if orb <= 6:
                    natal_aspects.append({
                        "planet": p["name"],
                        "planet_th": p["thai"],
                        "aspect": asp,
                        "aspect_th": asp_th,
                        "orb": round(orb, 2)
                    })

        natal_aspects.sort(key=lambda x: x["orb"])

        overview = (
            f"ปีอายุ {age} เป็นปีเรือน {house_num} ({HOUSE_TH[house_num-1]}) "
            f"ราศี{sign_th} ธีมตั้งต้นจึงอยู่ที่{house_topic}. "
            f"ดาวเจ้าเรือนปีคือ{PLANET_TH[ruler]} ไปอยู่เรือนกำเนิด "
            f"{ruler_house} ({HOUSE_TH[ruler_house-1]}) "
            f"ซึ่งเกี่ยวกับ{ruler_house_topic}. "
            f"แปลเป็นภาษาชีวิตคือ เรื่องของเรือน {house_num} "
            f"มีแนวโน้มเดินเรื่องผ่านเรื่องของเรือน {ruler_house}. "
            "ต้องอ่านมุมสัมพันธ์และดาวเจ้าเรือนอื่นประกอบก่อนสรุปเหตุการณ์เฉพาะ"
        )

        sections = [
            {
                "title": "ภาพรวมและธีมหลักของปี",
                "text": (
                    overview +
                    f" โทนของราศี{sign_th}คือ{SIGN_STYLE[SIGNS[sign_idx]]}. "
                    f"รอบปีนี้นับจากวันเกิด {req.annual_year}-{req.date[5:]} "
                    "ถึงวันเกิดปีถัดไป ไม่ใช่ปีปฏิทินเต็มปี."
                )
            },
            {
                "title": "Lord of the Year — ดาวที่พาเรื่องของปีไปสู่ชีวิตจริง",
                "text": (
                    f"{PLANET_TH[ruler]} อยู่ราศี{rd['sign_th']} "
                    f"{rd['degree']:.2f}° เรือน {ruler_house} และ"
                    f"{'กำลังถอยหลัง' if rd['retrograde'] else 'เดินหน้า'}. "
                    f"คุณภาพดาว: {dign}. {dignote}. "
                    f"ดาวนี้แทนเรื่อง{PLANET_MEANING[ruler]}. "
                    f"เมื่อเอามารวมกับเรือน {ruler_house} จะเห็นว่าธีมปี "
                    f"ต้องผ่านเรื่อง{ruler_house_topic}. "
                    f"ราศี{rd['sign_th']}ทำให้วิธีรับมือมีโทนว่า"
                    f"{SIGN_STYLE[rd['sign']]}."
                )
            },
            {
                "title": "การงานและทิศทางอาชีพ",
                "text": (
                    f"เวลาอ่านงาน ต้องดูเรือน 10 ร่วมกับเรือนปี {house_num} "
                    f"และดาวเจ้าเรือนปี {ruler}. "
                    f"ถ้าเรื่องงานปีนี้พัวพันกับ{ruler_house_topic} "
                    "ตัวอย่างเช่น งานที่ต้องทำสัญญา ประสานเงิน "
                    "หรือรับผิดชอบเรื่องของคนอื่น ก็อาจกลายเป็นจุดที่ต้องตัดสินใจ. "
                    "ให้ดูดาวเจ้าเรือน 10 และมุมที่ทำกับดาวเจ้าเรือนปีเพิ่ม "
                    "ก่อนสรุปว่าจะเป็นการเลื่อนตำแหน่ง เปลี่ยนงาน หรือเพิ่มภาระ."
                )
            },
            {
                "title": "การเงินและทรัพยากรร่วม",
                "text": (
                    f"แยกเงินตัวเองในเรือน 2 ออกจากเงินร่วม หนี้ ภาษี "
                    f"และภาระของอีกฝ่ายในเรือน 8. "
                    f"จุดเชื่อมของปีคือ {PLANET_TH[ruler]} เจ้าเรือนปี "
                    f"ไปอยู่เรือน {ruler_house} ({HOUSE_TH[ruler_house-1]}). "
                    "เรื่องที่เห็นเป็นรูปธรรมอาจเป็นการจัดงบ แบ่งค่าใช้จ่าย "
                    "ปรับหนี้ ตรวจสัญญา หรือคุยเรื่องทรัพย์สินร่วม "
                    "ไม่ควรตีความว่าได้เงินก้อนหรือเสียเงินก้อนโดยไม่มีสัญญาณยืนยัน."
                )
            },
            {
                "title": "ความรัก คู่ครอง และหุ้นส่วน",
                "text": (
                    f"เรือน 7 คือคู่ครอง หุ้นส่วน ลูกค้า และข้อตกลง "
                    f"ส่วนเรือน 5 คือความรักแบบโรแมนติก. "
                    f"อ่านสองเรือนนี้ร่วมกับเรือนปี {house_num} "
                    f"และตำแหน่ง {PLANET_TH[ruler]} ในเรือน {ruler_house}. "
                    "ถ้าความสัมพันธ์จริงจังขึ้น ภาพที่จับต้องได้อาจเป็นการคุยเรื่องเงิน "
                    "เวลา หน้าที่ หรืออนาคตที่ต้องรับผิดชอบร่วมกัน. "
                    "ถ้ายังโสด ให้มองเป็นช่วงที่รูปแบบการเลือกคนและขอบเขตความสัมพันธ์ถูกทบทวน "
                    "ไม่ใช่รับประกันว่าจะมีคู่."
                )
            },
            {
                "title": "บ้าน ครอบครัว และชีวิตส่วนตัว",
                "text": (
                    "เรือน 4 หมายถึงบ้าน ครอบครัว และฐานชีวิต. "
                    f"ถ้าเจ้าเรือน 4 เชื่อมกับ Lord of the Year หรือเรือน {ruler_house} "
                    "เรื่องบ้านอาจเข้ามาเป็นส่วนหนึ่งของการตัดสินใจปีนี้ "
                    "เช่น วางแผนย้ายบ้าน ซ่อมแซม จัดการทรัพย์สิน "
                    "หรือแบ่งหน้าที่ดูแลคนในครอบครัว."
                )
            },
            {
                "title": "สุขภาพ กิจวัตร และพลังงาน",
                "text": (
                    "เรือน 6 ใช้อ่านงานประจำ ภาระ และกิจวัตร "
                    "ส่วนเรือน 1 ใช้อ่านร่างกายและพลังชีวิต. "
                    "ถ้าเรือนเหล่านี้เชื่อมกับดาวเจ้าเรือนปี "
                    "อาจสะท้อนว่าภาระในปีนี้กระทบตารางพักผ่อน "
                    "หรือการจัดชีวิตประจำวันอย่างไร. "
                    "นี่เป็นการอ่านเชิงสัญลักษณ์ ไม่ใช่การวินิจฉัยโรค "
                    "และไม่ใช้แทนคำแนะนำแพทย์."
                )
            },
            {
                "title": "มุมสัมพันธ์ของ Lord of the Year",
                "text": (
                    "มุมที่พบ: " +
                    "; ".join(
                        f"{x['planet_th']} {x['aspect_th']} orb {x['orb']}°"
                        for x in natal_aspects
                    )
                    if natal_aspects else
                    "ไม่พบมุมหลักภายใน orb 6° ระหว่าง Lord of the Year กับดาวกำเนิดดวงอื่น จึงไม่ควรแต่งมุมสัมพันธ์เพิ่ม."
                )
            },
            {
                "title": "วิธีใช้ปีนี้ให้คุ้ม",
                "text": (
                    f"ให้เริ่มจากจัดการเรื่อง{house_topic} "
                    f"แล้วดูว่ามันพาไปแตะเรื่อง{ruler_house_topic}ตรงไหน. "
                    "ก่อนตกลงเรื่องสำคัญ ให้คุยหน้าที่ เงิน เวลา "
                    "และเงื่อนไขให้ชัด เก็บหลักฐาน และเผื่อเวลาสำหรับสิ่งที่ต้องค่อย ๆ สร้าง. "
                    f"จุดแข็งของราศี{rd['sign_th']}คือ{SIGN_STYLE[rd['sign']]}."
                )
            }
        ]

        return {
            "year": req.annual_year,
            "age": age,
            "profection_house": house_num,
            "house_th": HOUSE_TH[house_num - 1],
            "sign": SIGNS[sign_idx],
            "sign_th": sign_th,
            "sign_glyph": SIGN_GLYPH[sign_idx],
            "lord_of_year": ruler,
            "lord_position": rd,
            "ascendant": n["angles"],
            "natal_planets": n["planets"],
            "annual_period": {
                "start": f"{req.annual_year}-{req.date[5:]}",
                "end": f"{req.annual_year+1}-{req.date[5:]}"
            },
            "reading": {
                "sect": sect["name"],
                "benefic_of_sect": sect["benefic"],
                "malefic_of_sect": sect["malefic"],
                "dignity": dign,
                "dignity_note": dignote,
                "aspects": natal_aspects,
                "sections": sections
            }
        }

    except Exception as e:
        raise HTTPException(400, f"คำนวณ Annual Profection ไม่สำเร็จ: {e}")


@app.post("/api/transit")
def transit(req: TransitRequest):
    try:
        n = get_natal(req)
        jd = jd_for(req.transit_date, "12:00", req.tz)
        trans = planet_positions(jd)

        asc_idx = n["angles"]["asc_sign_index"]
        sect = sect_data(n)

        for p in trans.values():
            p["house"] = house_of(p["longitude"], asc_idx)
            p["house_th"] = HOUSE_TH[p["house"] - 1]

        raw = aspect_list(trans, n["planet_map"], 5)
        tomorrow = planet_positions(jd + 1)

        for a in raw:
            t = a["transit"]
            nname = a["natal"]

            d1 = wrapdiff(
                tomorrow[t]["longitude"],
                n["planet_map"][nname]["longitude"]
            )

            orb1 = abs(d1 - a["angle"])

            a["motion"] = (
                "Applying" if orb1 < a["orb"]
                else "Separating" if orb1 > a["orb"]
                else "Near exact"
            )

            a["motion_th"] = {
                "Applying": "กำลังเข้าใกล้มุมสนิท",
                "Separating": "กำลังแยกออกจากมุมสนิท",
                "Near exact": "อยู่ใกล้มุมสนิท"
            }[a["motion"]]

            a["house"] = house_of(
                n["planet_map"][nname]["longitude"], asc_idx
            )

            a["intensity"] = event_intensity(
                a["orb"], t, a["aspect"]
            )

            a["story"] = event_story(
                t, nname, a["aspect"], a["house"],
                a["orb"], a["motion"], sect
            )

        linked = natal_event_links(n, raw)

        major = [
            x for x in linked
            if x["planet"] in SLOW_PLANETS
        ]

        major.sort(
            key=lambda x: (
                x["orb"],
                SLOW_PLANETS.index(x["planet"])
            )
        )

        ingress = find_ingresses_and_stations(
            req.transit_date, req.months, req.tz
        )

        long_stories = transit_house_stories(
            trans, asc_idx
        )

        top = major[:5]

        if top:
            overview = (
                "ภาพใหญ่ช่วงนี้มีดาวใหญ่เข้ามากระตุ้นพื้นดวงหลายจุด: " +
                " ".join(
                    f"{x['planet_th']} {x['aspect_th']} "
                    f"{x['natal_th']} (orb {x['orb']}°) "
                    f"ไปแตะเรื่องเรือน {x['natal_planet_house']} "
                    "และเรื่องที่ดาวดวงนั้นเป็นเจ้าเรือน"
                    for x in top
                ) +
                ". อ่านเป็นธีมที่กำลังทำงานร่วมกัน ไม่ใช่เหตุการณ์แยกขาดจากกัน."
            )
        else:
            overview = (
                "ในวันที่เลือก ยังไม่พบมุมสนิทจากดาวใหญ่ต่อดาวกำเนิด "
                "ภายใน orb ที่กำหนด จึงให้น้ำหนักกับธีมเรือนที่ดาวใหญ่กำลังเดินผ่าน "
                "และเหตุการณ์ย้ายราศีในช่วงถัดไป แทนการสร้างคำทำนายเฉพาะเหตุการณ์ขึ้นมาเอง."
            )

        return {
            "date": req.transit_date,
            "transits": list(trans.values()),
            "aspects": raw[:80],
            "events": linked[:40],
            "major_events": major[:20],
            "overview": overview,
            "long_term_themes": long_stories,
            "timeline": ingress,
            "natal_angles": n["angles"],
            "natal_planets": n["planet_map"],
            "sect": sect,
            "months_scanned": req.months,
            "engine_note": (
                "ตำแหน่งดาวคำนวณเวลา 12:00 ตามเวลาท้องถิ่น; "
                "applying/separating ประเมินจากการเคลื่อนที่วันถัดไป; "
                "วันย้ายราศีและ station ค้นด้วย Swiss Ephemeris Moshier "
                "โดยสแกนรายวันและหาจุดเปลี่ยนด้วย bisection."
            )
        }

    except Exception as e:
        raise HTTPException(400, f"คำนวณ Transit ไม่สำเร็จ: {e}")


@app.post("/api/ask")
def ask(payload: dict):
    try:
        b = Birth(**payload["birth"])
        question = str(payload.get("question", "")).strip()

        if not question:
            raise ValueError("กรุณาพิมพ์คำถาม")

        n = get_natal(b)
        s = natal_summary(n)
        q = question.lower()

        if any(x in q for x in ["งาน", "อาชีพ", "ธุรกิจ", "career", "work"]):
            houses = [6, 10, 11]
            focus = "การงานและอาชีพ"

        elif any(x in q for x in ["เงิน", "การเงิน", "รายได้", "ทรัพย์", "finance", "money"]):
            houses = [2, 8, 11]
            focus = "การเงินและทรัพยากร"

        elif any(x in q for x in ["รัก", "คู่", "แฟน", "ความสัมพันธ์", "relationship", "love"]):
            houses = [5, 7, 8]
            focus = "ความรักและความสัมพันธ์"

        else:
            houses = list(range(1, 13))
            focus = "ภาพรวมชีวิต"

        relevant = []

        for h in houses:
            si = (n["angles"]["asc_sign_index"] + h - 1) % 12
            ruler = TRAD_RULER[si]
            rp = n["planet_map"][ruler]

            relevant.append(
                f"เรือน {h} ({HOUSE_TH[h-1]}) อยู่ราศี{SIGN_TH[si]} "
                f"มี {PLANET_TH[ruler]} เป็นเจ้าเรือน "
                f"และดาวไปอยู่เรือน {rp['house']} ({HOUSE_TH[rp['house']-1]}). "
                f"จึงต้องอ่านเรื่อง{HOUSE_TOPICS[h]} "
                f"ควบคู่กับเรื่อง{HOUSE_TOPICS[rp['house']]}"
            )

        answer = (
            f"ขอเริ่มจากโครงสร้างดวงก่อนนะ หัวข้อที่ถามคือ{focus}. "
            f"{s['story']}\n\n"
            "จุดที่เกี่ยวข้องในพื้นดวง:\n" +
            "\n".join(relevant) +
            "\n\nนี่คือการเชื่อมโครงสร้างพื้นดวง ยังไม่ใช่การระบุเหตุการณ์ตามวันเวลา "
            "เพราะต้องนำดาวจรของช่วงที่ถามมาซ้อนอีกชั้น "
            "ถ้าระบุช่วงเวลาได้ ระบบ Transit จะใช้หามุมดาวและช่วงเวลาที่เข้มข้นประกอบ."
        )

        return {
            "question": question,
            "answer": answer,
            "facts": {
                "natal": s,
                "relevant_houses": houses
            }
        }

    except Exception as e:
        raise HTTPException(400, f"ประมวลผลคำถามไม่สำเร็จ: {e}")


app.mount(
    "/static",
    StaticFiles(directory=ROOT),
    name="static"
)
