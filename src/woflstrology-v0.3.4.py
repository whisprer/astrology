#!/usr/bin/env python3
"""
Advanced Astrological Position Calculator with Compatibility Analysis
Full natal chart, transits, and relationship compatibility
"""

import swisseph as swe
from datetime import datetime, timedelta
import pytz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import json
import random
import os
import sys
from collections import Counter

# SET EPHEMERIS PATH - tell pyswisseph where to find ephemeris files
# This looks in the same directory as your script
script_dir = os.path.dirname(os.path.abspath(__file__))
ephe_path = os.path.join(script_dir, 'ephe')
swe.set_ephe_path(ephe_path)


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


def load_horoscope_database():
    """
    Load horoscope content from JSON database
    Works both as script and as bundled executable
    """
    # Determine if we're running as a script or frozen exe
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as normal Python script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    db_path = os.path.join(base_path, "horoscope_database.json")
    
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"⚠ Warning: {db_path} not found. Using default minimal database.")
        # Minimal fallback
        return {
            "sun_sign_themes": {sign: ["Energies are active"] for sign in ZODIAC_SIGNS},
            "moon_sign_influences": {sign: "influencing emotions" for sign in ZODIAC_SIGNS},
            "element_combinations": {},
            "general_wisdom": ["The stars guide you"],
            "house_daily_focus": {},
            "compatibility": {
                "element_dynamics": {},
                "universal_relationship_patterns": [],
                "compatibility_advice": {"challenging": [], "harmonious": [], "neutral": []},
                "transit_influences_on_relationships": {}
            }
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
    
    # House cusps
    for i in range(1, 13):
        if i < len(cusps):
            cusp_long = cusps[i]
            house_data["cusps"][i] = {
                "longitude": cusp_long,
                "sign": get_zodiac_sign(cusp_long),
                "degrees_in_sign": cusp_long % 30
            }
        else:
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
    """
    planet_long = planet_longitude % 360
    
    for house_num in range(1, 13):
        current_cusp = house_cusps[house_num]["longitude"] % 360
        next_house_num = (house_num % 12) + 1
        next_cusp = house_cusps[next_house_num]["longitude"] % 360
        
        if current_cusp < next_cusp:
            if current_cusp <= planet_long < next_cusp:
                return house_num
        else:
            if planet_long >= current_cusp or planet_long < next_cusp:
                return house_num
    
    return 1


def get_retrograde_interpretation_by_element(planet, element):
    """
    Get element-specific retrograde interpretation
    """
    interpretations = {
        "Mercury": {
            "Fire": "this influences your communication style and how you express your bold ideas",
            "Earth": "this brings attention to practical matters, contracts, organization, and daily planning",
            "Air": "this impacts your natural communication gifts and social connections",
            "Water": "this touches on emotional communication and intuitive decision-making"
        },
        "Mars": {
            "Fire": "this affects your natural drive, initiative, and how you channel action",
            "Earth": "this influences your work motivation and daily productivity patterns",
            "Air": "this impacts social assertiveness and group advocacy",
            "Water": "this touches on emotional reactions and how you handle confrontation"
        },
        "Venus": {
            "Fire": "this influences romantic expression and what you value in relationships",
            "Earth": "this brings focus to financial matters and material possessions",
            "Air": "this affects social dynamics, friendships, and partnerships",
            "Water": "this touches on deep emotional bonds and relationship patterns"
        },
        "Saturn": {
            "Fire": "this influences ambitious drive and long-term goal structures",
            "Earth": "this brings focus to career foundations and practical structures",
            "Air": "this affects mental frameworks and belief systems",
            "Water": "this touches on emotional boundaries and security needs"
        },
        "Jupiter": {
            "Fire": "this influences optimism, expansion, and your sense of adventure",
            "Earth": "this brings focus to growth in material and practical areas",
            "Air": "this affects learning, teaching, and sharing knowledge",
            "Water": "this touches on spiritual growth and emotional expansion"
        },
        "Uranus": {
            "Fire": "this influences innovation, rebellion, and your unique self-expression",
            "Earth": "this brings focus to changes in practical routines and stability",
            "Air": "this affects intellectual breakthroughs and social reform",
            "Water": "this touches on emotional liberation and intuitive insights"
        },
        "Neptune": {
            "Fire": "this influences inspiration, idealism, and creative vision",
            "Earth": "this brings focus to dissolving old structures and material attachments",
            "Air": "this affects imagination, illusions, and mental clarity",
            "Water": "this touches on spiritual connection and emotional boundaries"
        },
        "Pluto": {
            "Fire": "this influences personal power, transformation, and will",
            "Earth": "this brings focus to deep changes in resources and security",
            "Air": "this affects psychological insights and communication power",
            "Water": "this touches on emotional depths, secrets, and profound change"
        }
    }
    
    return interpretations.get(planet, {}).get(element, "this planetary energy turns inward for reflection")


def get_retrograde_interpretation_by_house(planet, house_num):
    """
    Get house-specific retrograde interpretation
    """
    house_interpretations = {
        "Mercury": {
            1: "influencing your self-expression and how you present yourself to the world",
            2: "bringing attention to financial decisions and resource management",
            3: "impacting daily communication, short trips, and sibling connections",
            4: "touching on family matters and your home and emotional foundations",
            5: "affecting creative projects, romance, and relationships with children",
            6: "influencing daily work routines, health habits, and service to others",
            7: "having an effect on partnerships, contracts, and one-on-one relationships",
            8: "bringing focus to shared resources, intimacy, and transformation",
            9: "impacting travel plans, higher learning, and philosophical beliefs",
            10: "affecting your career, public reputation, and relationship with authority",
            11: "influencing friendships, group activities, and long-term goals",
            12: "bringing attention to hidden matters and spiritual practices"
        },
        "Mars": {
            1: "influencing your personal drive and physical vitality",
            2: "affecting efforts around earning and building material security",
            3: "impacting daily interactions and local travel",
            4: "touching on home dynamics and family matters",
            5: "influencing creative output and romantic pursuits",
            6: "affecting energy for daily tasks and health matters",
            7: "bringing focus to relationship dynamics and past conflicts",
            8: "impacting power dynamics around shared resources",
            9: "affecting beliefs and long-distance matters",
            10: "influencing interactions with authority and career progress",
            11: "touching on dynamics within friend groups and social networks",
            12: "bringing attention to internalized anger and spiritual processing"
        },
        "Venus": {
            1: "influencing how you value yourself and your self-image",
            2: "bringing focus to spending habits and material values",
            3: "touching on relationships with siblings and neighbors",
            4: "affecting family values and what makes you feel at home",
            5: "influencing romantic relationships and creative projects",
            6: "impacting work relationships and daily pleasures",
            7: "bringing attention to partnership dynamics and past relationships",
            8: "affecting shared finances and intimate bonds",
            9: "touching on beliefs about love and relationships",
            10: "influencing professional relationships and public image",
            11: "affecting friendships and social values",
            12: "bringing focus to hidden relationships and values"
        },
        "Saturn": {
            1: "influencing self-discipline and personal responsibility",
            2: "bringing focus to financial structures and security",
            3: "affecting communication patterns and learning",
            4: "touching on family karma and foundational issues",
            5: "influencing creative endeavors and romantic commitments",
            6: "impacting work burdens and health matters",
            7: "bringing attention to relationship commitments and structures",
            8: "affecting deep fears and shared resource management",
            9: "touching on long-held beliefs and philosophies",
            10: "influencing career foundations and professional authority",
            11: "affecting friendships and group involvement quality",
            12: "bringing focus to karmic debts and spiritual limitations"
        },
        "Jupiter": {
            1: "influencing personal growth and self-confidence",
            2: "bringing focus to wealth expansion and abundance",
            3: "affecting learning opportunities and local connections",
            4: "touching on family blessings and home expansion",
            5: "influencing creative joy and romantic optimism",
            6: "impacting work fulfillment and health improvement",
            7: "affecting partnership growth and legal matters",
            8: "bringing attention to shared wealth and transformation",
            9: "influencing travel, education, and spiritual understanding",
            10: "affecting career opportunities and public recognition",
            11: "touching on community involvement and future hopes",
            12: "bringing focus to spiritual expansion and hidden blessings"
        },
        "Uranus": {
            1: "influencing personal freedom and unique self-expression",
            2: "bringing focus to sudden changes in resources and values",
            3: "affecting communication breakthroughs and unexpected news",
            4: "touching on home disruptions and family independence",
            5: "influencing creative innovation and unconventional romance",
            6: "impacting work changes and alternative health approaches",
            7: "affecting partnership freedom and unexpected relationship shifts",
            8: "bringing attention to sudden transformations and shared resources",
            9: "influencing radical beliefs and unexpected travel",
            10: "affecting career changes and public image shifts",
            11: "touching on friendship dynamics and group innovation",
            12: "bringing focus to sudden spiritual insights and hidden breakthroughs"
        },
        "Neptune": {
            1: "influencing self-image and spiritual identity",
            2: "bringing focus to financial illusions and material transcendence",
            3: "affecting communication clarity and intuitive messages",
            4: "touching on family ideals and emotional sensitivity",
            5: "influencing creative imagination and romantic idealism",
            6: "impacting work inspiration and health sensitivity",
            7: "affecting partnership ideals and relationship boundaries",
            8: "bringing attention to shared mysteries and spiritual transformation",
            9: "influencing spiritual beliefs and mystical experiences",
            10: "affecting career vision and public image idealization",
            11: "touching on social ideals and collective dreams",
            12: "bringing focus to spiritual connection and subconscious dissolution"
        },
        "Pluto": {
            1: "influencing personal power and transformative identity shifts",
            2: "bringing focus to resource control and value transformation",
            3: "affecting communication intensity and revealing hidden information",
            4: "touching on family power dynamics and ancestral healing",
            5: "influencing creative power and transformative romance",
            6: "impacting work transformation and deep health healing",
            7: "affecting relationship power dynamics and profound partnership shifts",
            8: "bringing attention to shared power, secrets, and rebirth",
            9: "influencing belief transformation and profound philosophical shifts",
            10: "affecting career power and public transformation",
            11: "touching on group power dynamics and collective transformation",
            12: "bringing focus to shadow work and spiritual rebirth"
        }
    }
    
    default = f"influencing the {HOUSE_MEANINGS[house_num]['name'].lower()} area of your life"
    return house_interpretations.get(planet, {}).get(house_num, default)


def check_natal_rulership(planet, natal_sun_sign):
    """
    Check if planet rules the natal sun sign
    """
    ruled_signs = RULERSHIPS.get(planet, [])
    return natal_sun_sign in ruled_signs


def generate_general_horoscope(current_positions, house_data, natal_sun_sign, horoscope_db):
    """
    Generate general daily horoscope from database
    """
    current_sun_sign = current_positions["Sun"]["sign"]
    current_moon_sign = current_positions["Moon"]["sign"]
    
    natal_element = get_element(natal_sun_sign)
    current_sun_element = get_element(current_sun_sign)
    current_moon_element = get_element(current_moon_sign)
    
    # Build general horoscope
    horoscope = f"\n**General Horoscope for {natal_sun_sign}:**\n\n"
    
    # Sun sign theme
    sun_themes = horoscope_db.get("sun_sign_themes", {}).get(current_sun_sign, ["Cosmic energies are at work"])
    sun_theme = random.choice(sun_themes)
    horoscope += f"With the Sun in {current_sun_sign}, {sun_theme.lower()}. "
    
    # Moon influence
    moon_influence = horoscope_db.get("moon_sign_influences", {}).get(current_moon_sign, "affecting your emotions")
    horoscope += f"The Moon in {current_moon_sign} is {moon_influence}. "
    
    # Element combination
    combo_key = f"{current_sun_element}_{current_moon_element}"
    element_combo = horoscope_db.get("element_combinations", {}).get(combo_key, "creating a unique energetic blend")
    horoscope += f"This combination of {element_combo}.\n\n"
    
    # Find the house with most planets (or random if tie)
    house_planet_counts = {}
    for planet_name, pos_data in current_positions.items():
        house_num = find_house_for_planet(pos_data["longitude"], house_data["cusps"])
        house_planet_counts[house_num] = house_planet_counts.get(house_num, 0) + 1
    
    prominent_house = max(house_planet_counts, key=house_planet_counts.get)
    house_focus = horoscope_db.get("house_daily_focus", {}).get(str(prominent_house), 
                                                                 f"influencing the {HOUSE_MEANINGS[prominent_house]['name'].lower()} area")
    horoscope += f"Today's cosmic emphasis falls on your {prominent_house}th house, {house_focus}. "
    
    # General wisdom
    wisdom = random.choice(horoscope_db.get("general_wisdom", ["Trust the cosmic flow"]))
    horoscope += f"{wisdom}."
    
    return horoscope


def determine_compatibility_type(sign1_element, sign2_element):
    """
    Determine if pairing is challenging, harmonious, or neutral
    """
    # Same element = harmonious
    if sign1_element == sign2_element:
        return "harmonious"
    
    # Compatible elements
    compatible_pairs = [
        ("Fire", "Air"), ("Air", "Fire"),
        ("Earth", "Water"), ("Water", "Earth")
    ]
    
    if (sign1_element, sign2_element) in compatible_pairs:
        return "harmonious"
    
    # Challenging elements
    challenging_pairs = [
        ("Fire", "Water"), ("Water", "Fire"),
        ("Earth", "Air"), ("Air", "Earth")
    ]
    
    if (sign1_element, sign2_element) in challenging_pairs:
        return "challenging"
    
    # Fire-Earth and Water-Air are neutral
    return "neutral"


def generate_compatibility_reading(natal_sun_sign, partner_sun_sign, current_positions, horoscope_db):
    """
    Generate compatibility analysis between two sun signs
    """
    natal_element = get_element(natal_sun_sign)
    partner_element = get_element(partner_sun_sign)
    
    # Determine compatibility type
    compat_type = determine_compatibility_type(natal_element, partner_element)
    
    reading = f"\n{'=' * 70}\n"
    reading += f"RELATIONSHIP COMPATIBILITY ANALYSIS\n"
    reading += f"{natal_sun_sign} ({natal_element}) ♥ {partner_sun_sign} ({partner_element})\n"
    reading += f"{'=' * 70}\n\n"
    
    # Element dynamics
    element_key = f"{natal_element}_{partner_element}"
    element_dynamic = horoscope_db.get("compatibility", {}).get("element_dynamics", {}).get(
        element_key, "This pairing brings together different energetic qualities that require conscious navigation."
    )
    
    reading += f"**Elemental Dynamic:**\n{element_dynamic}\n\n"
    
    # Universal relationship pattern (random selection)
    patterns = horoscope_db.get("compatibility", {}).get("universal_relationship_patterns", [])
    if patterns:
        num_patterns = min(3, len(patterns))
        selected_patterns = random.sample(patterns, num_patterns)
        reading += f"**Relational Patterns to Consider:**\n"
        for pattern in selected_patterns:
            reading += f"• {pattern}\n"
        reading += "\n"
    
    # Compatibility advice based on type
    advice_list = horoscope_db.get("compatibility", {}).get("compatibility_advice", {}).get(compat_type, [])
    if advice_list:
        advice = random.choice(advice_list)
        reading += f"**Astrological Guidance:**\n{advice}\n\n"
    
    # Current transit influences on relationships
    transit_influences = []
    
    # Check for retrograde planets that affect relationships
    if current_positions.get("Venus", {}).get("retrograde"):
        venus_retro = horoscope_db.get("compatibility", {}).get("transit_influences_on_relationships", {}).get("venus_retrograde", [])
        if venus_retro:
            transit_influences.append(("Venus Retrograde", random.choice(venus_retro)))
    
    if current_positions.get("Mars", {}).get("retrograde"):
        mars_retro = horoscope_db.get("compatibility", {}).get("transit_influences_on_relationships", {}).get("mars_retrograde", [])
        if mars_retro:
            transit_influences.append(("Mars Retrograde", random.choice(mars_retro)))
    
    if current_positions.get("Mercury", {}).get("retrograde"):
        mercury_retro = horoscope_db.get("compatibility", {}).get("transit_influences_on_relationships", {}).get("mercury_retrograde", [])
        if mercury_retro:
            transit_influences.append(("Mercury Retrograde", random.choice(mercury_retro)))
    
    # Add other transit influences based on current positions
    # Jupiter expansion if Jupiter is prominent
    jupiter_influence = horoscope_db.get("compatibility", {}).get("transit_influences_on_relationships", {}).get("jupiter_expansion", [])
    if jupiter_influence and random.random() > 0.5:  # 50% chance to include
        transit_influences.append(("Jupiter's Expansion", random.choice(jupiter_influence)))
    
    # Add Neptune or Pluto influences occasionally
    if current_positions.get("Neptune") and random.random() > 0.7:
        neptune_influence = horoscope_db.get("compatibility", {}).get("transit_influences_on_relationships", {}).get("neptune_illusion", [])
        if neptune_influence:
            transit_influences.append(("Neptune's Veil", random.choice(neptune_influence)))
    
    if current_positions.get("Pluto") and random.random() > 0.7:
        pluto_influence = horoscope_db.get("compatibility", {}).get("transit_influences_on_relationships", {}).get("pluto_transformation", [])
        if pluto_influence:
            transit_influences.append(("Pluto's Depth", random.choice(pluto_influence)))
    
    if transit_influences:
        reading += f"**Current Cosmic Influences on Relationships:**\n"
        for influence_name, influence_text in transit_influences:
            reading += f"\n• **{influence_name}**: {influence_text}\n"
    else:
        reading += f"**Current Cosmic Climate:**\nNo major planetary retrogrades currently affecting relationship dynamics. This period favors forward movement and clarity in romantic matters.\n"
    
    reading += f"\n{'=' * 70}\n"
    
    return reading


def generate_personalized_reading(current_positions, house_data, natal_sun_sign, natal_moon_sign, horoscope_db):
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
    
    # Add general horoscope
    reading += generate_general_horoscope(current_positions, house_data, natal_sun_sign, horoscope_db)
    
    # Add interpretation section
    reading += "\n\n**Specific Transit Influences:**\n"
    
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


def calculate_aspect_angle(long1, long2):
    """
    Calculate the shortest angle between two planetary longitudes
    """
    diff = abs(long1 - long2)
    if diff > 180:
        diff = 360 - diff
    return diff


def detect_aspects(natal_positions):
    """
    Detect major aspects between natal planets
    """
    aspects = []
    planet_list = list(natal_positions.keys())
    
    # Aspect definitions: (name, angle, orb)
    aspect_types = [
        ("conjunction", 0, 8),
        ("opposition", 180, 8),
        ("trine", 120, 8),
        ("square", 90, 8),
        ("sextile", 60, 6)
    ]
    
    # Check each pair of planets
    for i, planet1 in enumerate(planet_list):
        for planet2 in planet_list[i+1:]:
            long1 = natal_positions[planet1]["longitude"]
            long2 = natal_positions[planet2]["longitude"]
            
            angle = calculate_aspect_angle(long1, long2)
            
            # Check if angle matches any aspect
            for aspect_name, target_angle, orb in aspect_types:
                if abs(angle - target_angle) <= orb:
                    aspects.append({
                        "type": aspect_name,
                        "planet1": planet1,
                        "planet2": planet2,
                        "angle": angle
                    })
                    break  # Don't count the same pair twice
    
    return aspects


def calculate_full_natal_chart(year, month, day, hour, minute, second, lat, lon, timezone_str="UTC"):
    """
    Calculate complete natal chart with all planets
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
    
    natal_positions = {}
    
    # Calculate for each planet
    for planet_name, planet_id in PLANETS.items():
        result, ret_flag = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
        
        longitude = result[0]
        speed = result[3]
        
        sign = get_zodiac_sign(longitude)
        is_retrograde = speed < 0
        
        natal_positions[planet_name] = {
            "planet": planet_name,
            "sign": sign,
            "longitude": longitude,
            "speed": speed,
            "retrograde": is_retrograde,
            "degrees_in_sign": longitude % 30
        }
    
    return natal_positions


def generate_natal_chart_reading(natal_positions, house_data, horoscope_db):
    """
    Generate comprehensive natal chart reading with detailed aspect interpretations
    """
    reading = f"\n{'=' * 70}\n"
    reading += f"NATAL CHART READING\n"
    reading += f"Your Birth Chart Blueprint\n"
    reading += f"{'=' * 70}\n\n"
    
    # Rising sign interpretation
    asc_sign = house_data["ascendant"]["sign"]
    rising_interp = horoscope_db.get("natal_chart", {}).get("rising_sign", {}).get(
        asc_sign, "Your rising sign shapes how you meet the world."
    )
    reading += f"**Rising Sign (Ascendant): {asc_sign}**\n"
    reading += f"{rising_interp}\n\n"
    
    # Core planets
    reading += f"**Core Planetary Placements:**\n\n"
    
    core_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
    for planet in core_planets:
        if planet in natal_positions:
            pos = natal_positions[planet]
            sign = pos["sign"]
            house_num = find_house_for_planet(pos["longitude"], house_data["cusps"])
            retro = " ℞" if pos["retrograde"] else ""
            
            planet_sign_key = f"{planet}_{sign}"
            interp = horoscope_db.get("natal_chart", {}).get("planet_in_sign", {}).get(
                planet_sign_key, f"Your {planet} in {sign} shapes this planetary energy."
            )
            
            reading += f"• **{planet} in {sign}** (House {house_num}){retro}\n"
            reading += f"  {interp}\n\n"
    
    # Natal retrogrades
    natal_retrogrades = [p for p, data in natal_positions.items() if data["retrograde"] and p not in ["Sun", "Moon"]]
    
    if natal_retrogrades:
        reading += f"**Natal Retrograde Planets:**\n\n"
        reading += f"You were born with {len(natal_retrogrades)} planet(s) in retrograde motion:\n\n"
        
        for planet in natal_retrogrades:
            retro_interp = horoscope_db.get("natal_chart", {}).get("natal_retrograde", {}).get(
                planet, f"{planet} retrograde at birth indicates internal processing."
            )
            reading += f"• **{planet} Retrograde**: {retro_interp}\n\n"
    
    # DETAILED ASPECTS with interpretations
    aspects = detect_aspects(natal_positions)
    
    if aspects:
        reading += f"**Major Aspects - The Story of Your Inner Dynamics:**\n\n"
        reading += f"Aspects reveal how different facets of your personality interact, creating the complex tapestry of who you are. These are not just abstract symbols—they describe real patterns you've lived, are living, and will continue to navigate.\n\n"
        
        # Sort aspects by importance (conjunctions first, then oppositions, etc.)
        aspect_order = ["conjunction", "opposition", "trine", "square", "sextile"]
        aspects_sorted = sorted(aspects, key=lambda x: aspect_order.index(x["type"]) if x["type"] in aspect_order else 99)
        
        for aspect in aspects_sorted:  # Show all aspects
            planet1 = aspect["planet1"]
            planet2 = aspect["planet2"]
            aspect_type = aspect["type"]
            angle = aspect["angle"]
            
            # Try both possible key orders (e.g., Sun_Moon and Moon_Sun)
            aspect_key1 = f"{planet1}_{planet2}"
            aspect_key2 = f"{planet2}_{planet1}"
            
            aspect_interps = horoscope_db.get("natal_chart", {}).get("aspect_interpretations", {})
            
            # Try first key order
            detailed_interp = aspect_interps.get(aspect_key1, {}).get(aspect_type)
            
            # If not found, try reversed order
            if not detailed_interp:
                detailed_interp = aspect_interps.get(aspect_key2, {}).get(aspect_type)
            
            # If still not found, use default
            if not detailed_interp:
                detailed_interp = f"These planetary energies interact through {aspect_type}."
            
            # ADD THE ASPECT TO THE READING (this was missing!)
            reading += f"**{planet1} {aspect_type.title()} {planet2}** ({angle:.1f}°)\n"
            reading += f"{detailed_interp}\n\n"

        # This message should be here, AFTER the loop, but INSIDE the if block
        reading += f"*Your chart contains {len(aspects)} aspects forming the complete pattern of your psyche.*\n\n"

# CHART PATTERNS
    patterns = detect_chart_patterns(natal_positions)
    
    if patterns:
        reading += f"\n**Special Chart Patterns - Configurations of Destiny:**\n\n"
        reading += f"Your chart contains rare geometric patterns that significantly shape your life experience:\n\n"
        
        for pattern in patterns:
            pattern_type = pattern["type"]
            pattern_info = horoscope_db.get("natal_chart", {}).get("chart_patterns", {}).get(pattern_type, {})
            
            description = pattern_info.get("description", "")
            interpretation = pattern_info.get("interpretation", "")
            
            if pattern_type == "stellium":
                planet_names = ", ".join(pattern["planets"])
                reading += f"**Stellium in {pattern['sign']}**: {planet_names}\n"
            elif pattern_type == "t_square":
                planet_names = ", ".join(pattern["planets"])
                reading += f"**T-Square**: {planet_names} with apex at {pattern['apex']}\n"
            elif pattern_type == "yod":
                planet_names = ", ".join(pattern["planets"])
                reading += f"**Yod (Finger of God)**: {planet_names} pointing to {pattern['apex']}\n"
            elif pattern_type == "grand_trine":
                planet_names = ", ".join(pattern["planets"])
                reading += f"**Grand Trine in {pattern['element']}**: {planet_names}\n"
            else:
                planet_names = ", ".join(pattern["planets"])
                reading += f"**{pattern_type.replace('_', ' ').title()}**: {planet_names}\n"
            
            reading += f"{description}\n{interpretation}\n\n"
    
    # ELEMENTAL BALANCE
    element_balance = calculate_elemental_balance(natal_positions)
    
    reading += f"\n**Elemental Balance - Your Fundamental Nature:**\n\n"
    
    for element, data in element_balance.items():
        count = data["count"]
        percentage = data["percentage"]
        level = data["level"]
        
        element_info = horoscope_db.get("natal_chart", {}).get("elements", {}).get(element, {})
        keywords = element_info.get("keywords", "")
        interp = element_info.get(level, "This element influences your nature.")
        
        reading += f"**{element}** ({count} planets, {percentage:.0f}%) - *{keywords}*\n"
        reading += f"{interp}\n\n"
    
    # MODALITY BALANCE
    modality_balance = calculate_modality_balance(natal_positions)
    
    reading += f"\n**Modality Balance - Your Approach to Life:**\n\n"
    
    for modality, data in modality_balance.items():
        count = data["count"]
        percentage = data["percentage"]
        level = data["level"]
        
        mod_info = horoscope_db.get("natal_chart", {}).get("modalities", {}).get(modality, {})
        keywords = mod_info.get("keywords", "")
        interp = mod_info.get(level, "This modality influences your approach.")
        
        reading += f"**{modality}** ({count} planets, {percentage:.0f}%) - *{keywords}*\n"
        reading += f"{interp}\n\n"
    
    # DOMINANT PLANET
    dominant_planet, score = calculate_dominant_planet(natal_positions, house_data)
    
    reading += f"\n**Chart Ruler - Your Dominant Energy:**\n\n"
    reading += f"**{dominant_planet}** dominates your chart (influence score: {score})\n"
    
    dominant_interp = horoscope_db.get("natal_chart", {}).get("dominant_planet", {}).get(
        dominant_planet, f"{dominant_planet} energy shapes your life significantly."
    )
    reading += f"{dominant_interp}\n\n"
    
    # PLANETARY HOUR (current time)
    current_hour_planet = get_planetary_hour(datetime.now())
    hour_interp = horoscope_db.get("natal_chart", {}).get("planetary_hours", {}).get(
        current_hour_planet, "This planetary hour influences current activities."
    )
    
    reading += f"\n**Current Planetary Hour:**\n\n"
    reading += f"Right now ({datetime.now().strftime('%I:%M %p')}), the hour is ruled by **{current_hour_planet}**.\n"
    reading += f"{hour_interp}\n\n"
    
    reading += f"{'=' * 70}\n"
    
    return reading


def detect_chart_patterns(natal_positions):
    """
    Detect special chart patterns (Grand Trine, Grand Cross, T-Square, Stellium, Yod, Kite)
    """
    patterns = []
    planet_list = list(natal_positions.keys())
    
    # Helper to find planets in aspect
    def planets_in_aspect(planet1, planet2, target_angle, orb):
        long1 = natal_positions[planet1]["longitude"]
        long2 = natal_positions[planet2]["longitude"]
        angle = calculate_aspect_angle(long1, long2)
        return abs(angle - target_angle) <= orb
    
    # GRAND TRINE - 3 planets all trine each other (120° apart)
    for i, p1 in enumerate(planet_list):
        for j, p2 in enumerate(planet_list[i+1:], i+1):
            for k, p3 in enumerate(planet_list[j+1:], j+1):
                if (planets_in_aspect(p1, p2, 120, 8) and
                    planets_in_aspect(p2, p3, 120, 8) and
                    planets_in_aspect(p1, p3, 120, 8)):
                    
                    # Determine element
                    signs = [natal_positions[p]["sign"] for p in [p1, p2, p3]]
                    elements = [get_element(s) for s in signs]
                    element = max(set(elements), key=elements.count)
                    
                    patterns.append({
                        "type": "grand_trine",
                        "planets": [p1, p2, p3],
                        "element": element
                    })
    
    # GRAND CROSS - 4 planets, 2 oppositions squared to each other
    for i, p1 in enumerate(planet_list):
        for j, p2 in enumerate(planet_list[i+1:], i+1):
            if planets_in_aspect(p1, p2, 180, 8):  # Opposition
                for k, p3 in enumerate(planet_list):
                    if p3 not in [p1, p2] and planets_in_aspect(p1, p3, 90, 8):
                        for l, p4 in enumerate(planet_list):
                            if (p4 not in [p1, p2, p3] and
                                planets_in_aspect(p2, p4, 90, 8) and
                                planets_in_aspect(p3, p4, 180, 8)):
                                
                                pattern_planets = sorted([p1, p2, p3, p4])
                                if not any(p["type"] == "grand_cross" and sorted(p["planets"]) == pattern_planets for p in patterns):
                                    patterns.append({
                                        "type": "grand_cross",
                                        "planets": [p1, p2, p3, p4]
                                    })
    
    # T-SQUARE - 2 planets oppose, both square a 3rd (apex)
    for i, p1 in enumerate(planet_list):
        for j, p2 in enumerate(planet_list[i+1:], i+1):
            if planets_in_aspect(p1, p2, 180, 8):  # Opposition
                for apex in planet_list:
                    if apex not in [p1, p2]:
                        if (planets_in_aspect(p1, apex, 90, 8) and
                            planets_in_aspect(p2, apex, 90, 8)):
                            
                            pattern_planets = sorted([p1, p2, apex])
                            if not any(p["type"] == "t_square" and sorted(p["planets"]) == pattern_planets for p in patterns):
                                patterns.append({
                                    "type": "t_square",
                                    "planets": [p1, p2],
                                    "apex": apex
                                })
    
    # STELLIUM - 3+ planets in same sign or house
    from collections import Counter
    
    signs_count = Counter([natal_positions[p]["sign"] for p in planet_list])
    for sign, count in signs_count.items():
        if count >= 3:
            stellium_planets = [p for p in planet_list if natal_positions[p]["sign"] == sign]
            patterns.append({
                "type": "stellium",
                "planets": stellium_planets,
                "sign": sign
            })
    
    # YOD - 2 planets sextile, both quincunx (150°) a 3rd (apex)
    for i, p1 in enumerate(planet_list):
        for j, p2 in enumerate(planet_list[i+1:], i+1):
            if planets_in_aspect(p1, p2, 60, 6):  # Sextile
                for apex in planet_list:
                    if apex not in [p1, p2]:
                        if (planets_in_aspect(p1, apex, 150, 3) and
                            planets_in_aspect(p2, apex, 150, 3)):
                            
                            pattern_planets = sorted([p1, p2, apex])
                            if not any(p["type"] == "yod" and sorted(p["planets"]) == pattern_planets for p in patterns):
                                patterns.append({
                                    "type": "yod",
                                    "planets": [p1, p2],
                                    "apex": apex
                                })
    
    return patterns


def calculate_elemental_balance(natal_positions):
    """
    Calculate how many planets in each element
    """
    from collections import Counter
    
    elements = [get_element(natal_positions[p]["sign"]) for p in natal_positions]
    element_count = Counter(elements)
    
    total = len(natal_positions)
    balance = {}
    
    for element in ["Fire", "Earth", "Air", "Water"]:
        count = element_count.get(element, 0)
        percentage = (count / total) * 100
        
        # Determine if high, balanced, or low
        if percentage > 40:
            level = "high"
        elif percentage < 15:
            level = "low"
        else:
            level = "balanced"
        
        balance[element] = {
            "count": count,
            "percentage": percentage,
            "level": level
        }
    
    return balance


def calculate_modality_balance(natal_positions):
    """
    Calculate how many planets in each modality (Cardinal/Fixed/Mutable)
    """
    from collections import Counter
    
    modality_signs = {
        "Cardinal": ["Aries", "Cancer", "Libra", "Capricorn"],
        "Fixed": ["Taurus", "Leo", "Scorpio", "Aquarius"],
        "Mutable": ["Gemini", "Virgo", "Sagittarius", "Pisces"]
    }
    
    modalities = []
    for planet in natal_positions:
        sign = natal_positions[planet]["sign"]
        for mod, signs in modality_signs.items():
            if sign in signs:
                modalities.append(mod)
                break
    
    mod_count = Counter(modalities)
    total = len(natal_positions)
    balance = {}
    
    for modality in ["Cardinal", "Fixed", "Mutable"]:
        count = mod_count.get(modality, 0)
        percentage = (count / total) * 100
        
        if percentage > 40:
            level = "high"
        elif percentage < 20:
            level = "low"
        else:
            level = "balanced"
        
        balance[modality] = {
            "count": count,
            "percentage": percentage,
            "level": level
        }
    
    return balance


def calculate_dominant_planet(natal_positions, house_data):
    """
    Determine which planet has the most influence in the chart
    """
    scores = {planet: 0 for planet in natal_positions}
    
    # Points for ruling the Ascendant
    asc_sign = house_data["ascendant"]["sign"]
    for planet, ruled_signs in RULERSHIPS.items():
        if asc_sign in ruled_signs:
            scores[planet] += 5
    
    # Points for angular houses (1st, 4th, 7th, 10th)
    angular_houses = [1, 4, 7, 10]
    for planet, pos_data in natal_positions.items():
        house_num = find_house_for_planet(pos_data["longitude"], house_data["cusps"])
        if house_num in angular_houses:
            scores[planet] += 3
    
    # Points for being in ruling sign (dignity)
    for planet, pos_data in natal_positions.items():
        sign = pos_data["sign"]
        if planet in RULERSHIPS and sign in RULERSHIPS[planet]:
            scores[planet] += 4
    
    # Points for number of aspects
    aspects = detect_aspects(natal_positions)
    for aspect in aspects:
        scores[aspect["planet1"]] += 1
        scores[aspect["planet2"]] += 1
    
    # Find planet with highest score
    dominant = max(scores, key=scores.get)
    return dominant, scores[dominant]


def get_planetary_hour(dt):
    """
    Calculate which planet rules the current hour
    Traditional planetary hours system
    """
    # Planetary hour order (Chaldean order)
    planet_order = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
    
    # Day rulers
    day_rulers = {
        0: "Moon",      # Monday
        1: "Mars",      # Tuesday
        2: "Mercury",   # Wednesday
        3: "Jupiter",   # Thursday
        4: "Venus",     # Friday
        5: "Saturn",    # Saturday
        6: "Sun"        # Sunday
    }
    
    day_of_week = dt.weekday()
    hour_of_day = dt.hour
    
    # First hour of each day is ruled by that day's planet
    first_hour_planet = day_rulers[day_of_week]
    first_hour_index = planet_order.index(first_hour_planet)
    
    # Each subsequent hour moves to next planet in order
    current_hour_index = (first_hour_index + hour_of_day) % 7
    current_hour_planet = planet_order[current_hour_index]
    
    return current_hour_planet


def calculate_transits_to_natal(current_positions, natal_positions, house_data, horoscope_db):
    """
    Calculate current transiting planets' aspects to natal chart
    """
    transits = []
    
    for current_planet, current_data in current_positions.items():
        for natal_planet, natal_data in natal_positions.items():
            # Calculate aspect between current and natal position
            angle = calculate_aspect_angle(current_data["longitude"], natal_data["longitude"])
            
            # Check for major aspects
            aspect_types = [
                ("conjunction", 0, 8),
                ("opposition", 180, 8),
                ("trine", 120, 8),
                ("square", 90, 8),
                ("sextile", 60, 6)
            ]
            
            for aspect_name, target_angle, orb in aspect_types:
                if abs(angle - target_angle) <= orb:
                    # Find which natal house is being transited
                    natal_house = find_house_for_planet(natal_data["longitude"], house_data["cusps"])
                    
                    transits.append({
                        "transiting_planet": current_planet,
                        "natal_planet": natal_planet,
                        "aspect": aspect_name,
                        "angle": angle,
                        "natal_house": natal_house,
                        "orb": abs(angle - target_angle)
                    })
                    break
    
    # Sort by orb (tighter aspects first)
    transits.sort(key=lambda x: x["orb"])
    
    return transits


def calculate_lunar_phase_at_birth(natal_positions):
    """
    Calculate which lunar phase the person was born under
    """
    sun_long = natal_positions["Sun"]["longitude"]
    moon_long = natal_positions["Moon"]["longitude"]
    
    # Calculate angle from Sun to Moon
    phase_angle = (moon_long - sun_long) % 360
    
    # Determine phase
    if phase_angle < 45:
        return "new_moon", phase_angle
    elif phase_angle < 90:
        return "crescent_moon", phase_angle
    elif phase_angle < 135:
        return "first_quarter", phase_angle
    elif phase_angle < 180:
        return "gibbous_moon", phase_angle
    elif phase_angle < 225:
        return "full_moon", phase_angle
    elif phase_angle < 270:
        return "disseminating_moon", phase_angle
    elif phase_angle < 315:
        return "last_quarter", phase_angle
    else:
        return "balsamic_moon", phase_angle


def calculate_solar_return(natal_year, natal_month, natal_day, current_year, natal_sun_longitude, lat, lon, timezone_str="UTC"):
    """
    Calculate Solar Return chart - when Sun returns to exact natal position
    """
    # Start searching around birthday
    search_date = datetime(current_year, natal_month, natal_day, 12, 0, 0)
    tz = pytz.timezone(timezone_str)
    search_date = tz.localize(search_date)
    
    # Find exact moment Sun returns to natal position
    # Search +/- 2 days around birthday
    best_match = None
    smallest_diff = 360
    
    for hour_offset in range(-48, 49):  # Search 48 hours before and after
        test_date = search_date + timedelta(hours=hour_offset)
        utc_date = test_date.astimezone(pytz.UTC)
        
        jd = swe.julday(utc_date.year, utc_date.month, utc_date.day,
                       utc_date.hour + utc_date.minute/60.0)
        
        sun_result, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
        sun_long = sun_result[0]
        
        # Check how close to natal Sun position
        diff = abs(sun_long - natal_sun_longitude)
        if diff > 180:
            diff = 360 - diff
        
        if diff < smallest_diff:
            smallest_diff = diff
            best_match = test_date
    
    # Calculate full chart for Solar Return moment
    if best_match:
        return_positions = calculate_planetary_positions(
            best_match.year, best_match.month, best_match.day,
            best_match.hour, best_match.minute, 0, timezone_str
        )
        return_houses = calculate_houses(
            best_match.year, best_match.month, best_match.day,
            best_match.hour, best_match.minute, 0,
            lat, lon, timezone_str
        )
        return best_match, return_positions, return_houses
    
    return None, None, None


def calculate_progressions(natal_year, natal_month, natal_day, natal_hour, natal_minute, 
                          current_date, timezone_str="UTC"):
    """
    Calculate secondary progressions - 1 day = 1 year
    """
    # Calculate age
    birth_date = datetime(natal_year, natal_month, natal_day)
    age_years = (current_date - birth_date).days / 365.25
    
    # Progressed date = birth date + age in days
    progressed_date = birth_date + timedelta(days=age_years)
    
    # Calculate planetary positions for progressed date
    progressed_positions = calculate_planetary_positions(
        progressed_date.year, progressed_date.month, progressed_date.day,
        natal_hour, natal_minute, 0, timezone_str
    )
    
    return progressed_date, progressed_positions, age_years


def generate_synastry_reading(person1_positions, person2_positions, person1_sun_sign, person2_sun_sign, horoscope_db):
    """
    Generate full chart synastry between two people
    """
    reading = f"\n{'=' * 70}\n"
    reading += f"SYNASTRY ANALYSIS - Deep Chart Compatibility\n"
    reading += f"{person1_sun_sign} ♥ {person2_sun_sign}\n"
    reading += f"{'=' * 70}\n\n"
    
    reading += f"Beyond sun sign compatibility, here's how your complete charts interact:\n\n"
    
    # Find interaspects
    interaspects = []
    
    for p1_planet, p1_data in person1_positions.items():
        for p2_planet, p2_data in person2_positions.items():
            angle = calculate_aspect_angle(p1_data["longitude"], p2_data["longitude"])
            
            aspect_types = [
                ("conjunction", 0, 8),
                ("opposition", 180, 8),
                ("trine", 120, 8),
                ("square", 90, 8),
                ("sextile", 60, 6)
            ]
            
            for aspect_name, target_angle, orb in aspect_types:
                if abs(angle - target_angle) <= orb:
                    interaspects.append({
                        "person1_planet": p1_planet,
                        "person2_planet": p2_planet,
                        "aspect": aspect_name,
                        "angle": angle,
                        "orb": abs(angle - target_angle)
                    })
                    break
    
    # Sort by importance (closer orb = more important)
    interaspects.sort(key=lambda x: x["orb"])
    
    # Key synastry aspects to highlight
    important_combos = [
        ("Sun", "Moon"), ("Moon", "Sun"),
        ("Venus", "Mars"), ("Mars", "Venus"),
        ("Sun", "Venus"), ("Venus", "Sun"),
        ("Moon", "Venus"), ("Venus", "Moon")
    ]
    
    reading += f"**Most Significant Interaspects:**\n\n"
    
    shown = 0
    for aspect in interaspects:
        if shown >= 10:
            break
        
        p1 = aspect["person1_planet"]
        p2 = aspect["person2_planet"]
        asp = aspect["aspect"]
        
        is_important = (p1, p2) in important_combos
        
        if is_important:
            reading += f"⭐ "
        
        reading += f"**Your {p1} {asp} Their {p2}** ({aspect['angle']:.1f}°)\n"
        
        # Simplified interpretations
        if asp == "conjunction":
            reading += f"Your {p1} and their {p2} merge energies—you activate this in each other powerfully.\n"
        elif asp == "opposition":
            reading += f"Your {p1} and their {p2} create tension—you challenge each other in this area.\n"
        elif asp == "trine":
            reading += f"Your {p1} and their {p2} flow harmoniously—this comes naturally between you.\n"
        elif asp == "square":
            reading += f"Your {p1} and their {p2} create friction—you grow through this dynamic tension.\n"
        elif asp == "sextile":
            reading += f"Your {p1} and their {p2} offer opportunity—conscious effort enhances this connection.\n"
        
        reading += "\n"
        shown += 1
    
    if len(interaspects) > 10:
        reading += f"*Plus {len(interaspects) - 10} additional interaspects weaving your charts together.*\n\n"
    
    reading += f"{'=' * 70}\n"
    
    return reading


def predict_upcoming_transits(current_date, natal_positions, house_data, months_ahead=6):
    """
    Predict major transits coming in the next X months
    """
    predictions = []
    
    # Slow-moving planets to track (more significant transits)
    slow_planets = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    
    # Check each day for next 6 months
    for days_ahead in range(0, months_ahead * 30, 7):  # Check weekly
        future_date = current_date + timedelta(days=days_ahead)
        
        # Calculate planetary positions for that date
        future_positions = calculate_planetary_positions(
            future_date.year, future_date.month, future_date.day,
            12, 0, 0, "UTC"
        )
        
        # Check for exact aspects to natal chart
        for transit_planet in slow_planets:
            if transit_planet not in future_positions:
                continue
            
            for natal_planet, natal_data in natal_positions.items():
                angle = calculate_aspect_angle(
                    future_positions[transit_planet]["longitude"],
                    natal_data["longitude"]
                )
                
                # Check for exact aspects (within 1° orb)
                aspect_types = [
                    ("conjunction", 0, 1),
                    ("opposition", 180, 1),
                    ("trine", 120, 1),
                    ("square", 90, 1)
                ]
                
                for aspect_name, target_angle, orb in aspect_types:
                    if abs(angle - target_angle) <= orb:
                        natal_house = find_house_for_planet(natal_data["longitude"], house_data["cusps"])
                        
                        predictions.append({
                            "date": future_date,
                            "transit_planet": transit_planet,
                            "natal_planet": natal_planet,
                            "aspect": aspect_name,
                            "house": natal_house
                        })
    
    return predictions


def calculate_chiron(year, month, day, hour, minute, second, timezone_str="UTC"):
    """
    Calculate Chiron position (with error handling for missing ephemeris files)
    """
    try:
        tz = pytz.timezone(timezone_str)
        local_dt = tz.localize(datetime(year, month, day, hour, minute, second))
        utc_dt = local_dt.astimezone(pytz.UTC)
        
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                       utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)
        
        result, ret_flag = swe.calc_ut(jd, swe.CHIRON, swe.FLG_SWIEPH | swe.FLG_SPEED)
        longitude = result[0]
        sign = get_zodiac_sign(longitude)
        
        return {
            "sign": sign,
            "longitude": longitude,
            "degrees_in_sign": longitude % 30
        }
    except Exception as e:
        # If ephemeris files are missing, return None
        print(f"⚠ Chiron calculation requires additional ephemeris files. Skipping Chiron reading.")
        return None


