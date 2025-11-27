woflStrology Changelog
This changelog tracks major changes for the woflStrology repository, which hosts:



woflstrology-vX.X.X:

v0.0.0:	initial tells moon, sun and any relevant planetary positions.

v0.0.1:	more specific retrograde info specific to a given starsign/house.

v0.0.2:	auto gen location cords lat/long and starsign/house etc.

v0.0.3: altered advices to be less predictive an more widely applicapble

v0.0.4:	added general horoscope based on sunsign that draws on a `.json` db

v0.0.5:	added compatibility analyser with update to db to add various advices on potential partnerships based on potentials sun sign.

:: [test executables created using GitHub actions workflow to distribute to test subject for feedback - needed macOS and Linux versions hence use of workflows]

v0.0.6:	Added natal chart reading option

v0.0.7:	Added expanded 'Aspect' meaning readings

v0.0.8:	Fixed output of Aspect readings to display properly full info and extended to all Aspects not just 10

v0.0.9:	Added synastry and some of the extra natal stuff as it affects present time

v0.1.0:	Added even more natal stuff and also the remaining moon phase etc.

v0.2.0:	Added chiron and fixed stars

v0.2.1:	Added extra stuff on Solar Return, Progressions, and Relocation

v0.2.2:	Initial works on gittin asteroids in places as the grand finale data source!	

v0.3.x:	[From about 0.2.4 thru 0.3.3 was just many iterations of failing gradually improving the process of getting asteroid recognition/data thru/comment etc.]

v0.3.4:	Of note because it's the advent of a whole new tack - trying  to parse astorb.dat ourselves, then calc our own asateroid positions...

v0.3.5:	Reverted to trying to get the swisseph files and then a selection of various methods to dl the full 620k+

v0.3.6:	Ended up settling on using astorb.dat as a name db, swisseph files for the theme and main asteroids and then abandoning specific accuracy on named asteroids.

v0.4.0:	Added silly jonk planets/hypothetical planets/Hamburg and Uranian Astrology objects etc. - a bit of fun to round off a near complete project.

fin.



initial 202511262304

* initiated repo

* Added project meta files:
CHANGELOG.md (this file)
CODE\_OF\_CONDUCT.md
CONTRIBUTING.md
LICENSE.md
README.md
SECURITY.md

requirements.txt


* created:
src/
docs/ClaudeSonnet4.5-prompt.md
venv/  # environment for deps


* at 202511262327 added
horoscope/database.json


* at 202511271341 added 
src/ephe/  # for files relating to asteroid and plaetary/orbital object data


* at 20251127
dist/  # for files pertaining to executables for the various OS platforms


* at 20251127
`icons/`icon_gen.py/icon files/`png/`  # for icons addition to executables
