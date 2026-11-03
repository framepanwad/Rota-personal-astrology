from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import swisseph as swe
from pathlib import Path
import math

ROOT = Path(__file__).parent
app = FastAPI(title="ROTA Personal Astrology", version="3.0.0")

# Tropical zodiac, Whole Sign Houses, traditional rulers for houses.
PLANETS = [
    ("Sun", swe.SUN, "อาทิตย์", "☉"), ("Moon", swe.MOON, "จันทร์", "☽"),
    ("Mercury", swe.MERCURY, "พุธ", "☿"), ("Venus", swe.VENUS, "ศุกร์", "♀"),
    ("Mars", swe.MARS, "อังคาร", "♂"), ("Jupiter", swe.JUPITER, "พฤหัสบดี", "♃"),
    ("Saturn", swe.SATURN, "เสาร์", "♄"), ("Uranus", swe.URANUS, "ยูเรนัส", "♅"),
    ("Neptune", swe.NEPTUNE, "เนปจูน", "♆"), ("Pluto", swe.PLUTO, "พลูโต", "♇"),
]
PLANET_IDS = {p[0]: p[1] for p in PLANETS}
PLANET_TH = {p[0]: p[2] for p in PLANETS}
PLANET_GLYPH = {p[0]: p[3] for p in PLANETS}
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_TH = ["เมษ","พฤษภ","เมถุน","กรกฎ","สิงห์","กันย์","ตุล","พิจิก","ธนู","มังกร","กุมภ์","มีน"]
SIGN_GLYPH = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
TRAD_RULER = ["Mars","Venus","Mercury","Moon","Sun","Mercury","Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
HOUSE_TH = ["ตนุ","กดุมภะ","สหัชชะ","พันธุ","ปุตตะ","อริ","ปัตนิ","มรณะ","ศุภะ","กัมมะ","ลาภะ","วินาศ"]
HOUSE_TOPICS = {
  1:"ตัวตน ร่างกาย ภาพลักษณ์ และการเริ่มต้นด้วยตัวเอง", 2:"รายได้ เงินเก็บ ทรัพย์สิน และคุณค่าที่เราสร้าง",
  3:"การสื่อสาร เอกสาร การเรียนระยะสั้น พี่น้อง และการเดินทางใกล้", 4:"บ้าน ครอบครัว ที่อยู่อาศัย และรากฐานชีวิต",
  5:"ความรักแบบโรแมนติก ความสนุก งานสร้างสรรค์ และบุตร", 6:"งานประจำ ภาระ ตารางชีวิต สุขภาพประจำวัน และงานบริการ",
  7:"คู่ครอง หุ้นส่วน ลูกค้า สัญญา และคู่ขัดแย้งที่เปิดเผย", 8:"เงินร่วม หนี้ ภาษี มรดก ภาระของอีกฝ่าย และความไว้วางใจ",
  9:"ต่างประเทศ การเดินทางไกล การศึกษาสูง กฎหมาย และความเชื่อ", 10:"อาชีพ ตำแหน่ง ชื่อเสียง เป้าหมาย และผู้บังคับบัญชา",
  11:"รายได้จากอาชีพ เครือข่าย เพื่อน ผู้สนับสนุน และเป้าหมายระยะยาว", 12:"เรื่องเบื้องหลัง การพักฟื้น ความโดดเดี่ยว ค่าใช้จ่ายแฝง และสิ่งที่ควบคุมยาก"
}
PLANET_MEANING = {
 "Sun":"ตัวตน ความมุ่งหมาย อำนาจ การยอมรับ และผู้มีอำนาจ", "Moon":"ความต้องการ ความมั่นคง บ้าน ครอบครัว และความเปลี่ยนแปลง",
 "Mercury":"การคิด การสื่อสาร การเรียนรู้ เอกสาร และการเจรจา", "Venus":"ความรัก ความสัมพันธ์ ความพึงพอใจ เงินที่ใช้เพื่อความสุข และการประนีประนอม",
 "Mars":"แรงผลักดัน การแข่งขัน ความขัดแย้ง การตัดสินใจ และการลงมือ", "Jupiter":"การเติบโต โอกาส ความรู้ ผู้สนับสนุน และการขยายขอบเขต",
 "Saturn":"ความรับผิดชอบ ข้อจำกัด เวลา โครงสร้าง ภาระ และผลระยะยาว", "Uranus":"การเปลี่ยนแปลงฉับพลัน อิสรภาพ เทคโนโลยี และการหลุดจากรูปแบบเดิม",
 "Neptune":"อุดมคติ จินตนาการ ความคลุมเครือ ความเมตตา และสิ่งที่ยังมองไม่ชัด", "Pluto":"อำนาจ การควบคุม การเปลี่ยนแปลงเชิงลึก และการปิดฉากเพื่อเริ่มใหม่"
}
SIGN_STYLE = {
 "Aries":"ตรงไปตรงมา เร็ว กล้าเริ่ม และต้องระวังความใจร้อน", "Taurus":"ค่อยเป็นค่อยไป เน้นความมั่นคง ทรัพยากร และผลที่จับต้องได้",
 "Gemini":"เน้นข้อมูล การติดต่อ การเรียนรู้ และการมีหลายทางเลือก", "Cancer":"เน้นความปลอดภัย บ้าน ครอบครัว และความผูกพัน",
 "Leo":"เน้นความภาคภูมิใจ การแสดงตัว ความคิดสร้างสรรค์ และการยอมรับ", "Virgo":"เน้นรายละเอียด ระบบ งานบริการ การวิเคราะห์ และการปรับปรุง",
 "Libra":"เน้นความร่วมมือ คู่สัญญา ความยุติธรรม และการประนีประนอม", "Scorpio":"เน้นเรื่องลึกซึ้ง ทรัพยากรร่วม ความไว้ใจ และการเปลี่ยนผ่าน",
 "Sagittarius":"เน้นการขยายขอบเขต การศึกษา ต่างประเทศ และความเชื่อ", "Capricorn":"เน้นเป้าหมายระยะยาว วินัย หน้าที่ และความเป็นมืออาชีพ",
 "Aquarius":"เน้นเครือข่าย กลุ่มคน ระบบ ความคิดอิสระ และการเปลี่ยนแปลง", "Pisces":"เน้นจินตนาการ ความเมตตา การปล่อยวาง และขอบเขตที่ต้องชัดเจน"
}
ASPECTS = [(0,"Conjunction","กุม"),(60,"Sextile","โยค 60°"),(90,"Square","ฉาก"),(120,"Trine","ตรีโกณ"),(180,"Opposition","เล็ง")]
FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED
SLOW_PLANETS = ["Jupiter","Saturn","Uranus","Neptune","Pluto"]

class Birth(BaseModel):
    name: str = ""
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
    return swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute/60 + utc.second/3600, swe.GREG_CAL)

