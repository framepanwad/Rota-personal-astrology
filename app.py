from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import swisseph as swe
from pathlib import Path

ROOT = Path(__file__).parent
app = FastAPI(title="ROTA Personal Astrology - Friend Mode", version="3.3.0")

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
  1:"ตัวตน ลุคภายนอก ภาพจำ และพลังงานส่วนตัว", 2:"เงินในกระเป๋า ช่องทางหาเงิน ค่านิยม และของเปย์ตัวเอง",
  3:"เพื่อนสนิท คอนเนกชัน คอร์สสั้น การเดินทางใกล้ๆ และการสื่อสาร", 4:"บ้าน ครอบครัว เซฟโซน และที่อยู่อาศัย",
  5:"ความรักกุ๊กกิ๊ก ความสุข ไฟแพชชันโปรเจกต์ใหม่ ของเล่น/สัตว์เลี้ยง", 6:"งานประจำ รูทีนชีวิต สุขภาพ และออฟฟิศซินโดรม",
  7:"คู่แท้ หุ้นส่วน แฟน และคู่สัญญา", 8:"เงินคนอื่น หนี้สิน สัญญา ทรัพย์สินร่วม และการเยียวยาจิตใจ",
  9:"ต่างประเทศ การเรียนต่อ โลกทัศน์ และสายมู/ความเชื่อ", 10:"งานใหญ่ อาชีพ ชื่อเสียง ตำแหน่ง และเป้าหมายชีวิต",
  11:"เพื่อนกลุ่มใหญ่ คอนเนกชันปังๆ ความฝัน และลาภลอย", 12:"เรื่องเบื้องหลัง การพักชาร์จแบต เซนส์ และสิ่งที่มองไม่เห็น"
}

FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED
SLOW_PLANETS = ["Jupiter","Saturn","Uranus","Neptune","Pluto"]

# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS & CALCULATIONS (รองรับแปลง พ.ศ. อัตโนมัติ)
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

def parse_flexible_date(date_str: str) -> str:
    """แปลงวันที่รองรับทั้ง ค.ศ. (YYYY-MM-DD) และ พ.ศ. (เช่น 29 Jan BE 2539 หรือ 2539-01-29) เพื่อไม่ให้ระบบพัง"""
    date_str = date_str.strip()
    # ถ้ามีคำว่า BE หรือปีมากกว่า 2400 ให้แปลงเป็น ค.ศ.
    if "BE" in date_str:
        parts = date_str.replace("BE", "").strip().split()
        if len(parts) >= 3:
            day, month_str, year_be = parts[0], parts[1], int(parts[2])
            year_ce = year_be - 543
            months_map = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}
            month = months_map.get(month_str[:3], 1)
            return f"{year_ce}-{month:02d}-{int(day):02d}"
    
    # ถ้าขึ้นต้นด้วยปี พ.ศ. (เช่น 2539-01-29)
    try:
        parts = date_str.split("-")
        if len(parts) == 3 and int(parts[0]) > 2400:
            year_ce = int(parts[0]) - 543
            return f"{year_ce}-{parts[1]}-{parts[2]}"
    except:
        pass
        
    return date_str.split("T")[0] # คืนค่าเดิมถ้าเป็นมาตรฐานอยู่แล้ว

def jd_for(local_date, local_time="12:00", tz=7.0):
    clean_date = parse_flexible_date(local_date)
    dt = datetime.fromisoformat(f"{clean_date}T{local_time}:00")
    utc = dt - timedelta(hours=tz)
    return swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute/60 + utc.second/3600, swe.GREG_CAL)

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
    asc_ruler_
