#!/usr/bin/env python3
"""
Advanced Astrological Position Calculator with Auto-Location & Sign Detection
Calculates personalized interpretations with automatic geocoding and natal chart analysis
"""

import swisseph as swe
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

# Zodiac signs mapping
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", 
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO
}

# Planetary rulerships
RULERSHIPS = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mercury": ["Gemini", "Virgo"],
    "Venus": ["Taurus", "Libra"],
    "Mars": ["Aries", "Scorpio"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn": ["Capricorn", "Aquarius"],
    "Uranus": ["Aquarius"],
    "Neptune": ["Pisces"],
    "Pluto": ["Scorpio"]
}

# Element groupings
ELEMENTS = {
    "Fire": ["Aries", "Leo", "Sagittarius"],
    "Earth": ["Taurus", "Virgo", "Capricorn"],
    "Air": ["Gemini", "Libra", "Aquarius"],
    "Water": ["Cancer", "Scorpio", "Pisces"]
}

# House meanings
HOUSE_MEANINGS = {
    1: {"name": "Self", "description": "identity, appearance, vitality, life force"},
    2: {"name": "Resources", "description": "money, possessions, values, self-worth"},
    3: {"name": "Communication", "description": "siblings, short trips, learning, daily communication"},
    4: {"name": "Home", "description": "family, roots, foundations, private life"},
    5: {"name": "Pleasure", "description": "creativity, romance, children, self-expression"},
    6: {"name": "Health", "description": "daily work, service, health, routines"},
    7: {"name": "Relationships", "description": "partnerships, marriage, contracts, open enemies"},
    8: {"name": "Transformation", "description": "death, rebirth, shared resources, occult, sex"},
    9: {"name": "Wisdom", "description": "philosophy, higher learning, long journeys, spirituality"},
    10: {"name": "Career", "description": "public life, reputation, career, authority"},
    11: {"name": "Community", "description": "friends, groups, hopes, dreams, social networks"},
    12: {"name": "Subconscious", "description": "secrets, hidden enemies, karma, spirituality, solitude"}
}


def geocode_location(location_name):
    """
    Convert location name to latitude/longitude using OpenStreetMap Nominatim
    """
    geolocator = Nominatim(user_agent="astro_calculator_v1")
    
    try:
        print(f"Looking up coordinates for '{location_name}'...")
        location = geolocator.geocode(location_name, timeout=10)
        
        if location:
            print(f"✓ Found: {location.address}")
            print(f"  Coordinates: {location.latitude}, {location.longitude}")
            return location.latitude, location.longitude, location.address
        else:
            print(f"✗ Could not find location: {location_name}")
            return None, None, None
            
    except GeocoderTimedOut:
        print("⚠ Geocoding timeout. Retrying...")
        time.sleep(1)
        return geocode_location(location_name)
    except GeocoderServiceError as e:
        print(f"✗ Geocoding service error: {e}")
        return None, None, None


def get_zodiac_sign(longitude):
    """Convert ecliptic longitude to zodiac sign"""
    sign_num = int(longitude / 30.0)
    return ZODIAC_SIGNS[sign_num % 12]


def get_element(sign):
    """Get the element of a zodiac sign"""
    for element, signs in ELEMENTS.items():
        if sign in signs:
            return element
    return "Unknown"


def calculate_natal_positions(year, month, day, hour, minute, second, timezone_str="UTC"):
    """
    Calculate natal Sun and Moon positions from birth data
    Returns sun_sign and moon_sign
    """
    # Convert to UTC
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime(year, month, day, hour, minute, second))
    utc_dt = local_dt.astimezone(pytz.UTC)
    
    # Calculate Julian Day
    jd = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0
    )
    
    # Calculate Sun position
    sun_result, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
    sun_sign = get_zodiac_sign(sun_result[0])
    
    # Calculate Moon position
    moon_result, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)
    moon_sign = get_zodiac_sign(moon_result[0])
    
    return sun_sign, moon_sign