def wrapdiff(a,b): return abs((a-b+180)%360-180)
def sign_index(lon): return int((lon%360)//30)
def house_of(lon, asc_sign_idx): return ((sign_index(lon)-asc_sign_idx)%12)+1
def fmt_date(d): return d.strftime("%d %b %Y")

def planet_positions(jd):
    out={}
    for en,pid,th,glyph in PLANETS:
        xx,_=swe.calc_ut(jd,pid,FLAGS)
        lon,lat,dist,speed=xx[:4]
        si=sign_index(lon); deg=lon%30
        out[en]={"name":en,"thai":th,"glyph":glyph,"longitude":round(lon%360,6),"sign":SIGNS[si],"sign_th":SIGN_TH[si],"glyph_sign":SIGN_GLYPH[si],"degree":round(deg,2),"minute":int((deg%1)*60),"retrograde":speed<0,"speed":round(speed,6)}
    return out

def house_data(jd,lat,lon):
    _,ascmc=swe.houses_ex(jd,lat,lon,b'W')
    asc=ascmc[0]%360; mc=ascmc[1]%360; ai=sign_index(asc)
    houses=[]
    for i in range(12):
        si=(ai+i)%12
        houses.append({"house":i+1,"sign":SIGNS[si],"sign_th":SIGN_TH[si],"glyph":SIGN_GLYPH[si],"ruler":TRAD_RULER[si],"meaning":HOUSE_TH[i],"topic":HOUSE_TOPICS[i+1]})
    return {"asc":asc,"asc_sign":SIGNS[ai],"asc_sign_th":SIGN_TH[ai],"asc_glyph":SIGN_GLYPH[ai],"asc_degree":round(asc%30,2),"mc":mc,"houses":houses,"asc_sign_index":ai}

def get_natal(b):
    jd=jd_for(b.date,b.time,b.tz); planets=planet_positions(jd); angles=house_data(jd,b.lat,b.lon); ai=angles["asc_sign_index"]
    for p in planets.values():
        p["house"]=house_of(p["longitude"],ai); p["house_th"]=HOUSE_TH[p["house"]-1]
    aspects=aspect_list(planets,planets,5,skip_same=True)
    return {"julian_day":jd,"birth_lat":b.lat,"birth_lon":b.lon,"planets":list(planets.values()),"planet_map":planets,"angles":angles,"aspects":aspects}

def aspect_list(transits,natal,max_orb=5,skip_same=False):
    found=[]
    for tn,t in transits.items():
      for nn,n in natal.items():
        if skip_same and tn==nn: continue
        diff=wrapdiff(t["longitude"],n["longitude"])
        for angle,en,th in ASPECTS:
          orb=abs(diff-angle)
          if orb<=max_orb:
            found.append({"transit":tn,"transit_th":t["thai"],"natal":nn,"natal_th":n["thai"],"aspect":en,"aspect_th":th,"angle":angle,"orb":round(orb,3),"separation":round(diff,3)})
    return sorted(found,key=lambda x:x["orb"])

def sect_data(n):
    """Determine sect from the Sun's actual altitude above/below the ASC-DSC horizon."""
    sun = n["planet_map"]["Sun"]
    jd = n["julian_day"]
    # swe.azalt expects ecliptic coordinates when using ECL2HOR.
    geopos = (n["birth_lon"], n["birth_lat"], 0.0)
    xin = (sun["longitude"], 0.0, 1.0)
    azimuth, true_altitude, apparent_altitude = swe.azalt(
        jd, swe.ECL2HOR, geopos, 0.0, 10.0, xin
    )
    is_day = true_altitude > 0
    return {
        "name": "กลางวัน (Day chart)" if is_day else "กลางคืน (Night chart)",
        "is_day": is_day,
        "sun_altitude": round(true_altitude, 4),
        "horizon_rule": "Sun above ASC–DSC horizon" if is_day else "Sun below ASC–DSC horizon",
        "benefic": "Jupiter" if is_day else "Venus",
        "malefic": "Mars" if is_day else "Saturn"
    }

def dignity_of(planet,sign):
    domicile={"Mars":["Aries","Scorpio"],"Venus":["Taurus","Libra"],"Mercury":["Gemini","Virgo"],"Moon":["Cancer"],"Sun":["Leo"],"Jupiter":["Sagittarius","Pisces"],"Saturn":["Capricorn","Aquarius"]}
    exalt={"Sun":"Aries","Moon":"Taurus","Jupiter":"Cancer","Mercury":"Virgo","Saturn":"Libra","Mars":"Capricorn","Venus":"Pisces"}
    detr={"Sun":["Aquarius"],"Moon":["Capricorn"],"Mercury":["Sagittarius","Pisces"],"Venus":["Aries","Scorpio"],"Mars":["Taurus","Libra"],"Jupiter":["Gemini","Virgo"],"Saturn":["Cancer","Leo"]}
    fall={"Sun":"Libra","Moon":"Scorpio","Jupiter":"Capricorn","Mercury":"Pisces","Saturn":"Aries","Mars":"Cancer","Venus":"Virgo"}
    if sign in domicile.get(planet,[]): return "เกษตร (Domicile)","มีความถนัดตามธรรมชาติในเรื่องที่ดาวดวงนี้เป็นตัวแทน"
    if exalt.get(planet)==sign: return "อุจจ์ (Exaltation)","มีศักยภาพโดดเด่น แต่ต้องดูเรือนและมุมสัมพันธ์ประกอบ"
    if sign in detr.get(planet,[]): return "ประ (Detriment)","ต้องปรับวิธีใช้พลังของดาว และอาจเจอเงื่อนไขที่ทำให้เรื่องนี้ไม่ไหลลื่น"
    if fall.get(planet)==sign: return "นิจ (Fall)","ต้องใช้เวลาและวินัยพัฒนาคุณภาพของดาว ไม่ได้แปลว่าจะเกิดเรื่องร้ายโดยอัตโนมัติ"
    return "ไม่มี Essential Dignity หลัก","ประเมินจากเรือน Sect และมุมสัมพันธ์ร่วมกัน ไม่ตัดสินว่าดีหรือเสียจากราศีอย่างเดียว"

def natal_summary(n, client_name=""):
    """Compatibility wrapper: always return the same complete reading as Natal."""
    return detailed_natal_reading(n, client_name)


def addressed(name, text):
    """Use the client's preferred name naturally, without mechanically replacing every pronoun."""
    name = (name or "").strip()
    if not name:
        return text.replace("เจ้าชะตา", "คุณ")
    # Replace the generic second-person address with the exact display name.
    return text.replace("เจ้าชะตา", name).replace("คุณ", name)


def planet_aspects_for(n, planet, orb_limit=6):
    rows=[]
    base=n["planet_map"][planet]
    for other, p in n["planet_map"].items():
        if other == planet:
            continue
        diff=wrapdiff(base["longitude"],p["longitude"])
        for angle, asp, asp_th in ASPECTS:
            orb=abs(diff-angle)
            if orb <= orb_limit:
                rows.append({"planet":other,"planet_th":PLANET_TH[other],"aspect":asp,"aspect_th":asp_th,"orb":round(orb,2)})
    return sorted(rows,key=lambda x:x["orb"])


def evidence_tone(planet, sign, house, aspects, sect):
    """Short plain-language synthesis from actual chart factors; no event certainty from one factor."""
    dignity=dignity_of(planet,sign)[0]
    supportive=[x for x in aspects if x["aspect"] in ("Trine","Sextile")]
    tense=[x for x in aspects if x["aspect"] in ("Square","Opposition")]
    if dignity.startswith(("เกษตร","อุจจ์")) and supportive:
        return "เป็นจุดแข็งที่ใช้ได้จริง มีทั้งกำลังของดาวและแรงส่งจากมุมสัมพันธ์ ถ้าเจ้าตัวลงมือ เรื่องนี้มีโอกาสพัฒนาได้ไกลกว่าค่าเฉลี่ย"
    if dignity.startswith(("ประ","นิจ")) and tense:
        return "จุดนี้ไม่ได้มาแบบสบาย ๆ ต้องออกแรงแก้และเรียนรู้จากข้อจำกัด มีโอกาสเจอเรื่องให้หงุดหงิดหรือรู้สึกว่าต้องแบกมากกว่าคนอื่น แต่ไม่ได้แปลว่าพัง แปลว่าต้องวางเกมให้ดี"
    if tense:
        return "เรื่องนี้มีแรงเสียดทานอยู่จริง มักต้องตัดสินใจหรือปรับวิธีรับมือก่อนถึงจะได้ผล อย่าคิดว่าทุกอย่างจะไหลไปเอง"
    if supportive:
        return "มีจังหวะและทรัพยากรช่วยอยู่พอสมควร เป็นเรื่องที่ต่อยอดได้ ถ้ากล้าหยิบโอกาสและไม่ปล่อยให้ผ่านไปเฉย ๆ"
    if dignity.startswith(("เกษตร","อุจจ์")):
        return "ดาวมีพื้นกำลังดี เป็นทุนที่เจ้าตัวพัฒนาให้เห็นผลได้ แต่ผลลัพธ์ยังขึ้นกับการใช้ชีวิตและจังหวะเวลา"
    return "เป็นเรื่องที่ต้องดูจากภาพรวมและประสบการณ์จริง ไม่ได้เด่นจนควรทุ่มหมดหน้าตัก และไม่ได้เสียจนต้องกลัวไปก่อน"

# Narrative synthesis rules: a transit is interpreted through planet + natal house + natal planet/aspect + linked house rulers.
def transit_orb(planet, aspect):
    if planet in ("Jupiter","Saturn"): return 2.0 if aspect in ("Conjunction","Opposition","Square") else 1.5
    if planet in ("Uranus","Neptune","Pluto"): return 2.0
    if planet=="Mars": return 1.0
    return 0.8

def event_story(tname,nname,aspect,house,orb,motion,sect):
    topic=HOUSE_TOPICS[house]
    aspect_tone={
      "Conjunction":"เรื่องนี้ถูกดึงขึ้นมาตรงหน้า เลี่ยงยาก และต้องตัดสินใจหรือจัดการบางอย่าง",
      "Sextile":"มีช่องเปิดหรือคนช่วยอยู่ แต่โอกาสจะเกิดผลก็ต่อเมื่อคุณลงมือ",
      "Trine":"เป็นจังหวะที่เรื่องนี้เดินง่ายขึ้น มีแรงช่วยหรือทางออกที่มองเห็นชัดกว่าเดิม",
      "Square":"มีแรงกดดันหรือเรื่องติดขัดเข้ามาบังคับให้แก้ ไม่เหมาะกับการปล่อยปัญหาค้างไว้",
      "Opposition":"ต้องจัดสมดุลระหว่างความต้องการของตัวเองกับคนอื่น หรือระหว่างสองเรื่องที่แย่งเวลาและพลังกัน"
    }[aspect]
    planet_scenarios={
      "Jupiter":"ข่าวดี โอกาส ข้อเสนอ การเรียนรู้ หรือคนที่เปิดประตูให้ แต่ต้องเช็กว่าผลประโยชน์คุ้มกับต้นทุนจริงไหม",
      "Saturn":"ภาระ หน้าที่ กฎเกณฑ์ เส้นตาย หรือข้อตกลงระยะยาวที่ต้องรับผิดชอบมากขึ้น อะไรที่ไม่มั่นคงจะถูกทดสอบ",
      "Uranus":"แผนเปลี่ยนกะทันหัน ตารางรวน ความต้องการอิสระ หรือข้อเสนอที่ไม่อยู่ในแผนเดิม ควรมีแผนสำรอง",
      "Neptune":"ข้อมูลไม่ครบ ความคาดหวังคลุมเครือ หรือเรื่องที่ต้องใช้เวลาแยกความจริงออกจากความรู้สึก อย่าเซ็นหรือตกลงเพราะเกรงใจ",
      "Pluto":"เกมอำนาจ ความไว้ใจ การควบคุม หรือเรื่องที่กดไว้นานกลับมาให้จัดการแบบถอนรากถอนโคน",
      "Mars":"เรื่องเร่งด่วน การแข่งขัน การปะทะ หรือการตัดสินใจเร็ว ระวังคำพูดและการทำอะไรตอนอารมณ์ขึ้น",
      "Venus":"ความสัมพันธ์ การเงิน การต่อรอง หรือสิ่งที่ทำให้รู้สึกมีคุณค่า มีโอกาสปรับความเข้าใจหรือเลือกสิ่งที่สบายใจกว่า",
      "Mercury":"ข่าว ข้อความ เอกสาร การนัดหมาย การเดินทางสั้น ๆ และการเจรจา ตรวจรายละเอียดให้ครบก่อนตอบตกลง",
      "Sun":"เรื่องนี้กลายเป็นจุดสนใจ ต้องแสดงตัว รับผิดชอบ หรือมีคนจับตามองผลงานมากขึ้น",
      "Moon":"อารมณ์ ความต้องการความมั่นคง บ้าน หรือครอบครัวทำให้ต้องปรับแผนและจัดลำดับความสำคัญ"
    }[tname]
    timing="กำลังเข้าใกล้จุดพีก" if motion=="Applying" else "ผ่านจุดพีกแล้ว แต่ผลยังค่อย ๆ คลี่คลาย" if motion=="Separating" else "อยู่ใกล้จุดพีก"
    risk="อย่าตัดสินใจด้วยความรีบหรือความกลัว และควรตรวจข้อเท็จจริงก่อน" if aspect in ("Square","Opposition") or tname in ("Saturn","Mars","Neptune") else "อย่าปล่อยโอกาสผ่านไปเพราะรอให้ทุกอย่างพร้อม 100%"
    return (f"ช่วงนี้เรื่อง{topic}มีแนวโน้มถูกดึงขึ้นมาให้จัดการ เพราะดาวจร{PLANET_TH[tname]}กำลังกระทบดาวกำเนิด{PLANET_TH[nname]}ในมุม{dict((x[1],x[2]) for x in ASPECTS)[aspect]} {aspect_tone} ภาพที่อาจเห็นในชีวิตจริงคือ{planet_scenarios} {risk} ตอนนี้{timing} โดยมี orb {orb:.2f}° จึงให้น้ำหนักกับประเด็นนี้ตามความใกล้ของมุมดาว ไม่ได้แปลว่าทุกคนจะเจอเหตุการณ์เดียวกัน แต่เป็นหน้าต่างเวลาที่เรื่องนี้มีโอกาสเด่นขึ้น")

def event_intensity(orb,planet,aspect):
    if orb<=0.25: return "สูงมาก"
    if orb<=0.75: return "สูง"
    if orb<=1.5: return "ปานกลางถึงสูง"
    return "กำลังทำงาน"

def exact_aspect_events(transits,natal,asc_idx,sect):
    rows=[]
    for tname in SLOW_PLANETS+["Mars","Venus","Mercury","Sun"]:
      t=transits[tname]
      for nname,n in natal["planet_map"].items():
        diff=wrapdiff(t["longitude"],n["longitude"])
        for angle,asp,asp_th in ASPECTS:
          orb=abs(diff-angle); limit=transit_orb(tname,asp)
          if orb<=limit:
            house=house_of(n["longitude"],asc_idx)
            rows.append({"planet":tname,"planet_th":PLANET_TH[tname],"natal_planet":nname,"natal_planet_th":PLANET_TH[nname],"aspect":asp,"aspect_th":asp_th,"orb":round(orb,3),"house":house,"intensity":event_intensity(orb,tname,asp),"story":event_story(tname,nname,asp,house,orb,"Applying",sect)})
    rows.sort(key=lambda x:(x["orb"],SLOW_PLANETS.index(x["planet"]) if x["planet"] in SLOW_PLANETS else 9))
    return rows

def daily_planet(jd,planet):
    xx,_=swe.calc_ut(jd,PLANET_IDS[planet],FLAGS)
    return xx[0]%360,xx[3]

def find_ingresses_and_stations(start_date,months,tz):
    start=datetime.fromisoformat(start_date).date(); end=start+timedelta(days=round(months*30.436875))
    events=[]
    # Daily scan, then binary-search the transition to within about a minute.
    for planet in SLOW_PLANETS+["Mars","Venus","Mercury"]:
      prev_date=start; prev_jd=jd_for(prev_date.isoformat(),"12:00",tz); prev_lon,prev_speed=daily_planet(prev_jd,planet)
      prev_sign=sign_index(prev_lon); prev_retro=prev_speed<0
      d=start+timedelta(days=1)
      while d<=end:
        jd=jd_for(d.isoformat(),"12:00",tz); lon,speed=daily_planet(jd,planet); si=sign_index(lon); retro=speed<0
        if si!=prev_sign:
          # Find date boundary by bisection on unwrapped longitude, respecting direct motion.
          lo=jd-1; hi=jd
          for _ in range(24):
            mid=(lo+hi)/2; mlon,_=daily_planet(mid,planet)
            # Compare against the crossed 30-degree boundary in direction of motion.
            if prev_speed>=0:
              boundary=(prev_sign+1)*30
              unwrapped=mlon
              while unwrapped < prev_lon-180: unwrapped+=360
              if unwrapped < boundary: lo=mid
              else: hi=mid
            else:
              boundary=prev_sign*30
              unwrapped=mlon
              while unwrapped > prev_lon+180: unwrapped-=360
              if unwrapped > boundary: lo=mid
              else: hi=mid
          moment=(lo+hi)/2
          y,m,day,hour=swe.revjul(moment,swe.GREG_CAL)
          utc=datetime(y,m,day)+timedelta(hours=hour)
          local=utc+timedelta(hours=tz)
          new_si=si
          events.append({"date":local.strftime("%Y-%m-%d"),"date_label":fmt_date(local),"planet":planet,"planet_th":PLANET_TH[planet],"type":"ingress","title":f"{PLANET_TH[planet]} ย้ายเข้าราศี{SIGN_TH[new_si]}","from_sign":SIGN_TH[prev_sign],"to_sign":SIGN_TH[new_si],"description":f"ดาว{PLANET_TH[planet]}ย้ายจากราศี{SIGN_TH[prev_sign]} เข้าราศี{SIGN_TH[new_si]} พลังของดาวจึงเปลี่ยนโทน และย้ายไปเน้นเรื่องเรือนใหม่ตามลัคนาของคุณ"})
        if retro!=prev_retro:
          # Station date estimated by bisection on longitudinal speed sign change.
          lo=jd-1; hi=jd
          for _ in range(24):
            mid=(lo+hi)/2; _,ms=daily_planet(mid,planet)
            if (ms<0)==prev_retro: lo=mid
            else: hi=mid
          moment=(lo+hi)/2; y,m,day,hour=swe.revjul(moment,swe.GREG_CAL)
          local=datetime(y,m,day)+timedelta(hours=hour)
          local=local+timedelta(hours=tz)
          typ="retrograde" if retro else "direct"
          events.append({"date":local.strftime("%Y-%m-%d"),"date_label":fmt_date(local),"planet":planet,"planet_th":PLANET_TH[planet],"type":typ,"title":f"{PLANET_TH[planet]} เริ่มถอยหลัง" if retro else f"{PLANET_TH[planet]} กลับมาเดินหน้า","description":f"ดาว{PLANET_TH[planet]} เปลี่ยนทิศทางการเคลื่อนที่ ช่วงนี้เหมาะกับการทบทวนหรือเดินหน้าเรื่องที่เกี่ยวข้องอย่างมีสติ ไม่ได้แปลว่าทุกเรื่องจะหยุดหรือเกิดปัญหาแน่นอน"})
        prev_date=d; prev_jd=jd; prev_lon=lon; prev_speed=speed; prev_sign=si; prev_retro=retro
        d+=timedelta(days=1)
    events.sort(key=lambda x:x["date"])
    return events

def transit_house_stories(transits,asc_idx):
    rows=[]
    for p in SLOW_PLANETS:
      x=transits[p]; h=house_of(x["longitude"],asc_idx)
      rows.append({"planet":p,"planet_th":PLANET_TH[p],"sign":x["sign"],"sign_th":x["sign_th"],"degree":x["degree"],"house":h,"retrograde":x["retrograde"],"topic":HOUSE_TOPICS[h],"meaning":PLANET_MEANING[p],"story":f"ดาว{PLANET_TH[p]}อยู่เรือน {h} ({HOUSE_TH[h-1]}) ซึ่งเป็นเรื่อง{HOUSE_TOPICS[h]} เมื่อรวมกับความหมายของดาวที่เกี่ยวกับ{PLANET_MEANING[p]} จึงเป็นธีมระยะยาวที่ควรสังเกต ไม่ใช่เหตุการณ์เฉพาะวัน"})
    return rows

def natal_event_links(n,transit_aspects):
    # Link transit hit to natal planet's house and the house ruled by that natal planet.
    asc_idx=n["angles"]["asc_sign_index"]; out=[]
    for a in transit_aspects:
      natal_p=n["planet_map"][a["natal"]]
      natal_house=natal_p["house"]
      ruled=[]
      for i,r in enumerate(TRAD_RULER):
        if r==a["natal"]: ruled.append(i+1)
      out.append({**a,"planet":a["transit"],"planet_th":a["transit_th"],"natal_planet":a["natal"],"natal_planet_house":natal_house,"natal_planet_house_topic":HOUSE_TOPICS[natal_house],"ruled_houses":ruled,"linked_topics":[HOUSE_TOPICS[h] for h in ruled]})
    return out


TERMS_EGYPTIAN = {
 "Aries":[(6,"Jupiter"),(14,"Venus"),(21,"Mercury"),(26,"Mars"),(30,"Saturn")],
 "Taurus":[(8,"Venus"),(14,"Mercury"),(22,"Jupiter"),(27,"Saturn"),(30,"Mars")],
 "Gemini":[(6,"Mercury"),(12,"Jupiter"),(17,"Venus"),(24,"Mars"),(30,"Saturn")],
 "Cancer":[(7,"Mars"),(13,"Venus"),(19,"Mercury"),(26,"Jupiter"),(30,"Saturn")],
 "Leo":[(6,"Jupiter"),(11,"Venus"),(18,"Saturn"),(24,"Mercury"),(30,"Mars")],
 "Virgo":[(7,"Mercury"),(13,"Venus"),(18,"Jupiter"),(24,"Mars"),(30,"Saturn")],
 "Libra":[(6,"Saturn"),(14,"Mercury"),(21,"Jupiter"),(28,"Venus"),(30,"Mars")],
 "Scorpio":[(7,"Mars"),(11,"Venus"),(19,"Mercury"),(24,"Jupiter"),(30,"Saturn")],
 "Sagittarius":[(12,"Jupiter"),(17,"Venus"),(21,"Mercury"),(26,"Saturn"),(30,"Mars")],
 "Capricorn":[(7,"Mercury"),(14,"Jupiter"),(22,"Venus"),(26,"Saturn"),(30,"Mars")],
 "Aquarius":[(7,"Mercury"),(13,"Venus"),(20,"Jupiter"),(25,"Mars"),(30,"Saturn")],
 "Pisces":[(12,"Venus"),(16,"Jupiter"),(19,"Mercury"),(28,"Mars"),(30,"Saturn")]
}

def term_ruler(sign, degree):
    for bound, ruler in TERMS_EGYPTIAN[sign]:
        if degree < bound:
            return ruler
    return TERMS_EGYPTIAN[sign][-1][1]

def lot_positions(n):
    a=n["angles"]["asc"]
    sun=n["planet_map"]["Sun"]["longitude"]
    moon=n["planet_map"]["Moon"]["longitude"]
    day=sect_data(n)["is_day"]
    fortune=(a + moon - sun) % 360 if day else (a + sun - moon) % 360
    spirit=(a + sun - moon) % 360 if day else (a + moon - sun) % 360
    def describe(lon):
        si=sign_index(lon); h=house_of(lon,n["angles"]["asc_sign_index"])
        ruler=TRAD_RULER[si]; rp=n["planet_map"][ruler]
        return {"longitude":round(lon,5),"sign":SIGNS[si],"sign_th":SIGN_TH[si],"degree":round(lon%30,2),"house":h,"house_th":HOUSE_TH[h-1],"ruler":ruler,"ruler_position":rp,"ruler_dignity":dignity_of(ruler,rp["sign"])[0]}
    return {"fortune":describe(fortune),"spirit":describe(spirit)}

def aspect_narrative(aspect):
    names={"Conjunction":"พลังของดาวสองดวงรวมกันและทำงานเข้มข้น","Sextile":"มีช่องทางสนับสนุน แต่ต้องเลือกลงมือ","Square":"เกิดแรงเสียดทานที่ผลักให้ปรับตัว","Trine":"ความสามารถหรือโอกาสไหลต่อกันได้ง่าย","Opposition":"ต้องจัดสมดุลระหว่างสองด้านที่ดึงกันคนละทาง"}
    return names[aspect]

def house_ruler_map(n):
    ai=n["angles"]["asc_sign_index"]; pm=n["planet_map"]; out={}
    for h in range(1,13):
        si=(ai+h-1)%12; ruler=TRAD_RULER[si]; rp=pm[ruler]
        out[h]={"house":h,"sign":SIGNS[si],"sign_th":SIGN_TH[si],"ruler":ruler,"ruler_th":PLANET_TH[ruler],"ruler_house":rp["house"],"ruler_sign":rp["sign"],"ruler_sign_th":rp["sign_th"],"dignity":dignity_of(ruler,rp["sign"])[0],"retrograde":rp["retrograde"]}
    return out

def detailed_natal_reading(n, client_name=""):
    pm=n["planet_map"]; a=n["angles"]; sect=sect_data(n); lots=lot_positions(n); rulers=house_ruler_map(n)
    asc_ruler=TRAD_RULER[a["asc_sign_index"]]; asc=pm[asc_ruler]
    moon=pm["Moon"]; sun=pm["Sun"]
    sections=[]
    def add(title,text): sections.append({"title":title,"text":text})
    asc_dig=dignity_of(asc_ruler,asc["sign"])
    asc_asp=planet_aspects_for(n,asc_ruler)
    add("01 · ตัวตนและบุคลิกที่คนอื่นเห็น",f"ถ้าพูดกันตรง ๆ ลัคนา{a['asc_sign_th']} ทำให้ภาพแรกที่คนเห็นเป็นคนที่มีสไตล์แบบนี้ แต่ตัวตนจริง ๆ ของคุณไม่ได้มีแค่นั้น เพราะดาวประจำตัวคือ{PLANET_TH[asc_ruler]} ไปอยู่ราศี{asc['sign_th']} เรือน {asc['house']} เรื่อง{HOUSE_TOPICS[asc['house']]} เลยกลายเป็นธีมที่วนกลับมาให้ตัดสินใจอยู่เรื่อย ๆ ดาวดวงนี้มีสถานะ{asc_dig[0]} และ{evidence_tone(asc_ruler,asc['sign'],asc['house'],asc_asp,sect)} {('มุมที่เด่นคือ ' + ', '.join(x['planet_th']+' '+x['aspect_th']+' '+str(x['orb'])+'°' for x in asc_asp[:3]) + ' ซึ่งทำให้เรื่องนี้มีแรงหนุนหรือแรงกดเข้ามาเกี่ยวข้องชัดขึ้น' ) if asc_asp else 'ดาวประจำตัวไม่มีมุมหลักที่แน่นในเกณฑ์นี้ จึงให้น้ำหนักกับราศี เรือน และ Sect เป็นหลัก'} นี่คือเหตุผลว่าทำไมบางครั้งคนอื่นอาจมองคุณแบบหนึ่ง แต่แรงขับข้างในกลับพาไปอีกทาง")
    moon_element={'Aries':'ไฟ','Leo':'ไฟ','Sagittarius':'ไฟ','Taurus':'ดิน','Virgo':'ดิน','Capricorn':'ดิน','Gemini':'ลม','Libra':'ลม','Aquarius':'ลม','Cancer':'น้ำ','Scorpio':'น้ำ','Pisces':'น้ำ'}[moon['sign']]
    moon_selfcare={'ไฟ':'ขยับตัว ออกกำลัง เต้น หรือทำอะไรที่ได้ปล่อยพลัง','ดิน':'อยู่กับธรรมชาติ จัดบ้าน ทำอาหาร หรือทำกิจวัตรที่จับต้องได้','ลม':'อ่าน เขียน คุยกับคนที่คุยรู้เรื่อง หรือเรียนอะไรใหม่','น้ำ':'อยู่เงียบ ๆ ฟังเพลง อยู่ใกล้น้ำ หรือให้เวลาตัวเองได้รู้สึก'}[moon_element]
    moon_asp=planet_aspects_for(n,'Moon')
    add("02 · โลกภายใน ความรู้สึก และวิธีชาร์จพลัง",f"ข้างในคุณต้องการความรู้สึกแบบไหนถึงจะโอเค? ดูจากจันทร์ราศี{moon['sign_th']} ธาตุ{moon_element} เรือน {moon['house']} เรื่อง{HOUSE_TOPICS[moon['house']]}. เวลาเรื่องนี้ไม่ลงตัว อารมณ์มักเป็นตัวฟ้องก่อนเหตุผล คุณอาจรู้สึกหมดแรง หงุดหงิด หรืออยากถอยออกมาก่อนจะอธิบายได้ด้วยซ้ำ {evidence_tone('Moon',moon['sign'],moon['house'],moon_asp,sect)} วิธีชาร์จพลังที่เข้ากับดวงจันทร์ดวงนี้คือ{moon_selfcare} ไม่ใช่ฝืนทำตามสูตรของคนอื่น {('มุมที่ต้องจับตาคือ '+', '.join(x['planet_th']+' '+x['aspect_th']+' '+str(x['orb'])+'°' for x in moon_asp[:3])+'.') if moon_asp else 'จันทร์ไม่มีมุมหลักที่แน่นในเกณฑ์ที่ใช้ จึงเน้นอ่านจากราศีและเรือนเป็นหลัก'}")
    merc=pm['Mercury']; merc_asp=planet_aspects_for(n,'Mercury')
    add("03 · ความคิด การสื่อสาร และการตัดสินใจ",f"สมองของคุณไปทำงานหนักกับเรื่อง{HOUSE_TOPICS[merc['house']]} เพราะพุธอยู่ราศี{merc['sign_th']} เรือน {merc['house']} จุดนี้ทำให้การพูด การคิด การเรียนรู้ หรือการจัดการข้อมูลมักเป็นเครื่องมือสำคัญเวลาจะเอาตัวรอดหรือสร้างโอกาส {evidence_tone('Mercury',merc['sign'],merc['house'],merc_asp,sect)} {('เวลามีเรื่อง '+', '.join(x['planet_th']+' '+x['aspect_th'] for x in merc_asp[:2])+' เข้ามาเกี่ยวข้อง ให้ระวังการสื่อสารที่รีบเกินไปหรือการตัดสินใจจากข้อมูลไม่ครบ') if merc_asp else 'จุดนี้ไม่ได้มีมุมหลักมาขยายแรงมากเป็นพิเศษ จึงควรดูการใช้ทักษะจริงและสภาพแวดล้อมประกอบ'}")
    ven=pm['Venus']; mar=pm['Mars']; venasp=planet_aspects_for(n,'Venus'); marasp=planet_aspects_for(n,'Mars')
    add("04 · ความรัก วิธีรัก และแรงดึงดูด",f"เรื่องรักไม่ได้ดูแค่ว่าคุณชอบคนแบบไหน แต่ดูด้วยว่าคุณต้องการอะไรจากความสัมพันธ์และเวลามีปัญหาคุณตอบสนองยังไง ศุกร์อยู่ราศี{ven['sign_th']} เรือน {ven['house']} ทำให้ความสุขและความรู้สึกถูกรักผูกกับเรื่อง{HOUSE_TOPICS[ven['house']]}; ส่วนอังคารอยู่ราศี{mar['sign_th']} เรือน {mar['house']} บอกวิธีเดินหน้าและวิธีปะทะเมื่อไม่พอใจ {evidence_tone('Venus',ven['sign'],ven['house'],venasp,sect)} ขณะที่อังคารบอกว่าตอนโกรธหรืออยากได้อะไร คุณอาจ{('ตอบสนองค่อนข้างแรงหรือเร็ว' if marasp and any(x['aspect'] in ('Square','Opposition') for x in marasp) else 'เลือกลงมือหรือแสดงออกตามจังหวะของตัวเอง')} เรือน 5 เจ้าเรือน{PLANET_TH[rulers[5]['ruler']]} ไปอยู่เรือน {rulers[5]['ruler_house']} ส่วนเรือน 7 เจ้าเรือน{PLANET_TH[rulers[7]['ruler']]} ไปอยู่เรือน {rulers[7]['ruler_house']} ภาพนี้จึงต้องแยกความหวือหวาตอนเริ่มรักออกจากความพร้อมใช้ชีวิตร่วมกัน")
    add("05 · คู่ครองและบริบทที่อาจพบกัน",f"ลักษณะคู่ที่ดึงดูดอ่านจากราศีเรือน 7 และเจ้าเรือน 7 ไม่ใช่คำบรรยายรูปลักษณ์ตายตัว เจ้าเรือน 7 {PLANET_TH[rulers[7]['ruler']]} อยู่เรือน {rulers[7]['ruler_house']} จึงชี้บริบทที่ความสัมพันธ์อาจเชื่อมโยงกับ{HOUSE_TOPICS[rulers[7]['ruler_house']]}. ตัวอย่างเช่น หากเรือนนี้เกี่ยวกับงาน อาจรู้จักผ่านหน้าที่ ลูกค้า หรือเครือข่ายงาน; หากเกี่ยวกับการเรียนหรือเดินทาง อาจพบผ่านคอร์ส การเดินทาง หรือคนต่างถิ่น ต้องดูดาวร่วมและบริบทจริงก่อนระบุสถานที่เฉพาะ")
    money_ruler=rulers[2]['ruler']; money_planet=pm[money_ruler]; money_asp=planet_aspects_for(n,money_ruler)
    add("06 · การเงิน: หาเงินจากอะไรและเหนื่อยแค่ไหน",f"เรื่องหาเงินของคุณมีจุดเชื่อมกับ{HOUSE_TOPICS[rulers[2]['ruler_house']]}แบบชัด ๆ เพราะเจ้าเรือน 2 คือ{PLANET_TH[money_ruler]} อยู่ราศี{money_planet['sign_th']} เรือน {money_planet['house']} และมีสถานะ{rulers[2]['dignity']} ถ้าจะสร้างรายได้ให้โต ช่องทางที่เข้ากับดวงคือการต่อยอดเรื่องนี้ ไม่ใช่หวังพึ่งโชคอย่างเดียว {evidence_tone(money_ruler,money_planet['sign'],money_planet['house'],money_asp,sect)} ด้านอาชีพ เจ้าเรือน 10 คือ{PLANET_TH[rulers[10]['ruler']]} อยู่เรือน {rulers[10]['ruler_house']} ภาพหาเงินกับภาพงานจึง{('เชื่อมกันผ่านเรื่องเดียวกัน' if rulers[10]['ruler_house']==rulers[2]['ruler_house'] else 'มีคนละสนาม ต้องวางแผนให้สองด้านส่งแรงถึงกัน')} ถ้าต้องการรายได้ที่มั่นคง อย่าปล่อยให้ทักษะที่ทำเงินได้อยู่แค่ในงานประจำหรือช่องทางเดียว")
    add("07 · เงินเก็บ หนี้ และจุดเงินรั่ว",f"หาเงินเก่งอย่างเดียวไม่พอ ต้องดูด้วยว่าเงินอยู่กับคุณได้นานแค่ไหน เจ้าเรือน 8 คือ{PLANET_TH[rulers[8]['ruler']]} ไปอยู่เรือน {rulers[8]['ruler_house']} ส่วนเจ้าเรือน 12 คือ{PLANET_TH[rulers[12]['ruler']]} ไปอยู่เรือน {rulers[12]['ruler_house']} เรื่องเงินร่วม ภาระ หนี้ ภาษี และค่าใช้จ่ายที่มองไม่เห็นจึงอาจเข้ามาผ่านเรื่อง{HOUSE_TOPICS[rulers[8]['ruler_house']]} และ{HOUSE_TOPICS[rulers[12]['ruler_house']]} {('ที่น่าสนใจคือเจ้าเรือนการเงินไปเชื่อมกับเรือน 8/12 ด้วย จึงควรจริงจังกับสัญญาและเงินสำรองเป็นพิเศษ' if rulers[2]['ruler_house'] in (8,12) else 'ยังไม่มีเหตุผลพอจะฟันธงว่าต้องเป็นหนี้หรือเสียเงินก้อน แต่การแยกบัญชีเงินตัวเองกับเงินร่วมจะช่วยกันปัญหาได้มาก')}")
    f=lots['fortune']; sp=lots['spirit']
    add("08 · Lot of Fortune และ Lot of Spirit",f"Lot of Fortune อยู่ราศี{f['sign_th']} เรือน {f['house']} ({HOUSE_TH[f['house']-1]}) เจ้าเรือนคือ{PLANET_TH[f['ruler']]} ไปอยู่เรือน {f['ruler_position']['house']} และมีศักดิ์ {f['ruler_dignity']}. จุดนี้ใช้ดูเงื่อนไขทางกายภาพ โอกาส ทรัพยากร และสิ่งที่เข้ามาโดยไม่ต้องควบคุมทั้งหมด ส่วน Lot of Spirit อยู่ราศี{sp['sign_th']} เรือน {sp['house']} เจ้าเรือนคือ{PLANET_TH[sp['ruler']]} ไปอยู่เรือน {sp['ruler_position']['house']} ใช้อ่านเจตจำนง การเลือก และทิศทางที่เจ้าชะตาลงมือสร้างด้วยตัวเอง")
    add("09 · งาน อาชีพ และรูปแบบการทำงานประจำวัน",f"เรือน 10 และ MC เป็นคนละข้อมูล: Whole Sign เรือน 10 ใช้อ่านอาชีพและสถานะ ส่วน MC เป็นองศาจริงที่อาจตกเรือนใดก็ได้ MC อยู่ที่ {a['mc']:.2f}° ราศี{SIGN_TH[sign_index(a['mc'])]}. เจ้าเรือน 10 คือ{PLANET_TH[rulers[10]['ruler']]} อยู่เรือน {rulers[10]['ruler_house']}; Mercury อยู่เรือน {pm['Mercury']['house']}, Venus เรือน {pm['Venus']['house']}, Mars เรือน {pm['Mars']['house']} เป็นเครื่องมือด้านคิด-สื่อสาร มนุษยสัมพันธ์ และลงมือแก้ปัญหา ส่วนเรือน 6 อยู่ราศี{rulers[6]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[6]['ruler_house']} จึงบอกสภาพงานประจำวันและความเหน็ดเหนื่อยที่ต้องจัดการ")
    add("10 · บ้าน ครอบครัว พี่น้อง และการศึกษา",f"เรือน 4 อยู่ราศี{rulers[4]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[4]['ruler_house']} ใช้อ่านบ้าน รากฐาน และพื้นที่ส่วนตัว; เรือน 3 อยู่ราศี{rulers[3]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[3]['ruler_house']} ใช้อ่านพี่น้อง การสื่อสาร และการเรียนรู้ใกล้ตัว; เรือน 9 อยู่ราศี{rulers[9]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[9]['ruler_house']} ใช้อ่านการศึกษาสูง ต่างประเทศ และโลกทัศน์ การอ่านต้องพิจารณาดาวที่อยู่ในเรือนเหล่านี้ด้วย")
    add("11 · บุตร ความสร้างสรรค์ เพื่อน และเครือข่าย",f"เรือน 5 อยู่ราศี{rulers[5]['sign_th']} และเจ้าเรือนอยู่เรือน {rulers[5]['ruler_house']} ใช้อ่านความสุข งานสร้างสรรค์ ความรักแบบโรแมนติก และบุตร ส่วนเรือน 11 อยู่ราศี{rulers[11]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[11]['ruler_house']} ใช้อ่านเพื่อน กลุ่มคน ผู้สนับสนุน และผลตอบแทนจากอาชีพ ควรดูดาวในเรือนและมุมสัมพันธ์ก่อนให้คำตอบเฉพาะเรื่องจำนวนบุตรหรือผลสำเร็จ")
    add("12 · สุขภาพ พลังงาน และข้อควรระวัง",f"ในเชิงโหราศาสตร์ให้ตรวจเรือน 1, 6, 8 และ 12 รวมถึงเจ้าเรือนและดาวที่สัมพันธ์กัน: เรือน 1 เจ้าเรือนอยู่เรือน {rulers[1]['ruler_house']}, เรือน 6 เจ้าเรือนอยู่เรือน {rulers[6]['ruler_house']}, เรือน 12 เจ้าเรือนอยู่เรือน {rulers[12]['ruler_house']}. อ่านเป็นแนวโน้มเรื่องการดูแลตัวเอง ความเครียด และกิจวัตร ไม่ใช่การวินิจฉัยโรคหรือระบุอายุที่จะป่วย หากมีอาการจริงให้ใช้การตรวจทางการแพทย์")
    add("13 · จุดแข็ง จุดท้าทาย และการปรับใช้",f"จุดแข็งควรดูดาวที่มี Essential Dignity, อยู่ใน Sect ที่เหมาะ และได้รับมุมสนับสนุน; จุดท้าทายดูดาวที่เสียศักดิ์ ถูกกดด้วยมุมตึง หรือทำหน้าที่เป็นเจ้าเรือนสำคัญโดยมีเงื่อนไขมาก การแก้เกมคือเปลี่ยนคำอ่านให้เป็นการกระทำ: วางระบบเงินเมื่อเรือน 2/8/12 เชื่อมกัน, ทำขอบเขตความสัมพันธ์เมื่อเรือน 7 ถูกกด, และจัดตารางพักเมื่อเรือน 6/12 เด่น")
    client_name = (client_name or "").strip()
    for section in sections:
        section["text"] = addressed(client_name, section["text"])
    return {"client_name":client_name,"ascendant":a,"asc_ruler":asc_ruler,"ruler_position":asc,"sect":sect,"ruler_dignity":asc_dig,"story":sections[0]["text"],"sections":sections,"house_rulers":rulers,"lots":lots,"moon_self_care":{"sign":moon['sign'],"sign_th":moon['sign_th'],"house":moon['house'],"house_th":moon['house_th']},"prenatal_syzygy":prenatal_syzygy(n),"planet_details":planet_detail_table(n)}

def planet_detail_table(n):
    out=[]
    for name,p in n['planet_map'].items():
        dig=dignity_of(name,p['sign'])
        out.append({**p,"dignity":dig[0],"dignity_note":dig[1],"term_ruler":term_ruler(p['sign'],p['degree'])})
    return out

def prenatal_syzygy(n):
    """Find the nearest preceding lunation (new/full moon) by scanning phase angle."""
    jd=n['julian_day']; found=None; prev=None
    # Search backwards in 0.25-day steps for the last 0/180 degree phase crossing.
    step=0.25; t=jd; prev_angle=wrapdiff(n['planet_map']['Moon']['longitude'],n['planet_map']['Sun']['longitude'])
    for _ in range(120):
        t-=step; pos=planet_positions(t); angle=wrapdiff(pos['Moon']['longitude'],pos['Sun']['longitude'])
        # phase separation 0=new moon, 180=full moon; detect crossing near either phase
        target=min((0,180),key=lambda z:abs(angle-z))
        if abs(angle-target)<1.0:
            lo=t-step; hi=t+step
            for __ in range(20):
                mid=(lo+hi)/2; pp=planet_positions(mid); aa=wrapdiff(pp['Moon']['longitude'],pp['Sun']['longitude'])
                if abs(aa-target)<abs(prev_angle-target): hi=mid
                else: lo=mid
            moment=(lo+hi)/2; pp=planet_positions(moment); found={'type':'New Moon' if target==0 else 'Full Moon','sun_sign':pp['Sun']['sign'],'moon_sign':pp['Moon']['sign'],'approx_julian_day':round(moment,5)}
            break
        prev_angle=angle
    return found or {"note":"ไม่สามารถระบุ lunation ก่อนเกิดได้ในรอบค้นหานี้"}

@app.get("/")
def index(): return HTMLResponse((ROOT/"index.html").read_text(encoding="utf-8"))
@app.get("/api/health")
def health(): return {"ok":True,"engine":"Swiss Ephemeris via Moshier","version":swe.version,"rota_version":"3.1.0"}

@app.post("/api/natal")
def natal(b:Birth):
  try:
    n=get_natal(b); s=detailed_natal_reading(n,b.name)
    return {"birth":b.model_dump(),"client_name":b.name,"chart":n,"interpretation":s,"engine_note":"Swiss Ephemeris / Moshier; Tropical Zodiac; Whole Sign Houses; traditional rulers; sect from actual solar altitude."}
  except Exception as e: raise HTTPException(400,f"คำนวณดวงไม่สำเร็จ: {e}")

@app.post("/api/annual")
def annual(req:AnnualRequest):
  try:
    n=get_natal(req); age=req.annual_year-int(req.date[:4]);
    # Annual period begins on birthday; selected year is the birthday year.
    if age<0: raise ValueError("ปีที่เลือกอยู่ก่อนปีเกิด")
    house_num=(age%12)+1; asc_idx=n["angles"]["asc_sign_index"]; sign_idx=(asc_idx+house_num-1)%12
    ruler=TRAD_RULER[sign_idx]; rd=n["planet_map"][ruler]; sect=sect_data(n)
    dign,dignote=dignity_of(ruler,rd["sign"])
    ruler_house=rd["house"]; ruler_house_topic=HOUSE_TOPICS[ruler_house]
    natal_aspects=[]
    for p in n["planet_map"].values():
      if p["name"]==ruler: continue
      diff=wrapdiff(rd["longitude"],p["longitude"])
      for angle,asp,asp_th in ASPECTS:
        orb=abs(diff-angle)
        if orb<=6: natal_aspects.append({"planet":p["name"],"planet_th":p["thai"],"aspect":asp,"aspect_th":asp_th,"orb":round(orb,2)})
    natal_aspects.sort(key=lambda x:x["orb"])
    sign_th=SIGN_TH[sign_idx]; house_topic=HOUSE_TOPICS[house_num]
    # The narrative explicitly distinguishes annual profection theme from natal placement of its ruler.
    overview=(f"ปีอายุ {age} เป็นปีเรือน {house_num} ({HOUSE_TH[house_num-1]}) ราศี{sign_th} ธีมตั้งต้นจึงอยู่ที่{house_topic}. "
      f"แต่เราไม่หยุดแค่นั้น เพราะดาวเจ้าเรือนปีคือ{PLANET_TH[ruler]} ไปอยู่เรือนกำเนิด {ruler_house} ({HOUSE_TH[ruler_house-1]}) ซึ่งเกี่ยวกับ{ruler_house_topic}. "
      f"แปลเป็นภาษาชีวิตคือ เรื่องของเรือน {house_num} มีแนวโน้มเดินเรื่องผ่านเรื่องของเรือน {ruler_house} เช่น ถ้าปีนี้มีประเด็นเรื่องคนหรือข้อตกลง ก็อาจพาไปคุยเรื่องทรัพยากรร่วม ความรับผิดชอบ หรือความไว้ใจตามความหมายของตำแหน่งดาวนี้ ทั้งนี้ต้องอ่านมุมสัมพันธ์และดาวเจ้าเรือนอื่นประกอบก่อนสรุปเหตุการณ์เฉพาะ")
    sections=[
      {"title":"ภาพรวมและธีมหลักของปี","text":overview+f" โทนของราศี{sign_th}คือ{SIGN_STYLE[SIGNS[sign_idx]]}. รอบปีนี้นับจากวันเกิด {req.annual_year}-{req.date[5:]} ถึงวันเกิดปีถัดไป ไม่ใช่ปีปฏิทินเต็มปี."},
      {"title":"Lord of the Year — ดาวที่พาเรื่องของปีไปสู่ชีวิตจริง","text":f"{PLANET_TH[ruler]} อยู่ราศี{rd['sign_th']} {rd['degree']:.2f}° เรือน {ruler_house} และ{('กำลังถอยหลัง' if rd['retrograde'] else 'เดินหน้า')}. คุณภาพดาว: {dign}. {dignote}. ดาวนี้แทนเรื่อง{PLANET_MEANING[ruler]}. เมื่อเอามารวมกับเรือน {ruler_house} จะเห็นว่าธีมปีไม่ได้เกิดลอย ๆ แต่ต้องผ่านเรื่อง{ruler_house_topic}. ราศี{rd['sign_th']}ทำให้วิธีรับมือมีโทนว่า{SIGN_STYLE[rd['sign']]}."},
      {"title":"การงานและทิศทางอาชีพ","text":f"ปีนี้เรื่องงานมีแนวโน้มเดินผ่านเรื่อง{ruler_house_topic} มากกว่าจะมาแบบลอย ๆ เจ้าเรือนปี {PLANET_TH[ruler]} ไปอยู่เรือน {ruler_house} และเรือน 10 มีเจ้าเรือน {PLANET_TH[TRAD_RULER[(asc_idx+9)%12]]} อยู่เรือน {n['planet_map'][TRAD_RULER[(asc_idx+9)%12]]['house']} ถ้าจังหวะงานขยับ ภาพที่ควรจับตาคือการเปลี่ยนหน้าที่ การรับผิดชอบคนหรือข้อตกลง การใช้ทักษะเฉพาะตัว หรือการต้องตัดสินใจเรื่องเส้นทางอาชีพ {('มีมุมสนับสนุนจาก '+', '.join(x['planet_th']+' '+x['aspect_th'] for x in natal_aspects[:2])+' จึงมีแรงช่วยให้เดินหน้าได้') if natal_aspects else 'ยังไม่มีมุมแน่นจากดาวเจ้าเรือนปีมาช่วยยืนยันการเปลี่ยนแปลงใหญ่ จึงอย่าเพิ่งลาออกหรือเสี่ยงโดยไม่มีแผนรองรับ'}"},
      {"title":"การเงินและทรัพยากรร่วม","text":f"ปีนี้เงินของคุณต้องดูทั้งรายได้ตัวเองและภาระที่ต้องแชร์กับคนอื่น เจ้าเรือนปี {PLANET_TH[ruler]} อยู่เรือน {ruler_house} เรื่อง{ruler_house_topic} จึงอาจพาให้ต้องจัดระบบเงิน แบ่งค่าใช้จ่าย คุยเรื่องหนี้หรือทรัพย์สินร่วม หรือคิดใหม่ว่ารายได้ทางไหนคุ้มแรงที่สุด {('เพราะเจ้าเรือนปีไปอยู่เรือน 2/8 โดยตรง เรื่องเงินจึงเป็นหนึ่งในธีมที่เด่นจริง' if ruler_house in (2,8) else 'เงินไม่ได้เป็นธีมหลักที่สุดของปี แต่มีโอกาสเข้ามาเป็นเงื่อนไขของการตัดสินใจเรื่องอื่น')}. อย่าเพิ่งนับเงินที่ยังไม่เข้าบัญชี และอย่ารับภาระแทนใครโดยไม่ตกลงให้ชัด"},
      {"title":"ความรัก คู่ครอง และหุ้นส่วน","text":f"เรือน 7 คือคู่ครอง หุ้นส่วน ลูกค้า และข้อตกลง ส่วนเรือน 5 คือความรักแบบโรแมนติก. อ่านสองเรือนนี้ร่วมกับเรือนปี {house_num} และตำแหน่ง {PLANET_TH[ruler]} ในเรือน {ruler_house}. ถ้าความสัมพันธ์จริงจังขึ้น ภาพที่จับต้องได้อาจเป็นการคุยเรื่องเงิน เวลา หน้าที่ หรืออนาคตที่ต้องรับผิดชอบร่วมกัน. ถ้ายังโสด ให้มองเป็นช่วงที่รูปแบบการเลือกคนและขอบเขตความสัมพันธ์ถูกทบทวน ไม่ใช่รับประกันว่าจะมีคู่."},
      {"title":"บ้าน ครอบครัว และชีวิตส่วนตัว","text":f"เรือน 4 หมายถึงบ้าน ครอบครัว และฐานชีวิต. ถ้าเจ้าเรือน 4 เชื่อมกับ Lord of the Year หรือเรือน {ruler_house} เรื่องบ้านอาจเข้ามาเป็นส่วนหนึ่งของการตัดสินใจปีนี้ เช่น วางแผนย้ายบ้าน ซ่อมแซม จัดการทรัพย์สิน หรือแบ่งหน้าที่ดูแลคนในครอบครัว. ต้องตรวจมุมและเจ้าเรือน 4 ก่อนระบุว่าประเด็นใดเด่นจริง."},
      {"title":"สุขภาพ กิจวัตร และพลังงาน","text":f"เรือน 6 ใช้อ่านงานประจำ ภาระ และกิจวัตร ส่วนเรือน 1 ใช้อ่านร่างกายและพลังชีวิต. ถ้าเรือนเหล่านี้เชื่อมกับดาวเจ้าเรือนปี อาจสะท้อนว่าภาระในปีนี้กระทบตารางพักผ่อนหรือการจัดชีวิตประจำวันอย่างไร. นี่เป็นการอ่านเชิงสัญลักษณ์ ไม่ใช่การวินิจฉัยโรค และไม่ใช้แทนคำแนะนำแพทย์."},
      {"title":"มุมสัมพันธ์ของ Lord of the Year","text":("มุมที่พบ: "+"; ".join(f"{x['planet_th']} {x['aspect_th']} orb {x['orb']}°" for x in natal_aspects)) if natal_aspects else "ไม่พบมุมหลักภายใน orb 6° ระหว่าง Lord of the Year กับดาวกำเนิดดวงอื่น จึงไม่ควรแต่งมุมสัมพันธ์เพิ่ม."},
      {"title":"วิธีใช้ปีนี้ให้คุ้ม","text":f"ให้เริ่มจากจัดการเรื่อง{house_topic} แล้วดูว่ามันพาไปแตะเรื่อง{ruler_house_topic}ตรงไหน. ตัวอย่างเช่น ก่อนตกลงเรื่องสำคัญ ให้คุยหน้าที่ เงิน เวลา และเงื่อนไขให้ชัด เก็บหลักฐาน และเผื่อเวลาสำหรับสิ่งที่ต้องค่อย ๆ สร้าง. จุดแข็งของราศี{rd['sign_th']}คือ{SIGN_STYLE[rd['sign']]}."}
    ]
    for section in sections:
      section["text"] = addressed(req.name, section["text"])
    return {"client_name":req.name,"year":req.annual_year,"age":age,"profection_house":house_num,"house_th":HOUSE_TH[house_num-1],"sign":SIGNS[sign_idx],"sign_th":sign_th,"sign_glyph":SIGN_GLYPH[sign_idx],"lord_of_year":ruler,"lord_position":rd,"ascendant":n["angles"],"natal_planets":n["planets"],"annual_period":{"start":f"{req.annual_year}-{req.date[5:]}","end":f"{req.annual_year+1}-{req.date[5:]}"},"reading":{"sect":sect["name"],"benefic_of_sect":sect["benefic"],"malefic_of_sect":sect["malefic"],"dignity":dign,"dignity_note":dignote,"aspects":natal_aspects,"sections":sections}}
  except Exception as e: raise HTTPException(400,f"คำนวณ Annual Profection ไม่สำเร็จ: {e}")

@app.post("/api/transit")
def transit(req:TransitRequest):
  try:
    n=get_natal(req); jd=jd_for(req.transit_date,"12:00",req.tz); trans=planet_positions(jd); asc_idx=n["angles"]["asc_sign_index"]; sect=sect_data(n)
    for p in trans.values():
      p["house"]=house_of(p["longitude"],asc_idx); p["house_th"]=HOUSE_TH[p["house"]-1]
    raw=aspect_list(trans,n["planet_map"],5)
    tomorrow=planet_positions(jd+1)
    for a in raw:
      t=a["transit"]; nname=a["natal"]; d1=wrapdiff(tomorrow[t]["longitude"],n["planet_map"][nname]["longitude"]); orb1=abs(d1-a["angle"])
      a["motion"]="Applying" if orb1<a["orb"] else "Separating" if orb1>a["orb"] else "Near exact"
      a["motion_th"]={"Applying":"กำลังเข้าใกล้มุมสนิท","Separating":"กำลังแยกออกจากมุมสนิท","Near exact":"อยู่ใกล้มุมสนิท"}[a["motion"]]
      a["house"]=house_of(n["planet_map"][nname]["longitude"],asc_idx)
      a["intensity"]=event_intensity(a["orb"],t,a["aspect"])
      a["story"]=event_story(t,nname,a["aspect"],a["house"],a["orb"],a["motion"],sect)
    linked=natal_event_links(n,raw)
    major=[x for x in linked if x["planet"] in SLOW_PLANETS]
    major.sort(key=lambda x:(x["orb"],SLOW_PLANETS.index(x["planet"])))
    ingress=find_ingresses_and_stations(req.transit_date,req.months,req.tz)
    long_stories=transit_house_stories(trans,asc_idx)
    # Overall synthesis from the strongest slow-planet contacts.
    top=major[:5]
    if top:
      overview=(f"{req.name.strip()} ช่วงนี้ไม่ใช่เรื่องเดียวโดด ๆ แต่มีประเด็นที่โยงกันอยู่: " if req.name.strip() else "ช่วงนี้ไม่ใช่เรื่องเดียวโดด ๆ แต่มีประเด็นที่โยงกันอยู่: ")+" ".join(x["story"] for x in top[:3])+" ให้จับตาเรื่องเหล่านี้เป็นพิเศษ โดยเฉพาะมุมที่ใกล้สนิทที่สุด เพราะเป็นจุดที่แรงกดหรือแรงส่งชัดกว่าเรื่องอื่น"
    else:
      overview=((req.name.strip()+" ในวันที่เลือก ") if req.name.strip() else "ในวันที่เลือก ")+"ยังไม่พบมุมสนิทจากดาวใหญ่ต่อดาวกำเนิดภายใน orb ที่กำหนด จึงให้น้ำหนักกับธีมเรือนที่ดาวใหญ่กำลังเดินผ่านและเหตุการณ์ย้ายราศีในช่วงถัดไป แทนการสร้างคำทำนายเฉพาะเหตุการณ์ขึ้นมาเอง."
    return {"client_name":req.name,"date":req.transit_date,"transits":list(trans.values()),"aspects":raw[:80],"events":linked[:40],"major_events":major[:20],"overview":overview,"long_term_themes":long_stories,"timeline":ingress,"natal_angles":n["angles"],"natal_planets":n["planet_map"],"sect":sect,"months_scanned":req.months,"engine_note":"ตำแหน่งดาวคำนวณเวลา 12:00 ตามเวลาท้องถิ่น; applying/separating ประเมินจากการเคลื่อนที่วันถัดไป; วันย้ายราศีและ station ค้นด้วย Swiss Ephemeris Moshier โดยสแกนรายวันและหาจุดเปลี่ยนด้วย bisection."}
  except Exception as e: raise HTTPException(400,f"คำนวณ Transit ไม่สำเร็จ: {e}")

@app.post("/api/ask")
def ask(payload:dict):
  try:
    b=Birth(**payload["birth"]); client_name=(b.name or "").strip(); question=str(payload.get("question","")).strip()
    if not question: raise ValueError("กรุณาพิมพ์คำถาม")
    n=get_natal(b); s=detailed_natal_reading(n,client_name); q=question.lower()
    if any(x in q for x in ["งาน","อาชีพ","ธุรกิจ","career","work"]): houses=[6,10,11]; focus="การงานและอาชีพ"
    elif any(x in q for x in ["เงิน","การเงิน","รายได้","ทรัพย์","finance","money"]): houses=[2,8,11]; focus="การเงินและทรัพยากร"
    elif any(x in q for x in ["รัก","คู่","แฟน","ความสัมพันธ์","relationship","love"]): houses=[5,7,8]; focus="ความรักและความสัมพันธ์"
    else: houses=list(range(1,13)); focus="ภาพรวมชีวิต"
    name_prefix=(client_name+" ") if client_name else ""
    chosen=[x for x in s["sections"] if any(k in x["title"] for k in ({"การงานและอาชีพ":["งาน อาชีพ"],"การเงินและทรัพยากร":["การเงิน","เงินเก็บ"],"ความรักและความสัมพันธ์":["ความรัก","คู่ครอง"]}.get(focus,[])))]
    if not chosen: chosen=s["sections"][:5]
    linked=[]
    for h in houses:
      r=s["house_rulers"][h]
      linked.append(f"เรื่อง{HOUSE_TOPICS[h]}ไปเชื่อมกับ{HOUSE_TOPICS[r['ruler_house']]} ผ่านดาว{r['ruler_th']}ที่ไปอยู่เรือน {r['ruler_house']}")
    answer=(f"{name_prefix}ถ้าถามเรื่อง{focus} ฉันจะสรุปให้ตรง ๆ แบบนี้นะ\n\n"+"\n\n".join(x["text"] for x in chosen)+"\n\n"+" อีกจุดที่ทำให้เรื่องนี้ไม่แยกขาดจากชีวิตด้านอื่นคือ "+"; ".join(linked)+". นี่คือภาพพื้นดวงว่ามีแนวโน้มและจุดแข็งจุดอ่อนแบบไหน ถ้าต้องการฟันธงเป็นช่วงเดือนหรือวัน ต้องระบุช่วงเวลาที่สนใจแล้วซ้อน Transit กับ Annual Profection อีกชั้น ไม่ควรเดาวันจากพื้นดวงอย่างเดียว")
    return {"client_name":client_name,"question":question,"answer":answer,"facts":{"natal":s,"relevant_houses":houses}}
  except Exception as e: raise HTTPException(400,f"ประมวลผลคำถามไม่สำเร็จ: {e}")

app.mount("/static",StaticFiles(directory=ROOT),name="static")
