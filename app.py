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

def natal_summary(n):
    a=n["angles"]; pm=n["planet_map"]; sect=sect_data(n)
    asc_ruler=TRAD_RULER[a["asc_sign_index"]]; rd=pm[asc_ruler]
    dignote=dignity_of(asc_ruler,rd["sign"])
    return {"ascendant":a,"asc_ruler":asc_ruler,"ruler_position":rd,"sect":sect,"ruler_dignity":dignote,
      "story":f"ลัคนา{a['asc_sign_th']} ทำให้ดาวเจ้าเรือนลัคนาคือ{PLANET_TH[asc_ruler]} ({asc_ruler}) เป็นตัวตั้งต้นในการอ่านชีวิต ดาวดวงนี้ไปอยู่เรือน{rd['house']} ({HOUSE_TH[rd['house']-1]}) ในราศี{rd['sign_th']} ดังนั้นเรื่องตัวตนและการตัดสินใจมักพัวพันกับ{HOUSE_TOPICS[rd['house']]}. นี่เป็นจุดเชื่อมหลักที่ต้องอ่านร่วมกับดาวอื่น ไม่ใช่คำตัดสินบุคลิกจากลัคนาเพียงอย่างเดียว."}

# Narrative synthesis rules: a transit is interpreted through planet + natal house + natal planet/aspect + linked house rulers.
def transit_orb(planet, aspect):
    if planet in ("Jupiter","Saturn"): return 2.0 if aspect in ("Conjunction","Opposition","Square") else 1.5
    if planet in ("Uranus","Neptune","Pluto"): return 2.0
    if planet=="Mars": return 1.0
    return 0.8