def calculate_houses(year, month, day, hour, minute, second, lat, lon, timezone_str="UTC"):
    """
    Calculate house cusps using Placidus system
    Returns house data with cusps and angles
    """
    # Convert to UTC
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime(year, month, day, hour, minute, second))
    utc_dt = local_dt.astimezone(pytz.UTC)
    
    # Calculate Julian Day
    jd = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0
    )
    
    # Calculate houses using Placidus system
    # Returns: (cusps, ascmc)
    # cusps is a tuple with indices 0-12 (we use 1-12 for houses)
    # ascmc: [0]=Ascendant, [1]=MC, [2]=ARMC, [3]=Vertex
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    
    house_data = {
        "ascendant": {
            "longitude": ascmc[0],
            "sign": get_zodiac_sign(ascmc[0]),
            "degrees_in_sign": ascmc[0] % 30
        },
        "midheaven": {
            "longitude": ascmc[1],
            "sign": get_zodiac_sign(ascmc[1]),
            "degrees_in_sign": ascmc[1] % 30
        },
        "cusps": {}
    }
    
    # House cusps - pyswisseph returns 13 elements (0-12)
    # Houses 1-12 are at indices 1-12
    for i in range(1, 13):
        if i < len(cusps):
            cusp_long = cusps[i]
            house_data["cusps"][i] = {
                "longitude": cusp_long,
                "sign": get_zodiac_sign(cusp_long),
                "degrees_in_sign": cusp_long % 30
            }
        else:
            # Fallback if cusps array is shorter than expected
            house_data["cusps"][i] = {
                "longitude": 0.0,
                "sign": "Aries",
                "degrees_in_sign": 0.0
            }
    
    return house_data


def calculate_planetary_positions(year, month, day, hour, minute, second, timezone_str="UTC"):
    """
    Calculate positions of all planets for a given date/time
    Returns dict with planet data including sign and retrograde status
    """
    # Convert to UTC
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime(year, month, day, hour, minute, second))
    utc_dt = local_dt.astimezone(pytz.UTC)
    
    # Calculate Julian Day
    jd = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0
    )
    
    positions = {}
    
    # Calculate for each planet
    for planet_name, planet_id in PLANETS.items():
        result, ret_flag = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
        
        longitude = result[0]
        speed = result[3]
        
        sign = get_zodiac_sign(longitude)
        is_retrograde = speed < 0
        
        positions[planet_name] = {
            "planet": planet_name,
            "sign": sign,
            "longitude": longitude,
            "speed": speed,
            "retrograde": is_retrograde,
            "degrees_in_sign": longitude % 30
        }
    
    return positions


def find_house_for_planet(planet_longitude, house_cusps):
    """
    Determine which house a planet is in based on its longitude
    Houses are calculated counter-clockwise from Ascendant
    """
    # Normalize planet longitude to 0-360
    planet_long = planet_longitude % 360
    
    for house_num in range(1, 13):
        current_cusp = house_cusps[house_num]["longitude"] % 360
        
        # Get next house cusp (wraps around from 12 to 1)
        next_house_num = (house_num % 12) + 1
        next_cusp = house_cusps[next_house_num]["longitude"] % 360
        
        # Check if planet is between current and next cusp
        if current_cusp < next_cusp:
            # Normal case: cusps don't cross 0°
            if current_cusp <= planet_long < next_cusp:
                return house_num
        else:
            # Cusps cross 0° Aries
            if planet_long >= current_cusp or planet_long < next_cusp:
                return house_num
    
    return 1  # Default to 1st house if calculation fails


