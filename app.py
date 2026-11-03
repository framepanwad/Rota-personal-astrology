from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import swisseph as swe
from pathlib import Path

ROOT = Path(__file__).parent
app = FastAPI(title="ROTA Personal Astrology - Friend Mode", version="3.2.0")

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
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_TH = ["เมษ","พฤษภ","เมถุน","กรกฎ","สิงห์","กันย์","ตุล","พิจิก","ธนู","มังกร","กุมภ์","มีน"]
TRAD_RULER = ["Mars","Venus","Mercury","Moon","Sun","Mercury","Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
HOUSE_TH = ["ตนุ","กดุมภะ","สหัชชะ","พันธุ","ปุตตะ","อริ","ปัตนิ","มรณะ","ศุภะ","กัมมะ","ลาภะ","วินาศ"]

HOUSE_TOPICS = {
  1:"ตัวตน ลุคภายนอก ภาพจำ และพลังงานตัวเอง", 2:"เงินกระเป๋าเรา การหาเงิน ค่านิยม ของเปย์ตัวเอง",
  3:"เพื่อนสนิท คอนเนกชัน คอร์สสั้น การเดินทางใกล้ๆ สื่อสาร", 4:"บ้าน ครอบครัว เซฟโซน ที่อยู่อาศัย",
  5:"ความรักกุ๊กกิ๊ก ความสุข ไฟโปรเจกต์ใหม่ ของเล่น/สัตว์เลี้ยง", 6:"งานประจำ รูทีนชีวิต สุขภาพ ออฟฟิศซินโดรม",
  7:"คู่แท้ หุ้นส่วน แฟน สายเปย์คู่สัญญา", 8:"เงินคนอื่น หนี้สิน สัญญา ทรัพย์สินร่วม การเยียวยาจิตใจ",
  9:"ต่างประเทศ การเรียนต่อ โลกทัศน์ สายมู/ความเชื่อ", 10:"งานใหญ่ อาชีพ ชื่อเสียง ตำแหน่ง และเป้าหมายชีวิต",
  11:"เพื่อนกลุ่มใหญ่ คอนเนกชันปังๆ ความฝัน ลาภลอย", 12:"เรื่องเบื้องหลัง พักชาร์จแบต เซนส์ สิ่งที่มองไม่เห็น"
}

ASPECTS = [(0,"Conjunction","กุม (พลังรวมกันแรงมาก)"),(60,"Sextile","โยค (ส่งพลังสนับสนุนกันดี)"),(90,"Square","ฉาก (ตึงเครียด ต้องแก้ปัญหา)"),(120,"Trine","ตรีโกณ (ไหลลื่น โชคช่วย)"),(180,"Opposition","เล็ง (ดึงกันคนละทาง ต้องจัดสมดุล)")]
FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED
SLOW_PLANETS = ["Jupiter","Saturn","Uranus","Neptune","Pluto"]

# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS & CALCULATIONS
# -----------------------------------------------------------------------------
class Birth(BaseModel):
    name: str = "แก"
    date: str
    time: str
    place: str = "Bangkok, Thailand"
    lat: float = Field(13.7563, ge=-90, le=90)
    lon: float = Field(100.5018, ge=-180, le=180)
    tz: float = Field(7.0, ge=-12, le=14)

class TransitRequest(Birth):
    transit_date: str
    months: int = Field(12, ge=1, le=24)

class AnnualRequest(Birth):
    annual_year: int = Field(..., ge=1900, le=2200)

def jd_for(local_date, local_time="12:00", tz=7.0):
    dt = datetime.fromisoformat(f"{local_date}T{local_time}:00")
    utc = dt - timedelta(hours=tz)
    return swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute/60 + utc.second/3600, swe.GREG_CAL)