def detect_fixed_star_conjunctions(natal_positions, house_data, horoscope_db):
    """
    Detect if any fixed stars conjunct natal planets or angles (within 1° orb)
    """
    conjunctions = []
    
    # Get fixed stars data
    stars = horoscope_db.get("natal_chart", {}).get("fixed_stars", {}).get("stars", {})
    
    # Check planets
    for planet, pos_data in natal_positions.items():
        planet_long = pos_data["longitude"]
        
        for star_name, star_data in stars.items():
            # Calculate star's absolute longitude
            star_sign = star_data["sign"]
            star_deg_in_sign = star_data["longitude"]
            
            # Convert to absolute longitude
            sign_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
            star_sign_index = sign_order.index(star_sign)
            star_absolute_long = star_sign_index * 30 + star_deg_in_sign
            
            # Check if within 1° orb
            diff = abs(planet_long - star_absolute_long)
            if diff > 180:
                diff = 360 - diff
            
            if diff <= 1.0:
                conjunctions.append({
                    "star": star_name,
                    "planet": planet,
                    "orb": diff,
                    "star_data": star_data
                })
    
    # Check angles (Ascendant, MC)
    asc_long = house_data["ascendant"]["longitude"]
    mc_long = house_data["midheaven"]["longitude"]
    
    for star_name, star_data in stars.items():
        star_sign = star_data["sign"]
        star_deg_in_sign = star_data["longitude"]
        sign_order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        star_sign_index = sign_order.index(star_sign)
        star_absolute_long = star_sign_index * 30 + star_deg_in_sign
        
        # Check Ascendant
        diff_asc = abs(asc_long - star_absolute_long)
        if diff_asc > 180:
            diff_asc = 360 - diff_asc
        
        if diff_asc <= 1.0:
            conjunctions.append({
                "star": star_name,
                "planet": "Ascendant",
                "orb": diff_asc,
                "star_data": star_data
            })
        
        # Check MC
        diff_mc = abs(mc_long - star_absolute_long)
        if diff_mc > 180:
            diff_mc = 360 - diff_mc
        
        if diff_mc <= 1.0:
            conjunctions.append({
                "star": star_name,
                "planet": "Midheaven",
                "orb": diff_mc,
                "star_data": star_data
            })
    
    return conjunctions