def get_retrograde_interpretation_by_element(planet, element):
    """
    Get element-specific retrograde interpretation
    """
    interpretations = {
        "Mercury": {
            "Fire": "you may feel your usual quick thinking and decisive communication slowed, causing frustration with delays in expressing your bold ideas",
            "Earth": "expect practical matters like contracts, emails, and daily organization to require extra attention - double-check everything",
            "Air": "your natural gift for communication faces obstacles; conversations may be misunderstood and social connections feel strained",
            "Water": "emotional communication becomes murkier; trust your intuition but verify facts before making decisions based on feelings"
        },
        "Mars": {
            "Fire": "your natural drive and initiative feel blocked, leading to frustration when action is required - channel energy into planning instead",
            "Earth": "motivation for work and daily tasks wanes by about 20%, making it harder to maintain your usual productivity",
            "Air": "social assertiveness decreases; you may feel less inclined to advocate for yourself in group settings",
            "Water": "emotional reactions intensify and may lead to passive-aggressive behavior rather than direct confrontation"
        },
        "Venus": {
            "Fire": "romantic passion may cool temporarily; use this time to reassess what you truly value in relationships",
            "Earth": "financial matters and material possessions require review - avoid major purchases or investments",
            "Air": "social dynamics shift; friendships and partnerships need honest reevaluation",
            "Water": "deep emotional bonds come under scrutiny; past relationship patterns resurface for healing"
        },
        "Saturn": {
            "Fire": "your ambitious drive faces tests of discipline; long-term goals require patient restructuring",
            "Earth": "career foundations and practical structures demand careful review and possible rebuilding",
            "Air": "mental frameworks and belief systems undergo serious questioning",
            "Water": "emotional boundaries and security needs require mature reevaluation"
        }
    }
    
    return interpretations.get(planet, {}).get(element, "this planetary energy turns inward for reflection")


def get_retrograde_interpretation_by_house(planet, house_num):
    """
    Get house-specific retrograde interpretation
    """
    house_interpretations = {
        "Mercury": {
            1: "affecting your self-expression and how you present yourself to the world",
            2: "impacting financial decisions and how you manage resources",
            3: "disrupting daily communication, short trips, and connections with siblings",
            4: "stirring up family matters and issues around your home and emotional foundations",
            5: "affecting creative projects, romance, and relationships with children",
            6: "creating challenges in daily work routines, health habits, and service to others",
            7: "complicating partnerships, contracts, and one-on-one relationships",
            8: "bringing up issues around shared resources, intimacy, and transformation",
            9: "affecting travel plans, higher learning, and philosophical beliefs",
            10: "impacting your career, public reputation, and relationship with authority",
            11: "disrupting friendships, group activities, and long-term goals",
            12: "bringing hidden issues to light and affecting spiritual practices"
        },
        "Mars": {
            1: "dampening your personal drive and physical vitality",
            2: "slowing efforts to earn money and build material security",
            3: "creating tension in daily interactions and local travel",
            4: "stirring conflicts at home or with family members",
            5: "reducing creative output and complicating romantic pursuits",
            6: "lowering energy for daily tasks and potentially affecting health",
            7: "bringing past relationship conflicts back for resolution",
            8: "intensifying power struggles over shared resources",
            9: "challenging beliefs and creating obstacles in long-distance matters",
            10: "creating friction with authority figures and career progress",
            11: "causing tension within friend groups and social networks",
            12: "turning anger and drive inward, requiring spiritual processing"
        },
        "Venus": {
            1: "affecting how you value yourself and your self-image",
            2: "prompting review of spending habits and material values",
            3: "bringing up unresolved issues with siblings or neighbors",
            4: "highlighting family values and what makes you feel at home",
            5: "requiring reevaluation of romantic relationships and creative projects",
            6: "affecting work relationships and daily pleasures",
            7: "bringing past partners back or requiring relationship reassessment",
            8: "reviewing shared finances and intimate bonds",
            9: "questioning your beliefs about love and relationships",
            10: "affecting professional relationships and public image",
            11: "testing friendships and social values",
            12: "bringing secret relationships or hidden values to awareness"
        },
        "Saturn": {
            1: "testing your self-discipline and personal responsibility",
            2: "requiring serious financial restructuring",
            3: "demanding more mature communication patterns",
            4: "bringing up karmic family issues for resolution",
            5: "testing creative endeavors and romantic commitments",
            6: "increasing work burdens or health restrictions",
            7: "bringing relationship commitments under serious review",
            8: "facing fears around mortality and shared resources",
            9: "questioning long-held beliefs and philosophies",
            10: "testing career foundations and professional authority",
            11: "evaluating the quality of friendships and group involvement",
            12: "confronting karmic debts and spiritual limitations"
        }
    }
    
    default = f"affecting the {HOUSE_MEANINGS[house_num]['name'].lower()} area of your life"
    return house_interpretations.get(planet, {}).get(house_num, default)