def event_story(tname,nname,aspect,house,orb,motion,sect):
    pmeaning=PLANET_MEANING[tname]; nmeaning=PLANET_MEANING[nname]
    topic=HOUSE_TOPICS[house]
    aspect_tone={"Conjunction":"เรื่องนี้ถูกดึงขึ้นมาอยู่ตรงหน้า ต้องรับมือหรือเริ่มต้นบางอย่าง","Sextile":"มีช่องทางหรือคนช่วย แต่ต้องเป็นฝ่ายหยิบโอกาสและลงมือ","Trine":"เรื่องมีแนวโน้มไหลลื่นขึ้น ได้แรงสนับสนุนหรือเห็นทางออกง่ายขึ้น","Square":"มีแรงกดดันให้แก้ปัญหา จัดลำดับความสำคัญ หรือเปลี่ยนวิธีเดิม","Opposition":"ต้องหาจุดสมดุลระหว่างสองฝ่ายหรือสองความต้องการที่ดึงกันคนละทาง"}[aspect]
    timing="กำลังเข้าใกล้จุดพีก" if motion=="Applying" else "ผ่านจุดพีกแล้ว แต่ผลยังค่อย ๆ คลี่คลาย" if motion=="Separating" else "อยู่ใกล้จุดพีก"
    examples={
      "Jupiter":"ตัวอย่างเช่น มีคนแนะนำโอกาสใหม่ ได้เรียนรู้สิ่งที่ต่อยอดงาน หรือมีช่องทางที่ทำให้เรื่องนี้ขยายตัว แต่ควรดูต้นทุนและความคาดหวังให้สมจริง",
      "Saturn":"ตัวอย่างเช่น ต้องรับผิดชอบงานหรือข้อตกลงมากขึ้น ต้องวางแผนระยะยาว หรือพบว่าบางอย่างต้องใช้เวลาและวินัยกว่าจะเห็นผล",
      "Uranus":"ตัวอย่างเช่น ตารางหรือแผนเดิมเปลี่ยนกะทันหัน มีข้อเสนอที่ไม่คาดคิด หรือเริ่มอยากหลุดจากวิธีเดิม ๆ ควรเผื่อแผนสำรอง",
      "Neptune":"ตัวอย่างเช่น เรื่องที่เคยคิดว่าชัดอาจยังมีข้อมูลไม่ครบ หรือมีความคาดหวังสูงกว่าความจริง ควรถามให้ชัดและตรวจรายละเอียดก่อนตกลง",
      "Pluto":"ตัวอย่างเช่น ประเด็นเรื่องอำนาจ การควบคุม หรือความไว้ใจที่เคยเลี่ยงอาจต้องคุยกันจริงจัง เป็นช่วงปรับโครงสร้างมากกว่าการแก้ผิวเผิน",
      "Mars":"ตัวอย่างเช่น มีเรื่องเร่งให้ตัดสินใจ แข่งขัน หรือเผชิญหน้ากับปัญหาที่ค้างอยู่ ควรระวังการตอบโต้เร็วเกินไป",
      "Venus":"ตัวอย่างเช่น มีการเจรจาเรื่องความสัมพันธ์ เงิน หรือความพึงพอใจ อาจเป็นจังหวะปรับความเข้าใจหรือทบทวนสิ่งที่ให้คุณค่า",
      "Mercury":"ตัวอย่างเช่น มีข่าว เอกสาร นัดหมาย การพูดคุย หรือการตัดสินใจที่ต้องใช้ข้อมูล ควรตรวจวันเวลาและรายละเอียดให้ครบ",
      "Sun":"ตัวอย่างเช่น เรื่องนี้กลายเป็นจุดสนใจ ต้องแสดงจุดยืน รับผิดชอบ หรือได้รับการมองเห็นมากขึ้น",
      "Moon":"ตัวอย่างเช่น อารมณ์ ความต้องการเรื่องความมั่นคง หรือเรื่องบ้านและครอบครัวทำให้ต้องปรับแผนในช่วงนั้น"
    }[tname]
    return (f"ดาวจร{PLANET_TH[tname]} ({tname}) ซึ่งแทนเรื่อง{pmeaning} กำลังทำมุม{dict((x[1],x[2]) for x in ASPECTS)[aspect]}กับดาวกำเนิด{PLANET_TH[nname]} ({nname}) ที่แทนเรื่อง{nmeaning}. จุดนี้ไปกระตุ้นเรือนที่ {house} ซึ่งเกี่ยวกับ{topic}. {aspect_tone} {examples} ตอนนี้{timing} (orb {orb:.2f}°) จึงควรจับตาประเด็นนี้เป็นพิเศษ แต่ไม่ได้หมายความว่าเหตุการณ์จะเกิดแบบเดียวกันกับทุกคน ต้องดูบริบทชีวิตจริงประกอบ")

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