def wrapdiff(a,b): return abs((a-b+180)%360-180)
def sign_index(lon): return int((lon%360)//30)
def house_of(lon, asc_sign_idx): return ((sign_index(lon)-asc_sign_idx)%12)+1

def planet_positions(jd):
    out={}
    for en,pid,th,glyph in PLANETS:
        xx,_=swe.calc_ut(jd,pid,FLAGS)
        lon,speed=xx[0],xx[3]
        si=sign_index(lon); deg=lon%30
        out[en]={"name":en,"thai":th,"glyph":glyph,"longitude":round(lon%360,6),"sign":SIGNS[si],"sign_th":SIGN_TH[si],"degree":round(deg,2),"retrograde":speed<0}
    return out

def house_data(jd,lat,lon):
    _,ascmc=swe.houses_ex(jd,lat,lon,b'W')
    asc=ascmc[0]%360; ai=sign_index(asc)
    return {"asc":asc,"asc_sign":SIGNS[ai],"asc_sign_th":SIGN_TH[ai],"asc_sign_index":ai}

def get_natal(b):
    jd=jd_for(b.date,b.time,b.tz)
    planets=planet_positions(jd)
    angles=house_data(jd,b.lat,b.lon)
    ai=angles["asc_sign_index"]
    for p in planets.values():
        p["house"]=house_of(p["longitude"],ai)
        p["house_th"]=HOUSE_TH[p["house"]-1]
    return {"julian_day":jd,"planets":planets,"angles":angles}

# -----------------------------------------------------------------------------
# 3. FRIENDLY NARRATIVE GENERATOR (ภาษาเพื่อน เม้าท์มอย เข้าใจง่าย)
# -----------------------------------------------------------------------------
def get_friendly_name(name):
    name = (name or "").strip()
    return name if name and name != "แก" else "แก"

def build_natal_friendly_reading(n, client_name=""):
    fname = get_friendly_name(client_name)
    pm = n["planets"]
    ai = n["angles"]["asc_sign_index"]
    
    asc_sign = n["angles"]["asc_sign_th"]
    asc_ruler_en = TRAD_RULER[ai]
    asc_ruler = pm[asc_ruler_en]
    
    sun = pm["Sun"]
    moon = pm["Moon"]
    merc = pm["Mercury"]
    ven = pm["Venus"]
    mar = pm["Mars"]
    jup = pm["Jupiter"]
    sat = pm["Saturn"]

    sections = [
        {
            "title": "🧠 1. ตัวตน & Vibe ที่คนอื่นเห็น (Mental & Outer Vibe)",
            "text": f"ลัคนา{asc_sign} ทำให้เวลาคนเห็น {fname} ครั้งแรก จะรู้สึกว่าแกมีออร่าแบบนี้! แต่ตัวจริงข้างในคือนำพาด้วยดาว{asc_ruler['thai']} ที่ไปสถิตอยู่เรือน {asc_ruler['house']} ({asc_ruler['house_th']}). แปลว่าหัวใจหลักของแกในชีวิตนี้จะวนเวียนอยู่กับเรื่อง **{HOUSE_TOPICS[asc_ruler['house']]}** แกไม่ใช่คนตื้นเขิน คิดอะไรซับซ้อนกว่าที่คนอื่นเห็นเสมอ!"
        },
        {
            "title": "💖 2. โลกภายใน อารมณ์ & วิธีฮีลใจเวลาเครียด",
            "text": f"จันทร์สถิตราศี{moon['sign_th']} เรือน {moon['house']}. ข้างใน {fname} เป็นคนที่เรื่องอารมณ์ผูกกับความรู้สึกปลอดภัยในเรื่อง **{HOUSE_TOPICS[moon['house']]}** มากๆ เวลาเหนื่อยหรือนอยด์ แกอย่าฝืนไปสังสรรค์ตามคนอื่น ให้กลับมาชาร์จพลังในพื้นที่ส่วนตัว ดื่มน้ำ ทำจิตใจให้นิ่ง หรือโฟกัสกับสิ่งที่ควบคุมได้ แล้วพลังแกจะกลับมาเร็วมาก"
        },
        {
            "title": "🗣️ 3. สไตล์การคิด การพูด & การตัดสินใจ",
            "text": f"พุธอยู่ราศี{merc['sign_th']} เรือน {merc['house']}. เรื่องสมองไบร์ทและความคิด {fname} จะถนัดมากเป็นพิเศษในประเด็น **{HOUSE_TOPICS[merc['house']]}** เวลาเจรจาหรือติดต่อเรื่องนี้ แกจะมีไหวพริบดี พูดแป๊บเดียวคนก็เคลิ้มตาม แต่ข้อควรระวังคือ เวลาโกรธอย่าเพิ่งพิมพ์หรือพูดทันที ให้ถอยออกมา 5 นาที ไม่งั้นคำพูดแกจะแทงใจคนฟังจุกไปสามวัน!"
        },
        {
            "title": "🥰 4. เวลารักใครเป็นยังไง & สเปกที่แพ้ทาง",
            "text": f"ศุกร์อยู่ราศี{ven['sign_th']} เรือน {ven['house']} และอังคารอยู่เรือน {mar['house']}. เวลารักใคร {fname} จะแสดงออกผ่านเรื่อง **{HOUSE_TOPICS[ven['house']]}** ไม่ใช่แค่พูดหวานๆ แต่ชอบซัพพอร์ตให้เห็นเป็นรูปธรรม! ส่วนสเปกที่เห็นแล้วใจสั่น มักจะเป็นคนที่ดูมีความรับผิดชอบ ชัดเจน และเข้ามาร่วมแชร์เรื่อง **{HOUSE_TOPICS[mar['house']]}** ในชีวิตแกได้"
        },
        {
            "title": "💰 5. พื้นดวงการเงินตลอดชีวิต & จุดเงินรั่ว",
            "text": f"เรื่องเงินของ {fname} วนเวียนกับเรื่อง **{HOUSE_TOPICS[pm[TRAD_RULER[(ai+1)%12]]['house']]}**. แกเป็นพวกหาเงินเก่ง มีช่องทางหาเงินเข้ามาเรื่อยๆ ไม่ขัดสน แต่จุดที่ต้องระวังคือ 'เงินรั่วตามอารมณ์'! เวลาเครียดหรืออยากเปย์รางวัลให้ตัวเอง เงินจะไหลออกไวมาก เทคนิคคือ ได้เงินมาให้แยกบัญชีเก็บทันที อย่าแช่ไว้ในบัญชีพร้อมใช้"
        },
        {
            "title": "💼 6. การงาน อาชีพ & ศัตรูในที่ทำงาน",
            "text": f"ดาวการงานของแกตกเรือน {pm[TRAD_RULER[(ai+9)%12]]['house']}. งานที่ทำแล้วปังต้องเป็นงานที่ได้ใช้ศักยภาพในเรื่อง **{HOUSE_TOPICS[pm[TRAD_RULER[(ai+9)%12]]['house']]}** แกเหมาะกับการทำงานที่มีอิสระระดับนึง ไม่ชอบโดนจู้จี้จุกจิก ส่วนเรื่องศัตรูในที่ทำงาน มักมาในรูปแบบคนอิจฉาเงียบๆ เวลาแกทำผลงานเด่น วิธีรับมือคือ ไม่ต้องไปแลก ทำตัวสวยๆ รวยๆ เดินผ่านพอ!"
        }
    ]
    return sections

# -----------------------------------------------------------------------------
# 4. API ENDPOINTS
# -----------------------------------------------------------------------------
@app.get("/")
def index(): 
    if (ROOT/"index.html").exists():
        return HTMLResponse((ROOT/"index.html").read_text(encoding="utf-8"))
    return {"message": "ROTA Astrology API Ready!"}

@app.get("/api/health")
def health(): 
    return {"ok": True, "engine": "Swiss Ephemeris", "mode": "Friend Conversational"}

@app.post("/api/natal")
def natal(b: Birth):
    try:
        n = get_natal(b)
        sections = build_natal_friendly_reading(n, b.name)
        return {
            "client_name": b.name,
            "chart_info": {
                "asc_sign": n["angles"]["asc_sign_th"],
                "sun_sign": n["planets"]["Sun"]["sign_th"],
                "moon_sign": n["planets"]["Moon"]["sign_th"]
            },
            "sections": sections
        }
    except Exception as e: 
        raise HTTPException(400, f"คำนวณดวงไม่สำเร็จ: {e}")

@app.post("/api/annual")
def annual(req: AnnualRequest):
    try:
        n = get_natal(req)
        fname = get_friendly_name(req.name)
        birth_year = int(req.date[:4])
        age = req.annual_year - birth_year
        if age < 0: raise ValueError("ปีที่เลือกอยู่ก่อนปีเกิดนะแก")
        
        house_num = (age % 12) + 1
        asc_idx = n["angles"]["asc_sign_index"]
        sign_idx = (asc_idx + house_num - 1) % 12
        ruler = TRAD_RULER[sign_idx]
        rd = n["planets"][ruler]
        
        overview = (
            f"ปีนี้ {fname} อายุ {age} ปี! เรือนที่เปิดสวิตช์ทำงานหลักคือ **เรือนที่ {house_num} ({HOUSE_TH[house_num-1]}) ราศี{SIGN_TH[sign_idx]}**\n"
            f"🎯 **ธีมใหญ่ของปีนี้:** พลังงานชีวิตแกจะไปกระจุกอยู่ที่เรื่อง **'{HOUSE_TOPICS[house_num]}'** เป็นหลักเลย!\n"
            f"🪐 **ดาวผู้กุมแส้ปีนี้ (Lord of the Year):** คือดาว **{PLANET_TH[ruler]}** ซึ่งไปสถิตอยู่ในเรือนกำเนิดที่ {rd['house']} ({HOUSE_TH[rd['house']-1]})\n"
            f"💡 **สแนปชอตชีวิต:** เรื่อง **{HOUSE_TOPICS[house_num]}** จะพาแกไปเกี่ยวพันกับเรื่อง **{HOUSE_TOPICS[rd['house']]}** อย่างหลีกเลี่ยงไม่ได้! เช่น ถ้าปีนี้เน้นเรื่องงาน ก็จะมีเรื่องเงินร่วม/ข้อตกลงเข้ามาให้ตัดสินใจเพิ่มขึ้น เป็นปีที่ต้องลุยแบบมีสติแล้วจะปังมาก!"
        )
        
        sections = [
            {"title": "✨ ภาพรวม & Focus หลักของปีนี้", "text": overview},
            {"title": "💼 การงาน & การเรียนปีนี้", "text": f"โฟกัสเรื่องงานจะผูกกับ **{HOUSE_TOPICS[rd['house']]}** ถ้าคิดจะเปลี่ยนงาน ย้ายแผนก หรือเริ่มโปรเจกต์ใหม่ ช่วงปีอายุนี้นับเป็นจังหวะดีที่จะได้ลองอะไรใหม่ๆ แต่ต้องตรวจรายละเอียดสัญญาให้รอบคอบก่อนเซ็นนะ"},
            {"title": "💰 การเงิน & โชคลาภปีนี้", "text": f"การเงินจะขยับตามแอ็กชันของแกในเรื่อง **{HOUSE_TOPICS[house_num]}** ยิ่งแกทุ่มเทเรื่องนี้ เงินก็ยิ่งไหลเข้า แต่ระวังรายจ่ายแทรกซ้อนจากการเกรงใจคนอื่นด้วย"},
            {"title": "❤️ ความรัก & ความสัมพันธ์ปีนี้", "text": f"คนมีคู่ จะเป็นปีที่ได้เคลียร์ความเข้าใจและวางแผนอนาคตเรื่อง **{HOUSE_TOPICS[rd['house']]}** ร่วมกัน ส่วนคนโสด มีเกณฑ์เจอคนเข้ามาผูกพันผ่านวงสังคมหรือการทำงานช่วงนี้!"}
        ]
        
        return {
            "client_name": req.name,
            "annual_year": req.annual_year,
            "age": age,
            "profection_house": house_num,
            "house_th": HOUSE_TH[house_num-1],
            "sign_th": SIGN_TH[sign_idx],
            "lord_of_year": PLANET_TH[ruler],
            "sections": sections
        }
    except Exception as e:
        raise HTTPException(400, f"คำนวณ Annual Profection ไม่สำเร็จ: {e}")

@app.post("/api/transit")
def transit(req: TransitRequest):
    try:
        n = get_natal(req)
        fname = get_friendly_name(req.name)
        jd = jd_for(req.transit_date, "12:00", req.tz)
        trans = planet_positions(jd)
        asc_idx = n["angles"]["asc_sign_index"]
        
        highlights = []
        for p in SLOW_PLANETS:
            t_data = trans[p]
            h = house_of(t_data["longitude"], asc_idx)
            highlights.append({
                "planet": PLANET_TH[p],
                "house": h,
                "house_th": HOUSE_TH[h-1],
                "topic": HOUSE_TOPICS[h],
                "story": f"ดาว{PLANET_TH[p]} กำลังเดินผ่านเรือน {h} ({HOUSE_TH[h-1]}) ของ {fname} -> ช่วงนี้เรื่อง **'{HOUSE_TOPICS[h]}'** จะมีบททดสอบหรือโอกาสใหม่ๆ เข้ามาให้แกจัดการเป็นพิเศษ!"
            })
            
        return {
            "client_name": req.name,
            "transit_date": req.transit_date,
            "overview": f"เช็กดวงดาวจร ณ วันที่ {req.transit_date} สำหรับ {fname}! ช่วงนี้ดาวใหญ่กำลังย้ายตำแหน่งและส่งแรงกระแทกถึงเรื่องต่างๆ ในชีวิตแก ดังนี้:",
            "highlights": highlights
        }
    except Exception as e:
        raise HTTPException(400, f"คำนวณ Transit ไม่สำเร็จ: {e}")

if (ROOT/"static").exists():
    app.mount("/static", StaticFiles(directory=ROOT/"static"), name="static")