def check_natal_rulership(planet, natal_sun_sign):
    """
    Check if planet rules the natal sun sign
    """
    ruled_signs = RULERSHIPS.get(planet, [])
    return natal_sun_sign in ruled_signs


def generate_personalized_reading(current_positions, house_data, natal_sun_sign, natal_moon_sign):
    """
    Generate fully personalized astrological reading with house placements
    """
    moon_sign = current_positions["Moon"]["sign"]
    sun_sign = current_positions["Sun"]["sign"]
    
    natal_element = get_element(natal_sun_sign)
    
    # Build the main statement
    reading = f"Your Moon is currently transiting {moon_sign}"
    
    # Add Sun position
    if sun_sign != moon_sign:
        reading += f" whilst the Sun is in {sun_sign}"
    else:
        reading += f" alongside the Sun"
    
    # Find retrogrades and their houses
    retrogrades = []
    for planet_name, pos_data in current_positions.items():
        if pos_data["retrograde"] and planet_name not in ["Sun", "Moon"]:
            house_num = find_house_for_planet(pos_data["longitude"], house_data["cusps"])
            is_ruler = check_natal_rulership(planet_name, natal_sun_sign)
            retrogrades.append({
                "planet": planet_name,
                "sign": pos_data["sign"],
                "house": house_num,
                "is_ruler": is_ruler
            })
    
    # Add retrograde information to main statement
    if retrogrades:
        reading += ". Significantly, "
        retro_parts = []
        for retro in retrogrades:
            house_name = HOUSE_MEANINGS[retro["house"]]["name"]
            ruler_note = " (your chart ruler!)" if retro["is_ruler"] else ""
            retro_parts.append(
                f"{retro['planet']} is retrograde in {retro['sign']} in your {retro['house']}th house of {house_name}{ruler_note}"
            )
        reading += ", and ".join(retro_parts)
    
    reading += ". "
    
    # Add interpretation section
    reading += "\n\n**What This Means For You:**\n"
    
    # Retrograde interpretations
    if retrogrades:
        for retro in retrogrades:
            reading += f"\n• **{retro['planet']} Retrograde**: "
            
            # Element-based interpretation
            element_interp = get_retrograde_interpretation_by_element(retro["planet"], natal_element)
            reading += f"As a {natal_element} sign, {element_interp}. "
            
            # House-based interpretation
            house_interp = get_retrograde_interpretation_by_house(retro["planet"], retro["house"])
            reading += f"With this retrograde in your {retro['house']}th house, it's {house_interp}."
            
            # Extra emphasis if it's the chart ruler
            if retro["is_ruler"]:
                reading += f" **This is especially significant because {retro['planet']} rules your {natal_sun_sign} Sun, making its retrograde deeply personal.**"
    else:
        reading += "\n• No planets are currently in retrograde - a time of forward momentum and clear direction!"
    
    # Add natal chart context
    reading += f"\n\n**Your Natal Chart Context:**\n"
    reading += f"• Rising Sign (Ascendant): {house_data['ascendant']['sign']} at {house_data['ascendant']['degrees_in_sign']:.1f}°\n"
    reading += f"• Midheaven: {house_data['midheaven']['sign']} at {house_data['midheaven']['degrees_in_sign']:.1f}°\n"
    reading += f"• Sun Sign: {natal_sun_sign} ({natal_element} element)\n"
    reading += f"• Moon Sign: {natal_moon_sign} ({get_element(natal_moon_sign)} element)"
    
    return reading