def detailed_natal_reading(n):
    pm=n["planet_map"]; a=n["angles"]; sect=sect_data(n); lots=lot_positions(n); rulers=house_ruler_map(n)
    asc_ruler=TRAD_RULER[a["asc_sign_index"]]; asc=pm[asc_ruler]
    moon=pm["Moon"]; sun=pm["Sun"]
    sections=[]
    def add(title,text): sections.append({"title":title,"text":text})
    asc_dig=dignity_of(asc_ruler,asc["sign"])
    add("01 · ตัวตนและบุคลิกที่คนอื่นเห็น",f"ลัคนา{a['asc_sign_th']} เป็นวิธีที่คุณเข้าหาโลกและรับมือสถานการณ์แรก ๆ แต่แกนสำคัญกว่าคือเจ้าเรือนลัคนา {PLANET_TH[asc_ruler]} อยู่ราศี{asc['sign_th']} เรือน {asc['house']} ({HOUSE_TH[asc['house']-1]}). นี่ทำให้เรื่อง {HOUSE_TOPICS[asc['house']]} เป็นสนามที่ตัวตนของคุณต้องเข้าไปเรียนรู้และตัดสินใจบ่อย คุณภาพดาวอยู่ในสถานะ {asc_dig[0]}: {asc_dig[1]}. เมื่อนำไปอ่านร่วมกับ {sect['name']} และมุมสัมพันธ์ของดาวดวงนี้ จะเห็นว่าคุณไม่ได้มีแค่บุคลิกแบบลัคนา แต่มีแรงขับจากเรื่องเรือน {asc['house']} อยู่เบื้องหลังด้วย")
    add("02 · โลกภายใน ความรู้สึก และวิธีชาร์จพลัง",f"ดวงจันทร์อยู่ราศี{moon['sign_th']} ซึ่งเป็นธาตุ{ {'Aries':'ไฟ','Leo':'ไฟ','Sagittarius':'ไฟ','Taurus':'ดิน','Virgo':'ดิน','Capricorn':'ดิน','Gemini':'ลม','Libra':'ลม','Aquarius':'ลม','Cancer':'น้ำ','Scorpio':'น้ำ','Pisces':'น้ำ'}[moon['sign']] } และเรือน {moon['house']} ({HOUSE_TH[moon['house']-1]}). อารมณ์จึงผูกกับเรื่อง{HOUSE_TOPICS[moon['house']]}เป็นพิเศษ วิธีเติมพลังที่เข้ากับธาตุนี้คือ { {'ไฟ':'การเคลื่อนไหว ออกกำลัง เต้น หรือทำกิจกรรมที่ได้ปลดปล่อยแรงค้าง','ดิน':'ธรรมชาติ สัมผัสสิ่งของจริง จัดพื้นที่ให้เป็นระเบียบ และกิจวัตรที่มั่นคง','ลม':'อ่านหนังสือ เขียน พูดคุย แลกเปลี่ยนไอเดีย และเรียนสิ่งใหม่','น้ำ':'อยู่ใกล้น้ำ ฟังเพลง เขียนบันทึกอารมณ์ และมีพื้นที่ปลอดภัยให้รู้สึก'}[{'Aries':'ไฟ','Leo':'ไฟ','Sagittarius':'ไฟ','Taurus':'ดิน','Virgo':'ดิน','Capricorn':'ดิน','Gemini':'ลม','Libra':'ลม','Aquarius':'ลม','Cancer':'น้ำ','Scorpio':'น้ำ','Pisces':'น้ำ'}[moon['sign']]] }. อย่าฝืนชาร์จพลังด้วยวิธีที่ไม่ตรงกับความต้องการของตัวเอง")
    add("03 · ความคิด การสื่อสาร และการตัดสินใจ",f"ดาวพุธอยู่ราศี{pm['Mercury']['sign_th']} เรือน {pm['Mercury']['house']} จึงใช้ความคิดกับเรื่อง{HOUSE_TOPICS[pm['Mercury']['house']]}. เวลาตัดสินใจให้ดูทั้งข้อมูลและแรงกดดันจากเรือนนี้ จุดแข็งคือมีช่องทางเรียนรู้และสื่อสารผ่านเรื่องดังกล่าว ส่วนจุดที่ต้องระวังคือการคิดวนหรือรับข้อมูลมากเกินไปเมื่อเรื่องนั้นยังไม่ชัด")
    add("04 · ความรัก วิธีรัก และแรงดึงดูด",f"ดาวศุกร์อยู่ราศี{pm['Venus']['sign_th']} เรือน {pm['Venus']['house']} สะท้อนสิ่งที่ทำให้รู้สึกได้รับความรักและวิธีสร้างความกลมกลืน ส่วนดาวอังคารอยู่ราศี{pm['Mars']['sign_th']} เรือน {pm['Mars']['house']} สะท้อนแรงปรารถนา วิธีเข้าหา และการตอบสนองเมื่อไม่พอใจ เรือน 5 อยู่ราศี{rulers[5]['sign_th']} เจ้าเรือนคือ{PLANET_TH[rulers[5]['ruler']]} ไปอยู่เรือน {rulers[5]['ruler_house']} ขณะที่เรือน 7 อยู่ราศี{rulers[7]['sign_th']} เจ้าเรือนคู่ครองคือ{PLANET_TH[rulers[7]['ruler']]} ไปอยู่เรือน {rulers[7]['ruler_house']} ({HOUSE_TH[rulers[7]['ruler_house']-1]}). จึงควรแยกความตื่นเต้นแบบเรือน 5 ออกจากความพร้อมสร้างพันธะระยะยาวแบบเรือน 7 ไม่ควรใช้ Venus เพียงดวงเดียวตัดสินคู่ชีวิต")
    add("05 · คู่ครองและบริบทที่อาจพบกัน",f"ลักษณะคู่ที่ดึงดูดอ่านจากราศีเรือน 7 และเจ้าเรือน 7 ไม่ใช่คำบรรยายรูปลักษณ์ตายตัว เจ้าเรือน 7 {PLANET_TH[rulers[7]['ruler']]} อยู่เรือน {rulers[7]['ruler_house']} จึงชี้บริบทที่ความสัมพันธ์อาจเชื่อมโยงกับ{HOUSE_TOPICS[rulers[7]['ruler_house']]}. ตัวอย่างเช่น หากเรือนนี้เกี่ยวกับงาน อาจรู้จักผ่านหน้าที่ ลูกค้า หรือเครือข่ายงาน; หากเกี่ยวกับการเรียนหรือเดินทาง อาจพบผ่านคอร์ส การเดินทาง หรือคนต่างถิ่น ต้องดูดาวร่วมและบริบทจริงก่อนระบุสถานที่เฉพาะ")
    add("06 · การเงิน: หาเงินจากอะไรและเหนื่อยแค่ไหน",f"เรือน 2 อยู่ราศี{rulers[2]['sign_th']} เจ้าเรือนการเงินคือ{PLANET_TH[rulers[2]['ruler']]} ไปอยู่เรือน {rulers[2]['ruler_house']} ({HOUSE_TH[rulers[2]['ruler_house']-1]}) และมีศักดิ์ {rulers[2]['dignity']}. นี่คือช่องทางหลักที่รายได้และความสามารถในการสร้างทรัพย์เชื่อมไปหาเรื่อง{HOUSE_TOPICS[rulers[2]['ruler_house']]}. เรือน 10 อยู่ราศี{rulers[10]['sign_th']} เจ้าเรือนอาชีพคือ{PLANET_TH[rulers[10]['ruler']]} ไปอยู่เรือน {rulers[10]['ruler_house']} จึงต้องตรวจว่ากลไกอาชีพส่งแรงหนุนหรือเพิ่มภาระให้การเงินอย่างไร")
    add("07 · เงินเก็บ หนี้ และจุดเงินรั่ว",f"การหาเงินไม่เท่ากับการเก็บเงิน เรือน 8 อยู่ราศี{rulers[8]['sign_th']} เจ้าเรือนคือ{PLANET_TH[rulers[8]['ruler']]} อยู่เรือน {rulers[8]['ruler_house']} ส่วนเรือน 12 อยู่ราศี{rulers[12]['sign_th']} เจ้าเรือนคือ{PLANET_TH[rulers[12]['ruler']]} อยู่เรือน {rulers[12]['ruler_house']}. ใช้สองตำแหน่งนี้ตรวจเรื่องเงินร่วม ภาระ หนี้ ภาษี ค่าใช้จ่ายแฝง และการช่วยเหลือคนอื่น หากเจ้าเรือน 2 เชื่อมกับเจ้าเรือน 8 หรือ 12 ผ่านมุมดาว จะเป็นเหตุผลให้เน้นระบบบัญชี เงินสำรอง และข้อตกลงที่ชัด ไม่ใช่สรุปว่าเป็นหนี้หรือเงินรั่วแน่นอน")
    f=lots['fortune']; sp=lots['spirit']
    add("08 · Lot of Fortune และ Lot of Spirit",f"Lot of Fortune อยู่ราศี{f['sign_th']} เรือน {f['house']} ({HOUSE_TH[f['house']-1]}) เจ้าเรือนคือ{PLANET_TH[f['ruler']]} ไปอยู่เรือน {f['ruler_position']['house']} และมีศักดิ์ {f['ruler_dignity']}. จุดนี้ใช้ดูเงื่อนไขทางกายภาพ โอกาส ทรัพยากร และสิ่งที่เข้ามาโดยไม่ต้องควบคุมทั้งหมด ส่วน Lot of Spirit อยู่ราศี{sp['sign_th']} เรือน {sp['house']} เจ้าเรือนคือ{PLANET_TH[sp['ruler']]} ไปอยู่เรือน {sp['ruler_position']['house']} ใช้อ่านเจตจำนง การเลือก และทิศทางที่เจ้าชะตาลงมือสร้างด้วยตัวเอง")
    add("09 · งาน อาชีพ และรูปแบบการทำงานประจำวัน",f"เรือน 10 และ MC เป็นคนละข้อมูล: Whole Sign เรือน 10 ใช้อ่านอาชีพและสถานะ ส่วน MC เป็นองศาจริงที่อาจตกเรือนใดก็ได้ MC อยู่ที่ {a['mc']:.2f}° ราศี{SIGN_TH[sign_index(a['mc'])]}. เจ้าเรือน 10 คือ{PLANET_TH[rulers[10]['ruler']]} อยู่เรือน {rulers[10]['ruler_house']}; Mercury อยู่เรือน {pm['Mercury']['house']}, Venus เรือน {pm['Venus']['house']}, Mars เรือน {pm['Mars']['house']} เป็นเครื่องมือด้านคิด-สื่อสาร มนุษยสัมพันธ์ และลงมือแก้ปัญหา ส่วนเรือน 6 อยู่ราศี{rulers[6]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[6]['ruler_house']} จึงบอกสภาพงานประจำวันและความเหน็ดเหนื่อยที่ต้องจัดการ")
    add("10 · บ้าน ครอบครัว พี่น้อง และการศึกษา",f"เรือน 4 อยู่ราศี{rulers[4]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[4]['ruler_house']} ใช้อ่านบ้าน รากฐาน และพื้นที่ส่วนตัว; เรือน 3 อยู่ราศี{rulers[3]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[3]['ruler_house']} ใช้อ่านพี่น้อง การสื่อสาร และการเรียนรู้ใกล้ตัว; เรือน 9 อยู่ราศี{rulers[9]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[9]['ruler_house']} ใช้อ่านการศึกษาสูง ต่างประเทศ และโลกทัศน์ การอ่านต้องพิจารณาดาวที่อยู่ในเรือนเหล่านี้ด้วย")
    add("11 · บุตร ความสร้างสรรค์ เพื่อน และเครือข่าย",f"เรือน 5 อยู่ราศี{rulers[5]['sign_th']} และเจ้าเรือนอยู่เรือน {rulers[5]['ruler_house']} ใช้อ่านความสุข งานสร้างสรรค์ ความรักแบบโรแมนติก และบุตร ส่วนเรือน 11 อยู่ราศี{rulers[11]['sign_th']} เจ้าเรือนอยู่เรือน {rulers[11]['ruler_house']} ใช้อ่านเพื่อน กลุ่มคน ผู้สนับสนุน และผลตอบแทนจากอาชีพ ควรดูดาวในเรือนและมุมสัมพันธ์ก่อนให้คำตอบเฉพาะเรื่องจำนวนบุตรหรือผลสำเร็จ")
    add("12 · สุขภาพ พลังงาน และข้อควรระวัง",f"ในเชิงโหราศาสตร์ให้ตรวจเรือน 1, 6, 8 และ 12 รวมถึงเจ้าเรือนและดาวที่สัมพันธ์กัน: เรือน 1 เจ้าเรือนอยู่เรือน {rulers[1]['ruler_house']}, เรือน 6 เจ้าเรือนอยู่เรือน {rulers[6]['ruler_house']}, เรือน 12 เจ้าเรือนอยู่เรือน {rulers[12]['ruler_house']}. อ่านเป็นแนวโน้มเรื่องการดูแลตัวเอง ความเครียด และกิจวัตร ไม่ใช่การวินิจฉัยโรคหรือระบุอายุที่จะป่วย หากมีอาการจริงให้ใช้การตรวจทางการแพทย์")
    add("13 · จุดแข็ง จุดท้าทาย และการปรับใช้",f"จุดแข็งควรดูดาวที่มี Essential Dignity, อยู่ใน Sect ที่เหมาะ และได้รับมุมสนับสนุน; จุดท้าทายดูดาวที่เสียศักดิ์ ถูกกดด้วยมุมตึง หรือทำหน้าที่เป็นเจ้าเรือนสำคัญโดยมีเงื่อนไขมาก การแก้เกมคือเปลี่ยนคำอ่านให้เป็นการกระทำ: วางระบบเงินเมื่อเรือน 2/8/12 เชื่อมกัน, ทำขอบเขตความสัมพันธ์เมื่อเรือน 7 ถูกกด, และจัดตารางพักเมื่อเรือน 6/12 เด่น")
    return {"ascendant":a,"asc_ruler":asc_ruler,"ruler_position":asc,"sect":sect,"ruler_dignity":asc_dig,"story":sections[0]["text"],"sections":sections,"house_rulers":rulers,"lots":lots,"moon_self_care":{"sign":moon['sign'],"sign_th":moon['sign_th'],"house":moon['house'],"house_th":moon['house_th']},"prenatal_syzygy":prenatal_syzygy(n),"planet_details":planet_detail_table(n)}

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
    n=get_natal(b); s=detailed_natal_reading(n)
    return {"birth":b.model_dump(),"chart":n,"interpretation":s,"engine_note":"Swiss Ephemeris / Moshier; Tropical Zodiac; Whole Sign Houses; traditional rulers; sect from actual solar altitude."}
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
      {"title":"การงานและทิศทางอาชีพ","text":f"เวลาอ่านงาน เราต้องดูเรือน 10 (อาชีพและสถานะ) ร่วมกับเรือนปี {house_num} และดาวเจ้าเรือนปี {ruler}. ถ้าเรื่องงานปีนี้พัวพันกับ{ruler_house_topic} ตัวอย่างเช่น งานที่ต้องทำสัญญา ประสานเงิน หรือรับผิดชอบเรื่องของคนอื่น ก็อาจกลายเป็นจุดที่ต้องตัดสินใจมากกว่าการเปลี่ยนตำแหน่งอย่างเดียว. ให้ดูดาวเจ้าเรือน 10 และมุมที่ทำกับ {ruler} เพิ่มก่อนสรุปว่าจะเป็นการเลื่อนตำแหน่ง เปลี่ยนงาน หรือเพิ่มภาระ."},
      {"title":"การเงินและทรัพยากรร่วม","text":f"แยกเงินตัวเองในเรือน 2 ออกจากเงินร่วม หนี้ ภาษี และภาระของอีกฝ่ายในเรือน 8 ก่อน. จุดเชื่อมของปีคือ {PLANET_TH[ruler]} เจ้าเรือนปีไปอยู่เรือน {ruler_house} ({HOUSE_TH[ruler_house-1]}). ถ้าเรือนนี้เกี่ยวข้องกับเรือน 2 หรือ 8 ผ่านเจ้าเรือนหรือมุมดาว เรื่องที่เห็นเป็นรูปธรรมอาจเป็นการจัดงบ แบ่งค่าใช้จ่าย ปรับหนี้ ตรวจสัญญา หรือคุยเรื่องทรัพย์สินร่วม ไม่ควรตีความว่าได้เงินก้อนหรือเสียเงินก้อนโดยไม่มีสัญญาณยืนยัน."},
      {"title":"ความรัก คู่ครอง และหุ้นส่วน","text":f"เรือน 7 คือคู่ครอง หุ้นส่วน ลูกค้า และข้อตกลง ส่วนเรือน 5 คือความรักแบบโรแมนติก. อ่านสองเรือนนี้ร่วมกับเรือนปี {house_num} และตำแหน่ง {PLANET_TH[ruler]} ในเรือน {ruler_house}. ถ้าความสัมพันธ์จริงจังขึ้น ภาพที่จับต้องได้อาจเป็นการคุยเรื่องเงิน เวลา หน้าที่ หรืออนาคตที่ต้องรับผิดชอบร่วมกัน. ถ้ายังโสด ให้มองเป็นช่วงที่รูปแบบการเลือกคนและขอบเขตความสัมพันธ์ถูกทบทวน ไม่ใช่รับประกันว่าจะมีคู่."},
      {"title":"บ้าน ครอบครัว และชีวิตส่วนตัว","text":f"เรือน 4 หมายถึงบ้าน ครอบครัว และฐานชีวิต. ถ้าเจ้าเรือน 4 เชื่อมกับ Lord of the Year หรือเรือน {ruler_house} เรื่องบ้านอาจเข้ามาเป็นส่วนหนึ่งของการตัดสินใจปีนี้ เช่น วางแผนย้ายบ้าน ซ่อมแซม จัดการทรัพย์สิน หรือแบ่งหน้าที่ดูแลคนในครอบครัว. ต้องตรวจมุมและเจ้าเรือน 4 ก่อนระบุว่าประเด็นใดเด่นจริง."},
      {"title":"สุขภาพ กิจวัตร และพลังงาน","text":f"เรือน 6 ใช้อ่านงานประจำ ภาระ และกิจวัตร ส่วนเรือน 1 ใช้อ่านร่างกายและพลังชีวิต. ถ้าเรือนเหล่านี้เชื่อมกับดาวเจ้าเรือนปี อาจสะท้อนว่าภาระในปีนี้กระทบตารางพักผ่อนหรือการจัดชีวิตประจำวันอย่างไร. นี่เป็นการอ่านเชิงสัญลักษณ์ ไม่ใช่การวินิจฉัยโรค และไม่ใช้แทนคำแนะนำแพทย์."},
      {"title":"มุมสัมพันธ์ของ Lord of the Year","text":("มุมที่พบ: "+"; ".join(f"{x['planet_th']} {x['aspect_th']} orb {x['orb']}°" for x in natal_aspects)) if natal_aspects else "ไม่พบมุมหลักภายใน orb 6° ระหว่าง Lord of the Year กับดาวกำเนิดดวงอื่น จึงไม่ควรแต่งมุมสัมพันธ์เพิ่ม."},
      {"title":"วิธีใช้ปีนี้ให้คุ้ม","text":f"ให้เริ่มจากจัดการเรื่อง{house_topic} แล้วดูว่ามันพาไปแตะเรื่อง{ruler_house_topic}ตรงไหน. ตัวอย่างเช่น ก่อนตกลงเรื่องสำคัญ ให้คุยหน้าที่ เงิน เวลา และเงื่อนไขให้ชัด เก็บหลักฐาน และเผื่อเวลาสำหรับสิ่งที่ต้องค่อย ๆ สร้าง. จุดแข็งของราศี{rd['sign_th']}คือ{SIGN_STYLE[rd['sign']]}."}
    ]
    return {"year":req.annual_year,"age":age,"profection_house":house_num,"house_th":HOUSE_TH[house_num-1],"sign":SIGNS[sign_idx],"sign_th":sign_th,"sign_glyph":SIGN_GLYPH[sign_idx],"lord_of_year":ruler,"lord_position":rd,"ascendant":n["angles"],"natal_planets":n["planets"],"annual_period":{"start":f"{req.annual_year}-{req.date[5:]}","end":f"{req.annual_year+1}-{req.date[5:]}"},"reading":{"sect":sect["name"],"benefic_of_sect":sect["benefic"],"malefic_of_sect":sect["malefic"],"dignity":dign,"dignity_note":dignote,"aspects":natal_aspects,"sections":sections}}
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
      overview="ภาพใหญ่ช่วงนี้มีดาวใหญ่เข้ามากระตุ้นพื้นดวงหลายจุด: "+" ".join(f"{x['planet_th']} {x['aspect_th']} {x['natal_th']} (orb {x['orb']}°) ไปแตะเรื่องเรือน {x['natal_planet_house']} และเรื่องที่ดาวดวงนั้นเป็นเจ้าเรือน" for x in top)+". อ่านเป็นธีมที่กำลังทำงานร่วมกัน ไม่ใช่เหตุการณ์แยกขาดจากกัน."
    else:
      overview="ในวันที่เลือก ยังไม่พบมุมสนิทจากดาวใหญ่ต่อดาวกำเนิดภายใน orb ที่กำหนด จึงให้น้ำหนักกับธีมเรือนที่ดาวใหญ่กำลังเดินผ่านและเหตุการณ์ย้ายราศีในช่วงถัดไป แทนการสร้างคำทำนายเฉพาะเหตุการณ์ขึ้นมาเอง."
    return {"date":req.transit_date,"transits":list(trans.values()),"aspects":raw[:80],"events":linked[:40],"major_events":major[:20],"overview":overview,"long_term_themes":long_stories,"timeline":ingress,"natal_angles":n["angles"],"natal_planets":n["planet_map"],"sect":sect,"months_scanned":req.months,"engine_note":"ตำแหน่งดาวคำนวณเวลา 12:00 ตามเวลาท้องถิ่น; applying/separating ประเมินจากการเคลื่อนที่วันถัดไป; วันย้ายราศีและ station ค้นด้วย Swiss Ephemeris Moshier โดยสแกนรายวันและหาจุดเปลี่ยนด้วย bisection."}
  except Exception as e: raise HTTPException(400,f"คำนวณ Transit ไม่สำเร็จ: {e}")