def check_void_of_course_moon(dt):
    """
    Check if Moon is currently void of course
    Returns (is_void, last_aspect_time, next_sign_change_time)
    """
    tz = pytz.UTC
    utc_dt = dt.astimezone(tz)
    
    # Get current Moon position
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                   utc_dt.hour + utc_dt.minute/60.0)
    
    moon_result, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)
    moon_long = moon_result[0]
    moon_speed = moon_result[3]  # degrees per day
    
    current_sign = get_zodiac_sign(moon_long)
    degrees_in_sign = moon_long % 30
    
    # Calculate when Moon changes sign
    degrees_to_next_sign = 30 - degrees_in_sign
    hours_to_next_sign = (degrees_to_next_sign / moon_speed) * 24
    next_sign_change = utc_dt + timedelta(hours=hours_to_next_sign)
    
    # Look back up to 12 hours to find last aspect
    last_aspect_time = None
    
    for hours_back in range(0, 13):
        check_time = utc_dt - timedelta(hours=hours_back)
        check_jd = swe.julday(check_time.year, check_time.month, check_time.day,
                             check_time.hour + check_time.minute/60.0)
        
        check_moon_result, _ = swe.calc_ut(check_jd, swe.MOON, swe.FLG_SWIEPH)
        check_moon_long = check_moon_result[0]
        check_moon_sign = get_zodiac_sign(check_moon_long)
        
        # If we've crossed into previous sign, stop searching
        if check_moon_sign != current_sign:
            break
        
        # Check if Moon made aspect to any planet at this time
        for planet_id in [swe.SUN, swe.MERCURY, swe.VENUS, swe.MARS, 
                         swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]:
            planet_result, _ = swe.calc_ut(check_jd, planet_id, swe.FLG_SWIEPH)
            planet_long = planet_result[0]
            
            angle = calculate_aspect_angle(check_moon_long, planet_long)
            
            # Check for major aspects
            aspect_angles = [0, 60, 90, 120, 180]
            for target_angle in aspect_angles:
                if abs(angle - target_angle) <= 1.0:  # Within 1° orb
                    if last_aspect_time is None or check_time > last_aspect_time:
                        last_aspect_time = check_time
    
    # Moon is VOC if last aspect was found and we haven't changed signs yet
    is_void = last_aspect_time is not None
    
    return is_void, last_aspect_time, next_sign_change


