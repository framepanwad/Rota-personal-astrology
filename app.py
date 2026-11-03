
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import swisseph as swe
import math
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
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_TH = ["เมษ","พฤษภ","เมถุน","กรกฎ","สิงห์","กันย์","ตุล","พิจิก","ธนู","มังกร","กุมภ์","มีน"]
SIGN_GLYPH = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
TRAD_RULER = ["Mars","Venus","Mercury","Moon","Sun","Mercury","Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
HOUSE_TH = ["ตนุ","กดุมภะ","สหัชชะ","พันธุ","ปุตตะ","อริ","ปัตนิ","มรณะ","ศุภะ","กัมมะ","ลาภะ","วินาศ"]
ASPECTS = [(0,"Conjunction","กุม"),(60,"Sextile","โยค 60°"),(90,"Square","ฉาก"),(120,"Trine","ตรีโกณ"),(180,"Opposition","เล็ง")]
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
    hour = utc.hour + utc.minute/60 + utc.second/3600
    return swe.julday(utc.year, utc.month, utc.day, hour, swe.GREG_CAL)

def planet_positions(jd):
    result = {}
    for en, pid, th, glyph in PLANETS:
        xx, ret = swe.calc_ut(jd, pid, FLAGS)
        lon, lat, dist, speed_lon = xx[:4]
        idx = int(lon // 30) % 12
        deg = lon % 30
        result[en] = {
            "name": en, "thai": th, "glyph": glyph, "longitude": round(lon, 6),
            "sign": SIGNS[idx], "sign_th": SIGN_TH[idx], "glyph_sign": SIGN_GLYPH[idx],
            "degree": round(deg, 2), "minute": int((deg % 1)*60),
            "retrograde": speed_lon < 0, "speed": round(speed_lon, 5)
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
        houses.append({"house":i+1,"sign":SIGNS[sign_idx],"sign_th":SIGN_TH[sign_idx],
                       "glyph":SIGN_GLYPH[sign_idx],"ruler":TRAD_RULER[sign_idx],
                       "meaning":HOUSE_TH[i]})
    return {"asc":asc,"asc_sign":SIGNS[asc_sign],"asc_sign_th":SIGN_TH[asc_sign],
            "asc_glyph":SIGN_GLYPH[asc_sign],"asc_degree":round(asc%30,2),
            "mc":mc,"houses":houses}

def aspect_list(transits, natal, max_orb=5):
    found=[]
    for tname,t in transits.items():
        for nname,n in natal.items():
            if tname == nname: # same planet conjunctions are still meaningful; retain
                pass
            diff=abs((t["longitude"]-n["longitude"]+180)%360-180)
            for angle, en, th in ASPECTS:
                orb=abs(diff-angle)
                if orb <= max_orb:
                    found.append({"transit":tname,"transit_th":t["thai"],"natal":nname,
                                  "natal_th":n["thai"],"aspect":en,"aspect_th":th,
                                  "orb":round(orb,2),"separation":round(diff,2)})
    found.sort(key=lambda x:x["orb"])
    return found

def get_natal(b: Birth):
    jd=jd_for(b.date,b.time,b.tz)
    planets=planet_positions(jd)
    houses=house_data(jd,b.lat,b.lon)
    for p in planets.values():
        p["house"]=(int((p["longitude"]//30)-int(houses["asc"]//30))%12)+1
        p["house_th"]=HOUSE_TH[p["house"]-1]
    return {"julian_day":jd,"planets":list(planets.values()),"planet_map":planets,"angles":houses,
            "aspects":aspect_list(planets,planets, max_orb=0.15)}

@app.get("/")
def index():
    return HTMLResponse((ROOT/"index.html").read_text(encoding="utf-8"))

@app.get("/api/health")
def health():
    return {"ok":True,"engine":"Swiss Ephemeris via Moshier","version":swe.version}

@app.post("/api/natal")
def natal(b: Birth):
    try:
        n=get_natal(b)
        return {"birth":b.model_dump(),"chart":n,"engine_note":"คำนวณตำแหน่งดาวด้วย Swiss Ephemeris / Moshier; Tropical zodiac; Whole Sign Houses."}
    except Exception as e:
        raise HTTPException(400, f"คำนวณดวงไม่สำเร็จ: {e}")

@app.post("/api/transit")
def transit(req: TransitRequest):
    try:
        n=get_natal(req)
        jd=jd_for(req.transit_date,"12:00",req.tz)
        trans=planet_positions(jd)
        tomorrow=planet_positions(jd+1)
        aspects=aspect_list(trans,n["planet_map"],5)
        for a in aspects:
            t=a["transit"]; natal_name=a["natal"]
            diff0=abs((trans[t]["longitude"]-n["planet_map"][natal_name]["longitude"]+180)%360-180)
            diff1=abs((tomorrow[t]["longitude"]-n["planet_map"][natal_name]["longitude"]+180)%360-180)
            angle=next(x[0] for x in ASPECTS if x[1]==a["aspect"])
            orb1=abs(diff1-angle)
            a["motion"]="Applying" if orb1 < a["orb"] else "Separating" if orb1 > a["orb"] else "Near exact"
            a["motion_th"]={"Applying":"กำลังเข้าใกล้มุมสนิท","Separating":"กำลังแยกออกจากมุมสนิท","Near exact":"ใกล้มุมสนิท"}[a["motion"]]
        return {"date":req.transit_date,"transits":list(trans.values()),"aspects":aspects[:60],
                "natal_angles":n["angles"],"natal_planets":n["planet_map"],
                "engine_note":"Transit positions calculated for 12:00 local time; aspect motion estimated from next-day movement."}
    except Exception as e:
        raise HTTPException(400, f"คำนวณ Transit ไม่สำเร็จ: {e}")

class AnnualRequest(Birth):
    annual_year: int = Field(..., ge=1900, le=2200)


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
        sign_th = SIGN_TH[sign_idx]
        ruler = TRAD_RULER[sign_idx]

        ruler_data = n["planet_map"][ruler]

        return {
            "year": req.annual_year,
            "age": age,
            "profection_house": house_num,
            "house_th": HOUSE_TH[house_num - 1],
            "sign": sign,
            "sign_th": sign_th,
            "sign_glyph": SIGN_GLYPH[sign_idx],
            "lord_of_year": ruler,
            "lord_position": ruler_data,
            "ascendant": n["angles"],
            "natal_planets": n["planets"],
            "annual_period": {
                "start": f"{req.annual_year}-{req.date[5:]}",
                "end": f"{req.annual_year + 1}-{req.date[5:]}"
            }
        }

    except Exception as e:
        raise HTTPException(
            400, f"คำนวณ Annual Profection ไม่สำเร็จ: {e}"
        )

@app.post("/api/ask")
def ask(payload: dict):
    try:
        b=Birth(**payload["birth"])
        question=str(payload.get("question","")).strip()
        if not question: raise ValueError("กรุณาพิมพ์คำถาม")
        n=get_natal(b)
        asc=n["angles"]
        planets=n["planet_map"]
        lord=TRAD_RULER[SIGNS.index(asc["asc_sign"])]
        lord_data=planets[lord]
        focus = "การงาน" if any(x in question for x in ["งาน","อาชีพ","ธุรกิจ","career","work"]) else "การเงิน" if any(x in question for x in ["เงิน","การเงิน","รายได้","ทรัพย์","finance","money"]) else "ความสัมพันธ์" if any(x in question for x in ["รัก","คู่","แฟน","ความสัมพันธ์","relationship","love"]) else "ภาพรวมชีวิต"
        text=(f"ข้อมูลพื้นดวงที่ใช้ประกอบคำถาม: ลัคนา {asc['asc_sign_th']} ({asc['asc_sign']}) "
              f"องศา {asc['asc_degree']}° และดาวเจ้าเรือนลัคนาคือ {lord} อยู่ราศี {lord_data['sign_th']} "
              f"เรือนที่ {lord_data['house']} ({lord_data['house_th']}).\\n\\n"
              f"หัวข้อที่ระบบจัดกลุ่ม: {focus}\\n\\n"
              "นี่เป็นการสรุปข้อเท็จจริงจากตำแหน่งดาวและโครงสร้างเรือนที่คำนวณได้ ยังไม่ใช่คำพยากรณ์จาก AI "
              "ขั้นต่อไปควรเชื่อมโมเดลภาษาเพื่อสังเคราะห์ความหมายตามกฎ Traditional Astrology โดยไม่แต่งตำแหน่งดาวเพิ่ม.")
        return {"question":question,"answer":text,"facts":{"ascendant":asc,"asc_ruler":lord,"ruler_position":lord_data}}
    except Exception as e:
        raise HTTPException(400, f"ประมวลผลคำถามไม่สำเร็จ: {e}")

app.mount("/static", StaticFiles(directory=ROOT), name="static")
