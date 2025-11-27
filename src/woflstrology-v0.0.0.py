#!/usr/bin/env python3
"""
Astrological Position Calculator
Calculates Sun, Moon, and planetary positions with retrograde detection
"""

import swisseph as swe
from datetime import datetime
import pytz

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

# Astrological significance patterns
PORTENTOUS_CONDITIONS = {
    "Mercury retrograde": lambda pos: pos["planet"] == "Mercury" and pos["retrograde"],
    "Mars retrograde": lambda pos: pos["planet"] == "Mars" and pos["retrograde"],
    "Venus retrograde": lambda pos: pos["planet"] == "Venus" and pos["retrograde"],
    "Saturn retrograde": lambda pos: pos["planet"] == "Saturn" and pos["retrograde"],
}


def get_zodiac_sign(longitude):
    """Convert ecliptic longitude to zodiac sign"""
    sign_num = int(longitude / 30.0)
    return ZODIAC_SIGNS[sign_num % 12]


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
        # Calculate position with speed flag
        result, ret_flag = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
        
        longitude = result[0]  # Ecliptic longitude
        speed = result[3]      # Daily motion (speed)
        
        sign = get_zodiac_sign(longitude)
        is_retrograde = speed < 0  # Negative speed = retrograde
        
        positions[planet_name] = {
            "planet": planet_name,
            "sign": sign,
            "longitude": longitude,
            "speed": speed,
            "retrograde": is_retrograde,
            "degrees_in_sign": longitude % 30
        }
    
    swe.close()
    return positions


def detect_portentous_conditions(positions):
    """Detect astrologically significant conditions"""
    conditions = []
    
    for planet_name, pos_data in positions.items():
        for condition_name, condition_func in PORTENTOUS_CONDITIONS.items():
            if condition_func(pos_data):
                conditions.append({
                    "type": condition_name,
                    "planet": planet_name,
                    "sign": pos_data["sign"]
                })
    
    # Check for planetary alignments in same sign
    signs_with_planets = {}
    for planet_name, pos_data in positions.items():
        sign = pos_data["sign"]
        if sign not in signs_with_planets:
            signs_with_planets[sign] = []
        signs_with_planets[sign].append(planet_name)
    
    # Multiple planets in one sign is considered significant
    for sign, planets in signs_with_planets.items():
        if len(planets) >= 3:
            conditions.append({
                "type": "stellium",
                "planets": planets,
                "sign": sign
            })
    
    return conditions


def generate_reading(positions, portentous_conditions):
    """Generate conversational astrological reading"""
    moon_sign = positions["Moon"]["sign"]
    sun_sign = positions["Sun"]["sign"]
    
    # Build the main statement
    reading = f"Your Moon is in {moon_sign}"
    
    # Add contrasting Sun position
    if sun_sign != moon_sign:
        reading += f" whilst the Sun is in {sun_sign}"
    else:
        reading += f" along with the Sun"
    
    # Add portentous conditions
    if portentous_conditions:
        reading += ", and "
        
        condition_descriptions = []
        for condition in portentous_conditions:
            if condition["type"] == "stellium":
                planets_str = ", ".join(condition["planets"])
                condition_descriptions.append(
                    f"there is a stellium of {planets_str} in {condition['sign']}"
                )
            elif "retrograde" in condition["type"]:
                condition_descriptions.append(
                    f"{condition['planet']} is in retrograde in {condition['sign']}"
                )
        
        reading += ", ".join(condition_descriptions)
    
    # Add interpretation based on Moon/Sun relationship
    reading += ". This means that "
    
    if moon_sign == sun_sign:
        reading += "your emotional nature and core identity are aligned, creating inner harmony and clarity of purpose"
    else:
        # Get elements
        moon_element = get_element(moon_sign)
        sun_element = get_element(sun_sign)
        
        if moon_element == sun_element:
            reading += "your emotions and identity share the same elemental nature, creating a natural flow between inner and outer self"
        else:
            reading += f"your {moon_element} Moon and {sun_element} Sun create a dynamic interplay between emotional needs and conscious expression"
    
    # Add retrograde interpretations
    retrogrades = [c for c in portentous_conditions if "retrograde" in c.get("type", "")]
    if retrogrades:
        reading += ". Additionally, "
        for retro in retrogrades:
            planet = retro["planet"]
            if planet == "Mercury":
                reading += "with Mercury retrograde, expect communication delays and technological hiccups - a time for review rather than new beginnings"
            elif planet == "Mars":
                reading += "Mars retrograde suggests channeling energy inward, focusing on strategic planning rather than direct action"
            elif planet == "Venus":
                reading += "Venus retrograde indicates a period of reassessing relationships and values"
    
    reading += "."
    
    return reading


def get_element(sign):
    """Get the element of a zodiac sign"""
    fire_signs = ["Aries", "Leo", "Sagittarius"]
    earth_signs = ["Taurus", "Virgo", "Capricorn"]
    air_signs = ["Gemini", "Libra", "Aquarius"]
    water_signs = ["Cancer", "Scorpio", "Pisces"]
    
    if sign in fire_signs:
        return "Fire"
    elif sign in earth_signs:
        return "Earth"
    elif sign in air_signs:
        return "Air"
    elif sign in water_signs:
        return "Water"
    return "Unknown"


def main():
    """Main function - run astrological calculation"""
    # Get current date/time or use custom
    print("=" * 60)
    print("ASTROLOGICAL POSITION CALCULATOR")
    print("=" * 60)
    
    use_current = input("\nUse current date/time? (y/n): ").lower().strip()
    
    if use_current == 'y':
        now = datetime.now()
        year, month, day = now.year, now.month, now.day
        hour, minute, second = now.hour, now.minute, now.second
        timezone_str = "UTC"
    else:
        year = int(input("Enter year: "))
        month = int(input("Enter month (1-12): "))
        day = int(input("Enter day: "))
        hour = int(input("Enter hour (0-23): "))
        minute = int(input("Enter minute (0-59): "))
        second = 0
        timezone_str = input("Enter timezone (e.g., UTC, America/New_York, Europe/London): ").strip() or "UTC"
    
    print(f"\nCalculating for: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} {timezone_str}")
    print("-" * 60)
    
    # Calculate positions
    positions = calculate_planetary_positions(year, month, day, hour, minute, second, timezone_str)
    
    # Display all planetary positions
    print("\n📍 PLANETARY POSITIONS:")
    print("-" * 60)
    for planet, data in positions.items():
        retro_marker = " ℞" if data["retrograde"] else ""
        print(f"{planet:12s}: {data['sign']:12s} ({data['degrees_in_sign']:.2f}°){retro_marker}")
    
    # Detect portentous conditions
    portentous = detect_portentous_conditions(positions)
    
    if portentous:
        print("\n⚠️  PORTENTOUS CONDITIONS:")
        print("-" * 60)
        for condition in portentous:
            if condition["type"] == "stellium":
                planets_str = ", ".join(condition["planets"])
                print(f"• Stellium in {condition['sign']}: {planets_str}")
            else:
                print(f"• {condition['type'].title()}")
    
    # Generate and display reading
    print("\n" + "=" * 60)
    print("ASTROLOGICAL READING")
    print("=" * 60)
    reading = generate_reading(positions, portentous)
    print(f"\n{reading}\n")
    print("=" * 60)


if __name__ == "__main__":
    main()