def calculate_relocation_chart(natal_year, natal_month, natal_day, natal_hour, natal_minute,
                               natal_tz, new_lat, new_lon, new_tz="UTC"):
    """
    Calculate relocated chart - natal planets with new location's houses
    Shows how chart manifests differently in a new place
    """
    # Natal planetary positions stay the same
    natal_positions = calculate_full_natal_chart(
        natal_year, natal_month, natal_day, natal_hour, natal_minute, 0,
        new_lat, new_lon, natal_tz  # Use birth time but new location
    )
    
    # Calculate houses for new location
    relocated_houses = calculate_houses(
        natal_year, natal_month, natal_day, natal_hour, natal_minute, 0,
        new_lat, new_lon, natal_tz
    )
    
    return natal_positions, relocated_houses


def get_sabian_symbol_degree(longitude):
    """
    Convert absolute longitude to Sabian Symbol degree (1-360)
    Sabian symbols round UP to the next degree
    """
    import math
    degree = math.ceil(longitude) 
    if degree == 0:
        degree = 360
    return degree

def get_sabian_interpretation(planet_name, longitude, horoscope_db):
    """
    Get Sabian Symbol for a specific degree
    """
    degree_num = get_sabian_symbol_degree(longitude)
    
    # Look up in database
    sabian_data = horoscope_db.get("natal_chart", {}).get("sabian_symbols", {})
    symbols = sabian_data.get("symbols", {})
    
    if str(degree_num) in symbols:
        return symbols[str(degree_num)]
    else:
        # Fallback (shouldn't happen since we have all 360!)
        sign = get_zodiac_sign(longitude)
        deg_in_sign = int(longitude % 30) + 1
        return {
            "sign": sign,
            "degree": deg_in_sign,
            "symbol": f"Degree {deg_in_sign} of {sign}",
            "interpretation": "This degree holds specific meaning in your chart."
        }


def calculate_asteroid(asteroid_number, year, month, day, hour, minute, second, timezone_str="UTC"):
    """
    Calculate asteroid position by parsing astorb.dat and computing from orbital elements
    This bypasses Swiss Ephemeris entirely for asteroids
    """
    import math
    
    try:
        # Convert to UTC and get Julian Date
        tz = pytz.timezone(timezone_str)
        local_dt = tz.localize(datetime(year, month, day, hour, minute, second))
        utc_dt = local_dt.astimezone(pytz.UTC)
        decimal_hour = utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_hour)
        
        # Parse astorb.dat to find this asteroid's orbital elements
        orbital_elements = parse_astorb_for_asteroid(asteroid_number, ephe_path)
        
        if not orbital_elements:
            return None
        
        # Calculate position from orbital elements
        longitude = calculate_position_from_elements(jd, orbital_elements)
        
        if longitude is None:
            return None
        
        # Normalize longitude to 0-360
        longitude = longitude % 360.0
        
        sign = get_zodiac_sign(longitude)
        
        return {
            "longitude": longitude,
            "sign": sign,
            "degrees_in_sign": longitude % 30,
            "speed": 0.0,  # We're not calculating speed for now
            "retrograde": False
        }
        
    except Exception as e:
        return None