@app.post("/api/ask")
def ask(payload:dict):
  try:
    b=Birth(**payload["birth"]); question=str(payload.get("question","")).strip()
    if not question: raise ValueError("กรุณาพิมพ์คำถาม")
    n=get_natal(b); s=natal_summary(n); q=question.lower()
    if any(x in q for x in ["งาน","อาชีพ","ธุรกิจ","career","work"]): houses=[6,10,11]; focus="การงานและอาชีพ"
    elif any(x in q for x in ["เงิน","การเงิน","รายได้","ทรัพย์","finance","money"]): houses=[2,8,11]; focus="การเงินและทรัพยากร"
    elif any(x in q for x in ["รัก","คู่","แฟน","ความสัมพันธ์","relationship","love"]): houses=[5,7,8]; focus="ความรักและความสัมพันธ์"
    else: houses=list(range(1,13)); focus="ภาพรวมชีวิต"
    relevant=[]
    for h in houses:
      si=(n["angles"]["asc_sign_index"]+h-1)%12; ruler=TRAD_RULER[si]; rp=n["planet_map"][ruler]
      relevant.append(f"เรือน {h} ({HOUSE_TH[h-1]}) อยู่ราศี{SIGN_TH[si]} มี {PLANET_TH[ruler]} เป็นเจ้าเรือน และดาวไปอยู่เรือน {rp['house']} ({HOUSE_TH[rp['house']-1]}). จึงต้องอ่านเรื่อง{HOUSE_TOPICS[h]}ควบคู่กับเรื่อง{HOUSE_TOPICS[rp['house']]}")
    answer=f"ขอเริ่มจากโครงสร้างดวงก่อนนะ หัวข้อที่ถามคือ{focus}. {s['story']}\n\nจุดที่เกี่ยวข้องในพื้นดวง:\n"+"\n".join(relevant)+"\n\nนี่คือการเชื่อมโครงสร้างพื้นดวง ยังไม่ใช่การระบุเหตุการณ์ตามวันเวลา เพราะต้องนำดาวจรของช่วงที่ถามมาซ้อนอีกชั้น ถ้าระบุช่วงเวลาได้ ระบบ Transit จะใช้หามุมดาวและช่วงเวลาที่เข้มข้นประกอบ."
    return {"question":question,"answer":answer,"facts":{"natal":s,"relevant_houses":houses}}
  except Exception as e: raise HTTPException(400,f"ประมวลผลคำถามไม่สำเร็จ: {e}")

app.mount("/static",StaticFiles(directory=ROOT),name="static")
