#!/usr/bin/env python3
"""
Advanced Astrological Position Calculator with Compatibility Analysis
Full natal chart, transits, and relationship compatibility
"""

import swisseph as swe
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import json
import random
import os
import sys

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
    Generate comprehensive natal chart reading
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
    
    # Core planets (Sun, Moon, Mercury, Venus, Mars)
    reading += f"**Core Planetary Placements:**\n\n"
    
    core_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
    for planet in core_planets:
        if planet in natal_positions:
            pos = natal_positions[planet]
            sign = pos["sign"]
            house_num = find_house_for_planet(pos["longitude"], house_data["cusps"])
            retro = " ℞" if pos["retrograde"] else ""
            
            # Get interpretation from database
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
        reading += f"You were born with {len(natal_retrogrades)} planet(s) in retrograde motion, indicating areas of internalized development:\n\n"
        
        for planet in natal_retrogrades:
            retro_interp = horoscope_db.get("natal_chart", {}).get("natal_retrograde", {}).get(
                planet, f"{planet} retrograde at birth indicates internal processing of this planetary energy."
            )
            reading += f"• **{planet} Retrograde**: {retro_interp}\n\n"
    
    # Aspects
    aspects = detect_aspects(natal_positions)
    
    if aspects:
        reading += f"**Major Aspects in Your Chart:**\n\n"
        reading += f"Aspects reveal how different parts of your personality interact:\n\n"
        
        # Group by aspect type
        aspects_by_type = {}
        for aspect in aspects:
            aspect_type = aspect["type"]
            if aspect_type not in aspects_by_type:
                aspects_by_type[aspect_type] = []
            aspects_by_type[aspect_type].append(aspect)
        
        for aspect_type, aspect_list in aspects_by_type.items():
            aspect_info = horoscope_db.get("natal_chart", {}).get("aspects", {}).get(aspect_type, {})
            description = aspect_info.get("description", f"{aspect_type.title()} aspect")
            interpretation = aspect_info.get("interpretation", "These planets interact.")
            
            reading += f"**{aspect_type.title()}** - {description}\n"
            reading += f"{interpretation}\n"
            
            for aspect in aspect_list[:3]:  # Limit to 3 per type
                reading += f"  • {aspect['planet1']} {aspect_type} {aspect['planet2']} ({aspect['angle']:.1f}°)\n"
            
            if len(aspect_list) > 3:
                reading += f"  • ...and {len(aspect_list) - 3} more {aspect_type} aspects\n"
            
            reading += "\n"
    
    reading += f"{'=' * 70}\n"
    
    return reading


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
        
        # Calculate natal planetary positions
        natal_chart_positions = calculate_full_natal_chart(
            natal_year, natal_month, natal_day, natal_hour, natal_minute, 0,
            birth_lat, birth_lon, birth_tz
        )
        
        natal_reading = generate_natal_chart_reading(
            natal_chart_positions, house_data, horoscope_db
        )
        print(natal_reading)


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