def parse_astorb_for_asteroid(asteroid_number, ephe_path):
    """
    Parse astorb.dat to extract orbital elements for a specific asteroid
    Returns dict with orbital elements or None if not found
    """
    import os
    
    astorb_path = os.path.join(ephe_path, "astorb.dat")
    
    if not os.path.exists(astorb_path):
        return None
    
    try:
        with open(astorb_path, 'r', encoding='latin-1') as f:
            for line in f:
                if not line.strip():
                    continue
                
                if len(line) < 200:  # astorb.dat lines are ~267 chars
                    continue
                
                try:
                    # Parse asteroid number (columns 1-6)
                    num_str = line[0:6].strip()
                    num = int(num_str)
                    
                    if num == asteroid_number:
                        # Found our asteroid! Parse orbital elements
                        # Format based on astorb.dat specification
                        
                        # Epoch (columns 107-115) - Julian Date
                        epoch_str = line[106:115].strip()
                        epoch = float(epoch_str) if epoch_str else 2451545.0
                        
                        # Mean anomaly at epoch (columns 116-125) in degrees
                        mean_anom_str = line[115:125].strip()
                        mean_anomaly = float(mean_anom_str) if mean_anom_str else 0.0
                        
                        # Argument of perihelion (columns 126-135) in degrees
                        arg_peri_str = line[125:135].strip()
                        arg_perihelion = float(arg_peri_str) if arg_peri_str else 0.0
                        
                        # Longitude of ascending node (columns 136-145) in degrees
                        long_node_str = line[135:145].strip()
                        long_asc_node = float(long_node_str) if long_node_str else 0.0
                        
                        # Inclination (columns 146-155) in degrees
                        incl_str = line[145:155].strip()
                        inclination = float(incl_str) if incl_str else 0.0
                        
                        # Eccentricity (columns 70-79)
                        ecc_str = line[70:79].strip()
                        eccentricity = float(ecc_str) if ecc_str else 0.0
                        
                        # Semi-major axis (columns 92-103) in AU
                        a_str = line[92:103].strip()
                        semi_major_axis = float(a_str) if a_str else 1.0
                        
                        return {
                            'epoch': epoch,
                            'mean_anomaly': mean_anomaly,
                            'arg_perihelion': arg_perihelion,
                            'long_asc_node': long_asc_node,
                            'inclination': inclination,
                            'eccentricity': eccentricity,
                            'semi_major_axis': semi_major_axis
                        }
                
                except (ValueError, IndexError):
                    continue
        
        return None
        
    except Exception as e:
        return None


def calculate_position_from_elements(jd, elements):
    """
    Calculate ecliptic longitude from orbital elements
    Uses simplified Kepler orbital mechanics
    """
    import math
    
    try:
        # Extract elements
        epoch = elements['epoch']
        M0 = math.radians(elements['mean_anomaly'])
        omega = math.radians(elements['arg_perihelion'])
        Omega = math.radians(elements['long_asc_node'])
        i = math.radians(elements['inclination'])
        e = elements['eccentricity']
        a = elements['semi_major_axis']
        
        # Calculate mean motion (radians per day)
        # n = sqrt(k^2 / a^3) where k^2 = 0.01720209895^2 for AU and days
        k = 0.01720209895
        n = math.sqrt(k * k / (a * a * a))
        
        # Calculate mean anomaly at target date
        days_since_epoch = jd - epoch
        M = M0 + n * days_since_epoch
        M = M % (2 * math.pi)  # Normalize to 0-2pi
        
        # Solve Kepler's equation: E - e*sin(E) = M
        # Using Newton-Raphson iteration
        E = M  # Initial guess
        for iteration in range(10):  # 10 iterations is usually enough
            E_new = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
            if abs(E_new - E) < 1e-8:
                break
            E = E_new
        
        # Calculate true anomaly
        nu = 2 * math.atan2(
            math.sqrt(1 + e) * math.sin(E / 2),
            math.sqrt(1 - e) * math.cos(E / 2)
        )
        
        # Calculate distance from Sun
        r = a * (1 - e * math.cos(E))
        
        # Calculate heliocentric coordinates in orbital plane
        x_orb = r * math.cos(nu)
        y_orb = r * math.sin(nu)
        
        # Transform to ecliptic coordinates
        # First rotate by argument of perihelion
        x1 = x_orb * math.cos(omega) - y_orb * math.sin(omega)
        y1 = x_orb * math.sin(omega) + y_orb * math.cos(omega)
        z1 = 0.0
        
        # Then rotate by inclination
        x2 = x1
        y2 = y1 * math.cos(i)
        z2 = y1 * math.sin(i)
        
        # Finally rotate by longitude of ascending node
        x_ecl = x2 * math.cos(Omega) - y2 * math.sin(Omega)
        y_ecl = x2 * math.sin(Omega) + y2 * math.cos(Omega)
        z_ecl = z2
        
        # Calculate ecliptic longitude
        longitude = math.atan2(y_ecl, x_ecl)
        longitude = math.degrees(longitude)
        
        # Normalize to 0-360
        if longitude < 0:
            longitude += 360
        
        return longitude
        
    except Exception as e:
        return None

def search_astorb_for_names(search_term, ephe_path):
    """
    Search astorb.dat for asteroid names matching the search term
    Returns list of {name, number} dictionaries
    """
    import os
    
    astorb_path = os.path.join(ephe_path, 'astorb.dat')
    
    if not os.path.exists(astorb_path):
        print("⚠ astorb.dat not found. Using limited name database.")
        return []
    
    matches = []
    search_lower = search_term.lower().strip()
    
    try:
        with open(astorb_path, 'r', encoding='latin-1') as f:
            for line in f:
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Parse the line
                # Format: "     1 Ceres              ..."
                # Number is first 6 chars, name starts at char 7
                
                if len(line) < 20:
                    continue
                
                try:
                    # Extract number (first 6 chars, strip spaces)
                    num_str = line[0:6].strip()
                    asteroid_num = int(num_str)
                    
                    # Extract name (chars 7-25, strip spaces)
                    asteroid_name = line[7:25].strip()
                    
                    # Check if name matches search term
                    if search_lower in asteroid_name.lower():
                        matches.append({
                            "name": asteroid_name,
                            "number": asteroid_num
                        })
                        
                        # Limit to 10 matches to avoid overwhelming output
                        if len(matches) >= 10:
                            break
                            
                except (ValueError, IndexError):
                    continue
        
        return matches
        
    except Exception as e:
        print(f"⚠ Error reading astorb.dat: {e}")
        return []

def search_asteroid_by_name(search_name, ephe_path=None):
    """
    Search for asteroids by name - now searches astorb.dat dynamically!
    Falls back to hardcoded list if astorb.dat not available
    """
    if ephe_path:
        # Try searching astorb.dat first
        matches = search_astorb_for_names(search_name, ephe_path)
        if matches:
            return matches
    
    # Fallback to hardcoded names if astorb.dat search fails
    matches = []
    search_names_lower = search_name.lower().strip()
    
    # Existing hardcoded dictionary
    common_names = {
        # Male names
        "michael": 4793, "mike": 4793,
        "james": 2335, "jim": 2335, "jimmy": 2335,
        "john": 1583,
        "robert": 2071, "rob": 2071, "bob": 2071,
        "david": 2603, "dave": 2603,
        "william": 2866, "will": 2866, "bill": 2866,
        "richard": 3972, "rick": 3972, "dick": 3972,
        "joseph": 3556, "joe": 3556,
        "thomas": 2555, "tom": 2555,
        "charles": 2906, "charlie": 2906,
        "christopher": 4858, "chris": 4858,
        "daniel": 2504, "dan": 2504,
        "matthew": 10133, "matt": 10133,
        "anthony": 2404, "tony": 2404,
        "mark": 3791,
        "donald": 3395, "don": 3395,
        "steven": 3225, "steve": 3225,
        "paul": 3317,
        "andrew": 3671, "andy": 3671,
        "joshua": 6534, "josh": 6534,
        "kenneth": 3873, "ken": 3873,
        "kevin": 6913,
        "brian": 3225,
        "george": 2603,
        "edward": 3205, "ed": 3205, "eddie": 3205,
        "ronald": 3544, "ron": 3544,
        "timothy": 4655, "tim": 4655,
        "jason": 2335,
        "jeffrey": 21656, "jeff": 21656,
        "ryan": 5024,
        "jacob": 12524,
        "gary": 2700,
        "nicholas": 3937, "nick": 3937,
        "eric": 12796,
        "jonathan": 6446,
        "stephen": 3225,
        "larry": 12238,
        "justin": 3936,
        "scott": 2597,
        "brandon": 21656,
        "benjamin": 11548, "ben": 11548,
        "samuel": 3097, "sam": 3097,
        "frank": 2829,
        "gregory": 21656, "greg": 21656,
        "raymond": 2071,
        "alexander": 8966, "alex": 8966,
        "patrick": 1687, "pat": 1687,
        "jack": 5372,
        "dennis": 3214,
        "jerry": 3112,
        "tyler": 11548,
        "aaron": 3277,
        "henry": 3516,
        "douglas": 3873,
        "peter": 1987,
        "adam": 13070,
        "nathan": 12238,
        "zachary": 11548, "zach": 11548,
        "kyle": 21656,
        "walter": 1677,
        "harold": 2906,
        "jeremy": 21656,
        "ethan": 21656,
        "carl": 1727,
        "arthur": 2597,
        "terry": 3873,
        "joe": 3556,
        
        # Female names
        "mary": 2779,
        "patricia": 436, "pat": 436, "patty": 436,
        "jennifer": 6249, "jenny": 6249, "jen": 6249,
        "linda": 882,
        "barbara": 234, "barb": 234,
        "elizabeth": 412, "liz": 412, "beth": 412, "betty": 412,
        "susan": 793, "sue": 793,
        "jessica": 2239, "jess": 2239,
        "sarah": 1039, "sara": 1039,
        "karen": 1537,
        "nancy": 2870,
        "lisa": 3561,
        "betty": 2487,
        "margaret": 371, "maggie": 371, "meg": 371,
        "sandra": 1288, "sandy": 1288,
        "ashley": 2569,
        "kimberly": 2696, "kim": 2696,
        "emily": 291,
        "donna": 1323,
        "michelle": 1376,
        "carol": 2085,
        "amanda": 725,
        "melissa": 1390,
        "deborah": 1251, "debbie": 1251, "deb": 1251,
        "stephanie": 1277,
        "rebecca": 4713, "becky": 4713,
        "sharon": 1984,
        "laura": 952,
        "cynthia": 1143, "cindy": 1143,
        "kathleen": 2093, "kathy": 2093,
        "amy": 3375,
        "angela": 965,
        "shirley": 2441,
        "anna": 265,
        "brenda": 323,
        "pamela": 1939, "pam": 1939,
        "emma": 283,
        "nicole": 1547,
        "helen": 101,
        "samantha": 796, "sam": 796,
        "katherine": 2093, "kate": 2093, "katie": 2093,
        "christine": 1244, "chris": 1244,
        "debra": 1251,
        "rachel": 971,
        "catherine": 2093,
        "carolyn": 2085,
        "janet": 2301,
        "ruth": 1259,
        "maria": 170,
        "heather": 1092,
        "diane": 1376,
        "virginia": 50,
        "julie": 1192,
        "joyce": 1946,
        "victoria": 12,
        "olivia": 224,
        "kelly": 2907,
        "christina": 1244,
        "lauren": 9084,
        "joan": 1502,
        "evelyn": 715,
        "judith": 664,
        "megan": 2940,
        "cheryl": 1575,
        "andrea": 8955,
        "hannah": 1086,
        "jacqueline": 8558, "jackie": 8558,
        "martha": 205,
        "gloria": 294,
        "teresa": 295,
        "ann": 1087, "anne": 1087,
        "sara": 1039,
        "madison": 9387,
        "frances": 1015,
        "kathryn": 2093,
        "janice": 2301,
        "jean": 1815,
        "abigail": 21656,
        "sophia": 251,
        "grace": 2873,
        "denise": 1877,
        "judy": 2301,
        "christina": 1244,
        "rose": 223,
        "diana": 78,
        "brittany": 9502,
        "natalie": 1428,
        "danielle": 2700,
        "sophia": 251,
        "alexis": 2815,
        "lori": 3561,
        
        # Mythological
        "apollo": 1862,
        "athena": 881,
        "zeus": 5731,
        "hera": 103,
        "artemis": 105,
        "aphrodite": 1388,
        "hermes": 69230,
        "ares": 2174,
        "hades": 27928,
        "poseidon": 4341,
        "demeter": 1108,
        "hestia": 46,
        "dionysus": 3671,
        "persephone": 399,
        "hecate": 100,
        "pan": 4450,
        "prometheus": 1809,
        "orpheus": 3361,
        "medusa": 149,
        "pandora": 55,
        "europa": 52,
        "io": 85,
        "ganymede": 1036,
        "selene": 580,
        "helios": 895,
        "eos": 221,
        "nyx": 3908,
        "gaia": 1184,
        "uranus": 2207,
        "kronos": 10811,
        "rhea": 577,
        "titan": 1809,
        "atlas": 1198,
        "hercules": 532,
        "perseus": 9876,
        "theseus": 1841,
        "jason": 2335,
        "achilles": 588,
        "hector": 624,
        "odysseus": 1143,
        "penelope": 201,
        "helen": 101,
        "paris": 3317,
        "cassandra": 114,
        "electra": 130,
        "orion": 1327,
        "andromeda": 31,
        "pegasus": 1620
    }
    
    if search_name_lower in common_names:
        matches.append({
            "name": search_name.title(),
            "number": common_names[search_name_lower]
        })
    
    return matches