def main():
    """Main function"""
    print("=" * 70)
    print("PERSONALIZED ASTROLOGICAL TRANSIT CALCULATOR")
    print("=" * 70)
    
    # Get natal chart information
    print("\n📍 NATAL CHART INFORMATION (Birth Details)")
    print("-" * 70)
    
    natal_year = int(input("Birth year: "))
    natal_month = int(input("Birth month (1-12): "))
    natal_day = int(input("Birth day: "))
    natal_hour = int(input("Birth hour (0-23): "))
    natal_minute = int(input("Birth minute (0-59): "))
    
    # Auto-geocoding of birth location
    print("\n🌍 BIRTH LOCATION")
    print("-" * 70)
    print("Enter your birth city/location (e.g., 'London', 'New York', 'Tokyo')")
    location_input = input("Location: ").strip()
    
    birth_lat, birth_lon, full_address = geocode_location(location_input)
    
    # Fallback to manual coordinates if geocoding fails
    if birth_lat is None or birth_lon is None:
        print("\n⚠ Geocoding failed. Please enter coordinates manually.")
        print("You can find coordinates at: https://www.latlong.net/")
        birth_lat = float(input("Birth latitude: "))
        birth_lon = float(input("Birth longitude: "))
        full_address = location_input
    
    birth_tz = input("Birth timezone (e.g., UTC, Europe/London, America/New_York): ").strip() or "UTC"
    
    # Auto-calculate Sun and Moon signs from birth data
    print("\n⭐ Calculating your natal Sun and Moon signs...")
    natal_sun_sign, natal_moon_sign = calculate_natal_positions(
        natal_year, natal_month, natal_day, natal_hour, natal_minute, 0, birth_tz
    )
    print(f"✓ Sun Sign: {natal_sun_sign}")
    print(f"✓ Moon Sign: {natal_moon_sign}")
    
    # Get transit time (current positions)
    print("\n" + "=" * 70)
    print("CURRENT TRANSIT TIME")
    print("-" * 70)
    use_current = input("Use current date/time for transit calculation? (y/n): ").lower().strip()
    
    if use_current == 'y':
        now = datetime.now()
        transit_year, transit_month, transit_day = now.year, now.month, now.day
        transit_hour, transit_minute, transit_second = now.hour, now.minute, now.second
        transit_tz = birth_tz
    else:
        transit_year = int(input("Transit year: "))
        transit_month = int(input("Transit month (1-12): "))
        transit_day = int(input("Transit day: "))
        transit_hour = int(input("Transit hour (0-23): "))
        transit_minute = int(input("Transit minute (0-59): "))
        transit_second = 0
        transit_tz = birth_tz
    
    print("\n" + "=" * 70)
    print("CALCULATING...")
    print("=" * 70)
    
    # Calculate natal houses
    house_data = calculate_houses(
        natal_year, natal_month, natal_day, natal_hour, natal_minute, 0,
        birth_lat, birth_lon, birth_tz
    )
    
    # Calculate current planetary positions
    current_positions = calculate_planetary_positions(
        transit_year, transit_month, transit_day, 
        transit_hour, transit_minute, transit_second, transit_tz
    )
    
    # Display current positions
    print("\n🌟 CURRENT PLANETARY POSITIONS")
    print(f"Date: {transit_year}-{transit_month:02d}-{transit_day:02d} {transit_hour:02d}:{transit_minute:02d}")
    print(f"Birth Location: {full_address}")
    print("-" * 70)
    
    for planet, data in current_positions.items():
        house_num = find_house_for_planet(data["longitude"], house_data["cusps"])
        house_name = HOUSE_MEANINGS[house_num]["name"]
        retro_marker = " ℞" if data["retrograde"] else ""
        print(f"{planet:12s}: {data['sign']:12s} ({data['degrees_in_sign']:5.2f}°) | House {house_num} ({house_name}){retro_marker}")
    
    # Generate personalized reading
    print("\n" + "=" * 70)
    print("YOUR PERSONALIZED ASTROLOGICAL READING")
    print("=" * 70)
    
    reading = generate_personalized_reading(
        current_positions, house_data, natal_sun_sign, natal_moon_sign
    )
    
    print(f"\n{reading}\n")
    print("=" * 70)


if __name__ == "__main__":
    main()