def calculate_major_asteroids(year, month, day, hour, minute, second, lat, lon, timezone_str="UTC"):
    """
    Calculate the Big 6 asteroids
    """
    major_numbers = {
        "Ceres": 1,
        "Pallas": 2,
        "Juno": 3,
        "Vesta": 4,
        "Eros": 433,
        "Psyche": 16
    }
    
    asteroids = {}
    
    for name, number in major_numbers.items():
        position = calculate_asteroid(number, year, month, day, hour, minute, second, timezone_str)
        if position:
            asteroids[name] = position
    
    return asteroids


def scan_thematic_asteroids(natal_positions, house_data, theme, year, month, day, hour, minute, second, timezone_str):
    """
    Calculate all asteroids in a thematic group and check for aspects to natal planets
    """
    thematic_asteroids = {
        "love_and_romance": {433: "Eros", 763: "Cupido", 1221: "Amor", 447: "Valentine", 80: "Sappho", 1388: "Aphrodite"},
        "career_and_success": {19: "Fortuna", 151: "Abundantia"},
        "spiritual_and_karmic": {3811: "Karma", 128: "Nemesis", 896: "Sphinx"},
        "healing": {10: "Hygiea", 2878: "Panacea"},
        "creative_arts": {7: "Iris", 22: "Kalliope", 27: "Euterpe", 62: "Erato", 81: "Terpsichore"}
    }
    
    if theme not in thematic_asteroids:
        return []
    
    results = []
    
    for ast_num, ast_name in thematic_asteroids[theme].items():
        ast_pos = calculate_asteroid(ast_num, year, month, day, hour, minute, second, timezone_str)
        
        if not ast_pos:
            continue
        
        # Check for conjunctions to natal planets (within 3° orb)
        for planet_name, planet_data in natal_positions.items():
            angle_diff = calculate_aspect_angle(ast_pos["longitude"], planet_data["longitude"])
            
            if angle_diff <= 3:  # Conjunction
                results.append({
                    "asteroid_name": ast_name,
                    "asteroid_number": ast_num,
                    "asteroid_position": ast_pos,
                    "natal_planet": planet_name,
                    "aspect": "conjunction",
                    "orb": angle_diff
                })
    
    return results


def main():
    """Main function"""
    # Load horoscope database
    horoscope_db = load_horoscope_database()
    
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
    
    # Ask about compatibility analysis
    print("\n" + "=" * 70)
    print("COMPATIBILITY ANALYSIS (Optional)")
    print("-" * 70)
    do_compatibility = input("Would you like relationship compatibility analysis? (y/n): ").lower().strip()
    
    partner_sun_sign = None
    if do_compatibility == 'y':
        print("\nEnter your partner's (or potential partner's) Sun sign:")
        print("Options:", ", ".join(ZODIAC_SIGNS))
        partner_input = input("Partner's Sun sign: ").strip().title()
        
        if partner_input in ZODIAC_SIGNS:
            partner_sun_sign = partner_input
        else:
            print(f"⚠ '{partner_input}' not recognized. Skipping compatibility analysis.")

    # Ask about natal chart reading
    print("\n" + "=" * 70)
    print("NATAL CHART READING (Optional)")
    print("-" * 70)
    do_natal = input("Would you like a full natal chart reading? (y/n): ").lower().strip()

    # Ask about transits
    print("\n" + "=" * 70)
    print("TRANSIT ANALYSIS (Optional)")
    print("-" * 70)
    do_transits = input("Would you like to see how current planets affect YOUR birth chart? (y/n): ").lower().strip()
    
    # Ask about synastry
    print("\n" + "=" * 70)
    print("SYNASTRY - FULL CHART COMPATIBILITY (Optional)")
    print("-" * 70)
    do_synastry = input("Would you like deep chart compatibility with someone? (y/n): ").lower().strip()
    
    synastry_partner_data = None
    if do_synastry == 'y':
        print("\nEnter partner's birth information:")
        p_year = int(input("Partner birth year: "))
        p_month = int(input("Partner birth month (1-12): "))
        p_day = int(input("Partner birth day: "))
        p_hour = int(input("Partner birth hour (0-23): "))
        p_minute = int(input("Partner birth minute (0-59): "))
        
        # Ask for partner's location
        print("\n🌍 PARTNER'S BIRTH LOCATION")
        print("-" * 70)
        partner_location = input("Partner's birth city/location: ").strip()
        
        p_lat, p_lon, p_address = geocode_location(partner_location)
        
        # Fallback to manual if needed
        if p_lat is None or p_lon is None:
            print("\n⚠ Geocoding failed. Using your birth location for partner.")
            p_lat, p_lon = birth_lat, birth_lon
        
        p_tz = input("Partner's birth timezone (e.g., UTC, Europe/London): ").strip() or birth_tz
        
        synastry_partner_data = {
            "year": p_year,
            "month": p_month,
            "day": p_day,
            "hour": p_hour,
            "minute": p_minute,
            "lat": p_lat,
            "lon": p_lon,
            "tz": p_tz
        }

    # Ask about Solar Return
    print("\n" + "=" * 70)
    print("SOLAR RETURN - YOUR YEAR AHEAD (Optional)")
    print("-" * 70)
    print("Calculate your 'birthday chart' for this year - reveals themes from")
    print("your last birthday to your next birthday.")
    do_solar_return = input("Would you like your Solar Return chart? (y/n): ").lower().strip()
    
    # Ask about Progressions
    print("\n" + "=" * 70)
    print("SECONDARY PROGRESSIONS - INNER DEVELOPMENT (Optional)")
    print("-" * 70)
    print("Shows your psychological/spiritual age and internal development themes.")
    do_progressions = input("Would you like your progressed chart? (y/n): ").lower().strip()
    
    # Ask about Relocation
    print("\n" + "=" * 70)
    print("RELOCATION CHART - ASTROCARTOGRAPHY (Optional)")
    print("-" * 70)
    print("See how your chart would manifest in a different location.")
    do_relocation = input("Would you like a relocation chart? (y/n): ").lower().strip()
    
    relocation_data = None
    if do_relocation == 'y':
        print("\nEnter the location you're considering or currently living in:")
        reloc_location = input("Location (city, country): ").strip()
        
        reloc_lat, reloc_lon, reloc_address = geocode_location(reloc_location)
        
        if reloc_lat is None or reloc_lon is None:
            print("⚠ Could not find location. Skipping relocation chart.")
            do_relocation = 'n'
        else:
            print(f"✓ Found: {reloc_address}")
            reloc_tz = input("Timezone for this location (or press Enter to use your birth timezone): ").strip() or birth_tz
            
            relocation_data = {
                "lat": reloc_lat,
                "lon": reloc_lon,
                "tz": reloc_tz,
                "location": reloc_address
            }

    # Ask about Major Asteroids
    print("\n" + "=" * 70)
    print("MAJOR ASTEROIDS (Optional)")
    print("-" * 70)
    print("Calculate the Big 6 asteroids: Ceres, Pallas, Juno, Vesta, Eros, Psyche")
    do_major_asteroids = input("Would you like major asteroid placements? (y/n): ").lower().strip()
    
    # Ask about Personal Name Asteroids
    print("\n" + "=" * 70)
    print("PERSONAL NAME ASTEROID FINDER (Optional)")
    print("-" * 70)
    print("Search for asteroids named after you or loved ones!")
    do_name_search = input("Would you like to search for name asteroids? (y/n): ").lower().strip()

    search_name = []  # Initialize the list!

    if do_name_search == 'y':
        print("\nEnter names to search for (press Enter when done):")
        while True:
            name = input("Name (or press Enter to finish): ").strip()
            if not name:
                break
            search_name.append(name)
    
    print(f"\n✓ Collected {len(search_name)} names to search\n")

    # Ask about Thematic Asteroid Scanning
    print("\n" + "=" * 70)
    print("THEMATIC ASTEROID SCANNER (Optional)")
    print("-" * 70)
    print("Scan asteroids in specific themes (love, career, spiritual, etc.)")
    print("and see which ones aspect your natal planets!")
    do_thematic = input("Would you like thematic asteroid scanning? (y/n): ").lower().strip()
    
    selected_themes = []
    if do_thematic == 'y':
        print("\nAvailable themes:")
        print("1. Love & Romance")
        print("2. Career & Success")
        print("3. Spiritual & Karmic")
        print("4. Healing")
        print("5. Creative Arts")
        print("A. All themes")
        
        theme_choice = input("\nSelect themes (1-5, A for all, or comma-separated): ").strip().upper()
        
        if theme_choice == 'A':
            selected_themes = ["love_and_romance", "career_and_success", "spiritual_and_karmic", "healing", "creative_arts"]
        else:
            theme_map = {
                "1": "love_and_romance",
                "2": "career_and_success",
                "3": "spiritual_and_karmic",
                "4": "healing",
                "5": "creative_arts"
            }
            for choice in theme_choice.replace(",", " ").split():
                if choice in theme_map:
                    selected_themes.append(theme_map[choice])

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

    # Generate natal chart reading if requested
    if do_natal == 'y':
        print("\n⏳ Calculating natal chart...")
        natal_chart_positions = calculate_full_natal_chart(
            natal_year, natal_month, natal_day, natal_hour, natal_minute, 0,
            birth_lat, birth_lon, birth_tz
        )
        
        natal_reading = generate_natal_chart_reading(
            natal_chart_positions, house_data, horoscope_db
        )
        print(natal_reading)
        
        # ADD CHIRON READING (separate from main chart)
        print("\n⏳ Calculating Chiron placement...")
        chiron_data = calculate_chiron(
            natal_year, natal_month, natal_day, natal_hour, natal_minute, 0, birth_tz
        )
        
        if chiron_data:
            chiron_sign = chiron_data["sign"]
            chiron_deg = chiron_data["degrees_in_sign"]
            
            chiron_desc = horoscope_db.get("natal_chart", {}).get("chiron", {}).get("description", "")
            chiron_interp = horoscope_db.get("natal_chart", {}).get("chiron", {}).get("chiron_in_sign", {}).get(
                chiron_sign, "Chiron in this sign indicates a unique wound and healing gift."
            )
            
            print(f"\n{'=' * 70}")
            print(f"CHIRON - YOUR WOUND AND HEALING GIFT")
            print(f"{'=' * 70}\n")
            print(f"{chiron_desc}\n")
            print(f"**Chiron in {chiron_sign}** ({chiron_deg:.1f}°)\n")
            print(f"{chiron_interp}\n")
            print(f"{'=' * 70}\n")

        # FIXED STARS
        print("\n⏳ Checking for fixed star conjunctions...")
        fixed_star_conjunctions = detect_fixed_star_conjunctions(
            natal_chart_positions, house_data, horoscope_db
        )
        
        if fixed_star_conjunctions:
            print(f"\n{'=' * 70}")
            print(f"FIXED STARS - Ancient Celestial Influences")
            print(f"{'=' * 70}\n")
            
            stars_desc = horoscope_db.get("natal_chart", {}).get("fixed_stars", {}).get("description", "")
            print(f"{stars_desc}\n")
            
            for conjunction in fixed_star_conjunctions:
                star_name = conjunction["star"]
                planet = conjunction["planet"]
                orb = conjunction["orb"]
                star_data = conjunction["star_data"]
                
                keywords = star_data.get("keywords", "")
                interpretation = star_data.get("interpretation", "")
                
                print(f"**{star_name} conjunct {planet}** (within {orb:.2f}°)")
                print(f"*{keywords}*\n")
                print(f"{interpretation}\n")
            
            print(f"{'=' * 70}\n")
        else:
            print("ℹ No major fixed star conjunctions found in your chart (within 1° orb).\n")

        # SABIAN SYMBOLS
        print("\n⏳ Calculating Sabian Symbols for key placements...")
        
        print(f"\n{'=' * 70}")
        print(f"SABIAN SYMBOLS - The Oracular Degrees")
        print(f"{'=' * 70}\n")
        
        sabian_desc = horoscope_db.get("natal_chart", {}).get("sabian_symbols", {}).get(
            "description", "Each of the 360 degrees has a unique symbolic meaning."
        )
        print(f"{sabian_desc}\n")
        
        print(f"**Your Key Degree Meanings:**\n")
        # SABIAN SYMBOLS
        print("\n⏳ Calculating Sabian Symbols for key placements...")
        
        print(f"\n{'=' * 70}")
        print(f"SABIAN SYMBOLS - The Oracular Degrees")
        print(f"{'=' * 70}\n")
        
        sabian_desc = horoscope_db.get("natal_chart", {}).get("sabian_symbols", {}).get(
            "description", "Each of the 360 degrees has a unique symbolic meaning."
        )
        print(f"{sabian_desc}\n")
        
        print(f"**Your Key Degree Meanings:**\n")
        
        # CREATE THE KEY_POINTS LIST HERE (THIS WAS MISSING!)
        key_points = [
            ("Sun", natal_chart_positions["Sun"]["longitude"], "Your core identity and life purpose"),
            ("Moon", natal_chart_positions["Moon"]["longitude"], "Your emotional nature and instincts"),
            ("Ascendant", house_data["ascendant"]["longitude"], "How you approach life and are seen by others"),
            ("Mercury", natal_chart_positions["Mercury"]["longitude"], "Your thinking and communication style"),
            ("Venus", natal_chart_positions["Venus"]["longitude"], "Your love nature and values")
        ]
        
        # NOW ITERATE THROUGH IT
        for point_name, longitude, meaning in key_points:
            sabian = get_sabian_interpretation(point_name, longitude, horoscope_db)
            
            # Calculate exact degree position
            sign = sabian["sign"]
            degree = sabian["degree"]
            
            print(f"**{point_name} at {sign} {degree}°**")
            print(f"*{meaning}*")
            print(f"**Symbol:** {sabian['symbol']}")
            print(f"{sabian['interpretation']}\n")
        
        print(f"{'=' * 70}\n")
        
        for planet_name, planet_data in natal_chart_positions.items():
            longitude = planet_data["longitude"]
            sign = planet_data["sign"]
            
            sabian = get_sabian_interpretation(planet_name, longitude, horoscope_db)
            
            print(f"**{planet_name} at {sign} {sabian['degree']}°**")
            print(f"*Symbol:* {sabian['symbol']}")
            print(f"{sabian['interpretation']}\n")

        # Show Sabian for ALL planets
        print(f"**Sabian Symbols for Each Natal Planet:**\n")
        
        # Also show Ascendant and Midheaven
        asc_sabian = get_sabian_interpretation("Ascendant", house_data["ascendant"]["longitude"], horoscope_db)
        print(f"**Ascendant at {house_data['ascendant']['sign']} {asc_sabian['degree']}°**")
        print(f"*Symbol:* {asc_sabian['symbol']}")
        print(f"{asc_sabian['interpretation']}\n")
        
        mc_sabian = get_sabian_interpretation("Midheaven", house_data["midheaven"]["longitude"], horoscope_db)
        print(f"**Midheaven at {house_data['midheaven']['sign']} {mc_sabian['degree']}°**")
        print(f"*Symbol:* {mc_sabian['symbol']}")
        print(f"{mc_sabian['interpretation']}\n")
        
        for point_name, longitude, meaning in key_points:
            sabian = get_sabian_interpretation(point_name, longitude, horoscope_db)
            
            # Calculate exact degree position
            sign = sabian["sign"]
            degree = sabian["degree"]
            
            print(f"**{point_name} at {sign} {degree}°**")
            print(f"*{meaning}*")
            print(f"**Symbol:** {sabian['symbol']}")
            print(f"{sabian['interpretation']}\n")
        
        print(f"{'=' * 70}\n")

        # ADD LUNAR PHASE
        lunar_phase, phase_angle = calculate_lunar_phase_at_birth(natal_chart_positions)
        phase_info = horoscope_db.get("natal_chart", {}).get("lunar_phases", {}).get(lunar_phase, {})
        
        print(f"\n{'=' * 70}")
        print(f"LUNAR PHASE AT BIRTH")
        print(f"{'=' * 70}\n")
        print(f"**{phase_info.get('phase', 'Unknown')}** ({phase_angle:.1f}° from Sun)")
        print(f"*{phase_info.get('keywords', '')}*\n")
        print(f"{phase_info.get('interpretation', '')}\n")
        print(f"{'=' * 70}\n")
    
    # TRANSITS TO NATAL CHART
    if do_transits == 'y' and do_natal == 'y':
        print("\n⏳ Calculating transits to your natal chart...")
        
        transits = calculate_transits_to_natal(current_positions, natal_chart_positions, house_data, horoscope_db)
        
        print(f"\n{'=' * 70}")
        print(f"CURRENT TRANSITS TO YOUR NATAL CHART")
        print(f"How Today's Planets Affect Your Birth Chart")
        print(f"{'=' * 70}\n")
        
        if transits:
            print("**Active Transits Right Now:**\n")
            
            for transit in transits[:10]:  # Show top 10
                trans_planet = transit["transiting_planet"]
                natal_planet = transit["natal_planet"]
                aspect = transit["aspect"]
                house = transit["natal_house"]
                
                # Get interpretation
                transit_interp = horoscope_db.get("natal_chart", {}).get("transits", {}).get(aspect, {}).get(
                    trans_planet, f"This transit activates your natal {natal_planet}."
                )
                
                print(f"**{trans_planet} {aspect.title()} Natal {natal_planet}** (House {house})")
                print(f"{transit_interp}\n")
            
            if len(transits) > 10:
                print(f"*Plus {len(transits) - 10} additional transits shaping your current experience.*\n")
        else:
            print("No major transits are exact at this moment.\n")
        
        print(f"{'=' * 70}\n")
        
        # UPCOMING TRANSITS
        print("\n⏳ Calculating upcoming major transits...")
        
        upcoming = predict_upcoming_transits(datetime.now(), natal_chart_positions, house_data, months_ahead=6)
        
        if upcoming:
            print(f"\n{'=' * 70}")
            print(f"UPCOMING MAJOR TRANSITS - Next 6 Months")
            print(f"{'=' * 70}\n")
            
            for prediction in upcoming[:8]:  # Show top 8
                date = prediction["date"].strftime("%B %d, %Y")
                trans = prediction["transit_planet"]
                natal = prediction["natal_planet"]
                aspect = prediction["aspect"]
                house = prediction["house"]
                
                print(f"**{date}**: {trans} {aspect.title()} Natal {natal} (House {house})")
            
            print(f"\n{'=' * 70}\n")

    # ADD MAJOR ASTEROIDS
    if do_major_asteroids == 'y':
        print("\n⏳ Calculating major asteroids...")
        
        major_asteroids = calculate_major_asteroids(
            natal_year, natal_month, natal_day, natal_hour, natal_minute, 0,
            birth_lat, birth_lon, birth_tz
        )
        
        asteroid_desc = horoscope_db.get("natal_chart", {}).get("asteroids", {}).get(
            "description", "Asteroids add nuanced archetypal energies to your chart."
        )
        print(f"{asteroid_desc}\n")

        major_data = horoscope_db.get("natal_chart", {}).get("asteroids", {}).get("major_asteroids", {})

        # for ast_name, ast_position in major_asteroids.items():
        #     print(f"\n🔍 DEBUG: Processing {ast_name}")
        #     print(f"Position data: {ast_position}")

        #     sign = ast_position["sign"]
        #     degree = ast_position["degrees_in_sign"]
        #     retro = " ℞" if ast_position["retrograde"] else ""
        #     house = find_house_for_planet(ast_position["longitude"], house_data["cusps"])

        #     print(f"Sign: {sign}, Degree: {degree:.1f}, House: {house}")

    # Major asteroid search results
    if do_major_asteroids == 'y':
        print("\n⏳ Calculating major asteroids...")
        major_asteroids = calculate_major_asteroids(natal_year, natal_month, natal_day, natal_hour, natal_minute, 0, birth_lat, birth_lon, birth_tz)

        print("\n" + "=" * 70)
        print("MAJOR ASTEROIDS - The Big 6")
        print("=" * 70 + "\n")

        # Get description from JSON
        asteroid_desc = horoscope_db.get("natal_chart", {}).get("asteroids", {}).get("description", "")
        print(f"{asteroid_desc}\n\n")

        major_data = horoscope_db.get("natal_chart", {}).get("asteroids", {}).get("major_asteroids", {})
    
    for ast_name, ast_position in major_asteroids.items():
        sign = ast_position["sign"]
        degree = ast_position["degrees_in_sign"]
        retro = " ℞" if ast_position["retrograde"] else ""
        house = find_house_for_planet(ast_position["longitude"], house_data["cusps"])
        
        print(f"**{ast_name}** in {sign} {degree:.1f}°{retro} (House {house})")
        
        # Find the asteroid data in JSON by number
        asteroid_numbers = {"Ceres": "1", "Pallas": "2", "Juno": "3", "Vesta": "4", "Eros": "433", "Psyche": "16"}
        ast_num = asteroid_numbers.get(ast_name, "")
        
        if ast_num and ast_num in major_data:
            ast_info = major_data[ast_num]
            
            # Get general interpretation
            general_interp = ast_info.get("interpretation", "")
            if general_interp:
                print(f"  {general_interp}")
            
            # Get sign-specific interpretation
            sign_interps = ast_info.get("in_signs", {})
            sign_interp = sign_interps.get(sign, "")
            if sign_interp:
                print(f"  In {sign}: {sign_interp}")
        
        # Add house meaning
        house_meaning = HOUSE_MEANINGS.get(house, {}).get("description", "")
        if house_meaning:
            print(f"  In your {house}th house, this energy focuses on {house_meaning}.\n")
        else:
            print()
    
    print("=" * 70 + "\n")



    # ADD THEMATIC ASTEROID SCANNER
    # if do_thematic == 'y' and selected_themes == 'y':
        # print("\n⏳ Scanning thematic asteroids...")
        # 
        # print(f"\n{'=' * 70}")
        # print(f"THEMATIC ASTEROID SCAN")
        # print(f"{'=' * 70}\n")
        # 
        # thematic_info = horoscope_db.get("natal_chart", {}).get("asteroids", {}).get("thematic_groups", {})
        # 
        # for theme in selected_themes:
            # theme_data = thematic_info.get(theme, {})
            # theme_name = theme.replace("_", " ").title()
            # theme_desc = theme_data.get("description", "")
            # 
            # print(f"**{theme_name}**")
            # if theme_desc:
                # print(f"{theme_desc}")
            # print()
            # 
            # Scan this theme
            # results = scan_thematic_asteroids(
                # natal_chart_positions, house_data, theme,
                # natal_year, natal_month, natal_day, natal_hour, natal_minute, 0, birth_tz
            # )
            # 
            # if results:
                # print(f"🌟 **Active Asteroid Conjunctions:**\n")
                # for result in results:
                    # ast_name = result["asteroid_name"]
                    # natal_planet = result["natal_planet"]
                    # orb = result["orb"]
                    # ast_sign = result["asteroid_position"]["sign"]
                    # 
                    # print(f"• **{ast_name}** conjunct **{natal_planet}** (within {orb:.1f}°)")
                    # print(f"  {ast_name} in {ast_sign} merges with your natal {natal_planet}")
                    # print(f"  This amplifies {theme_name.lower()} energy through {natal_planet}!\n")
            # else:
                # print(f"No exact conjunctions found for {theme_name.lower()} asteroids.\n")
            # 
            # print()
        # 
        # print(f"{'=' * 70}\n")

    # Named asteroid search results
    if search_name:
        print("\n" + "=" * 70)
        print("PERSONAL NAME ASTEROIDS")
        print("=" * 70 + "\n")
    
    for search_name in search_name:
        print(f"🔍 Searching for '{search_name}'...")
        matches = search_asteroid_by_name(search_name, ephe_path)
        
        if matches:
            print(f"✓ Found {len(matches)} match(es):\n")
            
            for match in matches[:5]:  # Limit to top 5 to avoid overwhelming output
                match_name = match["name"]
                match_num = match["number"]
                
                print(f"  **{match_name}** (#{match_num})")
                
                # CALCULATE THE ACTUAL POSITION
                pos = calculate_asteroid(int(match_num), natal_year, natal_month, natal_day, natal_hour, natal_minute, 0, birth_tz)
                
                if pos:
                    house = find_house_for_planet(pos["longitude"], house_data["cusps"])
                    retro = " ℞" if pos["retrograde"] else ""
                    print(f"    ↳ {pos['sign']} {pos['degrees_in_sign']:.1f}°{retro} in House {house}")
                    
                    # Add house-based meaning
                    house_info = HOUSE_MEANINGS.get(house, {})
                    house_name = house_info.get("name", "this area")
                    house_desc = house_info.get("description", "this life area")
                    
                    print(f"    Your personal asteroid '{match_name}' connects your identity to {house_desc}.")
                    print(f"    This placement in your {house}th house of {house_name} suggests a deep soul connection to this life area.\n")
                else:
                    print(f"    ↳ Position could not be calculated (not found in ephemeris data)\n")
            
            if len(matches) > 5:
                print(f"    ... and {len(matches) - 5} more matches\n")
        else:
            print(f"✗ No asteroids found matching '{search_name}'\n")
    
    print("=" * 70 + "\n")


    # THEMATIC SCAN RESULTS  
    if selected_themes:
        print("\n======================================================================")
        print("THEMATIC ASTEROID SCAN")
        print("======================================================================\n")

    if selected_themes:
        print("\n" + "=" * 70)
        print("THEMATIC ASTEROID SCAN")
        print("=" * 70 + "\n")
    
    # CALCULATE NATAL POSITIONS FOR ASPECT CHECKING
    natal_chart_positions = calculate_full_natal_chart(natal_year, natal_month, natal_day, natal_hour, natal_minute, 0, birth_lat, birth_lon, birth_tz)
    
    themes_data = horoscope_db.get("natal_chart", {}).get("asteroids", {}).get("major_asteroids", {}).get("16", {}).get("thematic_groups", {})
    
    for theme_key in selected_themes:
        theme_info = themes_data.get(theme_key, {})
        theme_desc = theme_info.get("description", f"Asteroids for theme: {theme_key}")
        
        print(f"🔮 {theme_desc}\n")
        
        theme_asteroids = theme_info.get("asteroids", {})
        
        if theme_asteroids:
            found_any = False
            
            for ast_num_str, ast_desc in theme_asteroids.items():
                ast_num = int(ast_num_str)
                
                # Calculate the asteroid position
                ast_pos = calculate_asteroid(ast_num, natal_year, natal_month, natal_day, natal_hour, natal_minute, 0, birth_tz)
                
                if ast_pos:
                    found_any = True
                    house = find_house_for_planet(ast_pos["longitude"], house_data["cusps"])
                    retro = " ℞" if ast_pos["retrograde"] else ""
                    
                    print(f"  **{ast_desc}**")
                    print(f"    ↳ {ast_pos['sign']} {ast_pos['degrees_in_sign']:.1f}°{retro} in House {house}")
                    
                    # Check for conjunctions to natal planets
                    aspects_found = []
                    # Try this first - most likely:
                    # Maybe it's called this:
                    for planet_name, planet_data in natal_chart_positions.items():
                        angle_diff = calculate_aspect_angle(ast_pos["longitude"], planet_data["longitude"])
                        if angle_diff <= 3:  # Tight 3° conjunction
                            aspects_found.append(f"conjunct your natal {planet_name}")
                    
                    if aspects_found:
                        print(f"    ✨ {', '.join(aspects_found)} - highly significant!")
                    
                    # Add house meaning
                    house_info = HOUSE_MEANINGS.get(house, {})
                    if house_info:
                        print(f"    This asteroid activates your {house}th house of {house_info.get('description', 'life')}.")
                    
                    print()
            
            if not found_any:
                print(f"  (No asteroids in this theme could be calculated from available data)\n")
        else:
            print(f"  (Theme data not available in database)\n")
        
        print()
    
    print("=" * 70 + "\n")

    # SYNASTRY
    if do_synastry == 'y' and synastry_partner_data:
        print("\n⏳ Calculating synastry...")
        
    # SYNASTRY
    if do_synastry == 'y' and synastry_partner_data:
        print("\n⏳ Calculating synastry...")
        
        # Calculate partner's chart
        partner_positions = calculate_full_natal_chart(
            synastry_partner_data["year"],
            synastry_partner_data["month"],
            synastry_partner_data["day"],
            synastry_partner_data["hour"],
            synastry_partner_data["minute"],
            0, 
            synastry_partner_data["lat"],
            synastry_partner_data["lon"],
            synastry_partner_data["tz"]
        )
        
        partner_sun_sign, _ = calculate_natal_positions(
            synastry_partner_data["year"],
            synastry_partner_data["month"],
            synastry_partner_data["day"],
            synastry_partner_data["hour"],
            synastry_partner_data["minute"],
            0, 
            synastry_partner_data["tz"]
        )
        
        synastry_reading = generate_synastry_reading(
            natal_chart_positions, partner_positions,
            natal_sun_sign, partner_sun_sign, horoscope_db
        )
        
        print(synastry_reading)

    # ADD SOLAR RETURN
    if do_solar_return == 'y':
        print("\n⏳ Calculating Solar Return chart...")
        
        # Get natal Sun longitude for reference
        natal_sun_long = natal_chart_positions["Sun"]["longitude"]
        
        # Calculate for most recent birthday year
        current_year = datetime.now().year
        
        # If birthday hasn't happened yet this year, use last year
        birthday_this_year = datetime(current_year, natal_month, natal_day)
        if datetime.now() < birthday_this_year:
            solar_return_year = current_year - 1
        else:
            solar_return_year = current_year
        
        sr_date, sr_positions, sr_houses = calculate_solar_return(
            natal_year, natal_month, natal_day, solar_return_year,
            natal_sun_long, birth_lat, birth_lon, birth_tz
        )
        
        if sr_date and sr_positions and sr_houses:
            print(f"\n{'=' * 70}")
            print(f"SOLAR RETURN CHART - YOUR YEAR AHEAD")
            print(f"Chart for {sr_date.strftime('%B %d, %Y at %I:%M %p %Z')}")
            print(f"Valid from Birthday {solar_return_year} to Birthday {solar_return_year + 1}")
            print(f"{'=' * 70}\n")
            
            sr_desc = horoscope_db.get("natal_chart", {}).get("solar_return", {}).get(
                "interpretation", 
                "Your Solar Return chart shows the themes and energies of your current year."
            )
            print(f"{sr_desc}\n")
            
            # Show Solar Return Ascendant
            sr_asc_sign = sr_houses["ascendant"]["sign"]
            print(f"**Solar Return Ascendant: {sr_asc_sign}**")
            print(f"This year, you approach life through the lens of {sr_asc_sign}.\n")
            
            # Show key Solar Return planets
            print(f"**Key Solar Return Placements:**\n")
            
            key_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
            for planet in key_planets:
                if planet in sr_positions:
                    sign = sr_positions[planet]["sign"]
                    house = find_house_for_planet(sr_positions[planet]["longitude"], sr_houses["cusps"])
                    print(f"• **{planet} in {sign}, House {house}**: This year, {planet.lower()} energy manifests through {sign} in your {house}th house area of life.")
            
            print(f"\n**Interpretation:**")
            print(f"Houses activated this year show where you'll experience the most growth and activity.")
            print(f"Planets in angular houses (1st, 4th, 7th, 10th) indicate major themes.\n")
            
            # Count planets in houses for emphasis
            from collections import Counter
            sr_house_count = Counter()
            for planet, pos_data in sr_positions.items():
                house = find_house_for_planet(pos_data["longitude"], sr_houses["cusps"])
                sr_house_count[house] += 1
            
            if sr_house_count:
                most_populated = sr_house_count.most_common(3)
                print(f"**House Emphasis This Year:**")
                for house, count in most_populated:
                    if count > 1:
                        house_meanings = {
                            1: "self, identity, new beginnings",
                            2: "money, values, resources",
                            3: "communication, learning, siblings",
                            4: "home, family, roots",
                            5: "creativity, romance, children",
                            6: "work, health, service",
                            7: "partnerships, relationships",
                            8: "transformation, shared resources",
                            9: "travel, philosophy, expansion",
                            10: "career, public life, achievement",
                            11: "friends, groups, aspirations",
                            12: "spirituality, endings, unconscious"
                        }
                        meaning = house_meanings.get(house, "this life area")
                        print(f"• **House {house}** ({count} planets): Focus on {meaning}")
            
            print(f"\n{'=' * 70}\n")
        else:
            print("⚠ Could not calculate Solar Return. Please check your birth data.\n")
    
    # ADD PROGRESSIONS
    if do_progressions == 'y':
        print("\n⏳ Calculating Secondary Progressions...")
        
        prog_date, prog_positions, age_years = calculate_progressions(
            natal_year, natal_month, natal_day, natal_hour, natal_minute,
            datetime.now(), birth_tz
        )
        
        if prog_date and prog_positions:
            print(f"\n{'=' * 70}")
            print(f"SECONDARY PROGRESSIONS - YOUR INNER DEVELOPMENT")
            print(f"Progressed Date: {prog_date.strftime('%B %d, %Y')}")
            print(f"Your Age: {int(age_years)} years")
            print(f"{'=' * 70}\n")
            
            prog_desc = horoscope_db.get("natal_chart", {}).get("progressions", {}).get(
                "interpretation",
                "Secondary progressions show your psychological development."
            )
            print(f"{prog_desc}\n")
            
            print(f"**Key Progressed Placements:**\n")
            
            # Show progressed vs natal for key planets
            inner_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
            
            for planet in inner_planets:
                if planet in prog_positions and planet in natal_chart_positions:
                    prog_sign = prog_positions[planet]["sign"]
                    natal_sign = natal_chart_positions[planet]["sign"]
                    
                    prog_long = prog_positions[planet]["longitude"]
                    natal_long = natal_chart_positions[planet]["longitude"]
                    
                    # Calculate how much planet has progressed
                    progression = (prog_long - natal_long) % 360
                    
                    if prog_sign != natal_sign:
                        print(f"• **Progressed {planet} in {prog_sign}** (natal {natal_sign})")
                        print(f"  Your internal {planet.lower()} energy has matured into {prog_sign} qualities.")
                    else:
                        print(f"• **Progressed {planet} in {prog_sign}** (still in natal sign)")
                        print(f"  Progressed {progression:.1f}° from natal position - deepening natal themes.")
                    print()
            
            # Highlight progressed Moon (moves fastest)
            if "Moon" in prog_positions:
                prog_moon_sign = prog_positions["Moon"]["sign"]
                print(f"**Progressed Moon in {prog_moon_sign}:**")
                print(f"Your emotional needs and security focus are currently colored by {prog_moon_sign}.")
                print(f"The progressed Moon changes signs roughly every 2.5 years, showing evolving emotional themes.\n")
            
            print(f"{'=' * 70}\n")
    
    # ADD RELOCATION CHART
    if do_relocation == 'y' and relocation_data == 'y':
        print("\n⏳ Calculating Relocation chart...")
        
        reloc_positions, reloc_houses = calculate_relocation_chart(
            natal_year, natal_month, natal_day, natal_hour, natal_minute,
            birth_tz, relocation_data["lat"], relocation_data["lon"], relocation_data["tz"]
        )
        
        print(f"\n{'=' * 70}")
        print(f"RELOCATION CHART - ASTROCARTOGRAPHY")
        print(f"Your Chart in: {relocation_data['location']}")
        print(f"{'=' * 70}\n")
        
        print(f"Your natal planets remain the same, but the HOUSES change in a new location.")
        print(f"This shows how different life areas become emphasized depending on where you live.\n")
        
        # Compare birth and relocation Ascendants
        birth_asc = house_data["ascendant"]["sign"]
        reloc_asc = reloc_houses["ascendant"]["sign"]
        
        print(f"**Birth Ascendant:** {birth_asc}")
        print(f"**Relocation Ascendant:** {reloc_asc}\n")
        
        if birth_asc != reloc_asc:
            print(f"Your rising sign changes to {reloc_asc} in this location!")
            print(f"You would be perceived differently and approach life through a new lens here.\n")
        else:
            print(f"Your rising sign remains {reloc_asc} - your outer personality is similar here.\n")
        
        # Show how natal planets fall in different houses
        print(f"**How Your Natal Planets Shift Houses:**\n")
        
        for planet in ["Sun", "Moon", "Mercury", "Venus", "Mars"]:
            if planet in natal_chart_positions:
                birth_house = find_house_for_planet(
                    natal_chart_positions[planet]["longitude"], 
                    house_data["cusps"]
                )
                reloc_house = find_house_for_planet(
                    natal_chart_positions[planet]["longitude"], 
                    reloc_houses["cusps"]
                )
                
                if birth_house != reloc_house:
                    print(f"• **{planet}**: Moves from House {birth_house} → House {reloc_house}")
                    
                    # Simplified house meanings
                    house_keywords = {
                        1: "identity/self", 2: "money/values", 3: "communication/learning",
                        4: "home/family", 5: "creativity/romance", 6: "work/health",
                        7: "relationships", 8: "transformation/intimacy", 9: "travel/philosophy",
                        10: "career/public life", 11: "friends/groups", 12: "spirituality/unconscious"
                    }
                    
                    from_area = house_keywords.get(birth_house, "this area")
                    to_area = house_keywords.get(reloc_house, "this area")
                    
                    print(f"  {planet} energy shifts from {from_area} to {to_area}")
                else:
                    print(f"• **{planet}**: Remains in House {birth_house}")
        
        print(f"\n**Interpretation:**")
        print(f"In {relocation_data['location']}, life themes and opportunities manifest through different areas.")
        print(f"Consider which house placements align better with your goals and desired lifestyle.\n")
        
        print(f"{'=' * 70}\n")

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
    
    # VOID OF COURSE MOON CHECK
    print("\n⏳ Checking if Moon is Void of Course...")
    is_void, last_aspect, next_sign = check_void_of_course_moon(datetime.now())
    
    print(f"\n{'=' * 70}")
    print(f"VOID OF COURSE MOON")
    print(f"{'=' * 70}\n")
    
    voc_desc = horoscope_db.get("natal_chart", {}).get("void_of_course_moon", {}).get("description", "")
    voc_advice = horoscope_db.get("natal_chart", {}).get("void_of_course_moon", {}).get("advice", "")
    
    if is_void:
        print("⚠ **The Moon is currently VOID OF COURSE**\n")
        if last_aspect:
            print(f"Last aspect was at: {last_aspect.strftime('%I:%M %p %Z')}")
        print(f"Moon enters next sign at: {next_sign.strftime('%I:%M %p %Z on %B %d')}\n")
        print(f"{voc_desc}\n")
        print(f"**Advice:** {voc_advice}\n")
    else:
        print("✓ The Moon is NOT void of course right now.\n")
        print(f"Moon enters next sign at: {next_sign.strftime('%I:%M %p %Z on %B %d')}\n")
        print("This is a good time for initiating important matters.\n")
    
    print(f"{'=' * 70}\n")

    # Generate compatibility reading if requested
    if partner_sun_sign:
        compatibility_reading = generate_compatibility_reading(
            natal_sun_sign, partner_sun_sign, current_positions, horoscope_db
        )
        print(compatibility_reading)
    
    # Generate personalized reading
    print("\n" + "=" * 70)
    print("YOUR PERSONALIZED ASTROLOGICAL READING")
    print("=" * 70)
    
    reading = generate_personalized_reading(
        current_positions, house_data, natal_sun_sign, natal_moon_sign, horoscope_db
    )
    
    print(f"\n{reading}\n")
    print("=" * 70)
    
    # ADD THIS AT THE VERY END:
    input("\n\nPress ENTER to exit...")


if __name__ == "__main__":
    main()
