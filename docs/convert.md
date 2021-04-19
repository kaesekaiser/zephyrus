This file extensively covers the usage of two closely related Zephyrus functions: `z!tconvert`, which converts between temperature systems, and `z!convert`, which converts between most other forms of measurement.

# z!tconvert
`z!tconvert` converts between units of temperature. The command is formatted:
``
z!tconvert <number> <unit1> to <unit2>
``
This returns a temperature in `<unit2>` equivalent to `<number>` degrees `<unit1>`. The command can also be formatted:
``
z!tconvert <number> <unit>
``
This returns a temperature in the opposite system (Celsius to Fahrenheit, anything else to Celsius) equivalent to `<number>` degrees `<unit>`.

## Units
`tconv` works with Celsius (°C), Fahrenheit (°F), Kelvin (K), and Rankine (°R). You can either use the full name of the unit, or the abbreviation, with or without the degree symbol.

# z!convert
`z!convert` converts between units of measurement *other than temperature* in much the same way as `z!tconvert`. The command is formatted:
``
z!convert <number> <unit1...> to <unit2...>
``
This returns a measurement in `<unit2>` equivalent to `<number>` `<unit1>`. The command can also be formatted:
``
z!convert <number> <unit...>
``
If you don't include the word `to`, everything after the number is read as one unit. This returns a measurement in the opposite system (metric to US, anything else to metric) equivalent to `<number>` `<unit>`.

`z!convert` works with most [SI (International System) units](https://en.wikipedia.org/wiki/International_System_of_Units#Units_and_prefixes), along with their US counterparts. It also allows for combinations of these units (for example, meters per second); for more on this, see the section [Combining Units](#combining-units).

## Base Units
You can either use the full name of the unit, or the abbreviation. Abbreviations are case-sensitive.
### Length
#### Metric
`meter` or `metre` with any [SI prefix](https://en.wikipedia.org/wiki/Metric_prefix#List_of_SI_prefixes), abbreviated as `m`.
#### Imperial / US
`inch`/`in` (2.54 cm); `foot`/`ft` (12 in); `yard`/`yd` (3 ft); `fathom`/`ftm` (6 ft); `mile`/`mi` (5280 ft)
#### Other
`astronomical unit`/`au`/`AU`/`ua` (149,597,870,700 m)

### Mass
#### Metric
`gram` or `gramme` with any SI prefix, abbreviated as `g`; `tonne`/`metric ton` (1000 kg)
#### Imperial / US
`ounce`/`oz` (1/16 lb); `pound`/`lb` (453.59237 g); `stone`/`st` (14 lb); `hundredweight`/`cwt` (100 lb); `short ton`/`ton` (2000 lb); `long ton` (2240 lb)
#### Other
`atomic mass unit`/`amu`/`u` (1.660539040 yg); `dalton` (1 amu) with any SI prefix, abbreviated as `Da`

### Time
#### Metric
`second` with any SI prefix, abbreviated as `s` or `sec`.
#### Other
`minute`/`min` (60 s); `hour`/`hr` (60 min); `day`/`d` (24 hr); `week`/`wk` (7 d); `year` (365 d) with any SI prefix, abbreviated as `yr`.

### Current
`ampere` or `amp` with any SI prefix, abbreviated as `A`.

## Named Derived Units
### Area
#### Metric
`are` (100 m<sup>2</sup>) with any SI prefix, abbreviated as `a`.
#### US
`acre`/`ac` (1/640 mi<sup>2</sup> or 0.40468564224 ha).

### Volume
#### Metric
`liter` or `litre` (0.001 m<sup>3</sup>) with any SI prefix, abbreviated as `L` or `l`.
#### US
The US system is [pretty different](https://en.wikipedia.org/wiki/Comparison_of_the_imperial_and_US_customary_measurement_systems) from the imperial system; all of these measurements are specifically American. Imperial measurements maaaay be added at some point. These are also all liquid volumes.

`teaspoon`/`tsp` (4.92892159375 mL); `tablespoon`/`tbsp` (3 tsp); `fluid ounce`/`fl oz` (2 tbsp); `cup`/`c` (8 fl oz); `pint`/`pt` (2 c); `quart`/`qt` (2 pt); `gallon`/`gal` (4 qt); `barrel`/`bbl` (31 1/2 gal); `hogshead` (63 gal).

### Frequency
`hertz` (1 s<sup>-1</sup>) with any SI prefix, abbreviated as `Hz`.

### Force
#### Metric
`newton` (1 kg\*m/s<sup>2</sup>) with any SI prefix, abbreviated as `N`.
#### US
`pound-force`/`lbf` (4.448222 N).

### Pressure
#### Metric
`pascal` (1 kg/m\*s<sup>2</sup> or 1 N/m<sup>2</sup>) with any SI prefix, abbreviated as `Pa`; `bar` (100000 Pa) with any SI prefix.
#### US
`psi` (1 lb/in<sup>2</sup> or 6894.75729 Pa).
#### Other
`atmosphere`/`atm` (101325 Pa); `torr` (1/760 atm); `mm Hg`/`mmHg` (133.322387 Pa); `in Hg`/`inHg` (25.4 mm Hg).

### Energy
Also torque, technically.
#### Metric
`joule` (1 kg\*m<sup>2</sup>/s<sup>2</sup> or 1 N\*m) with any SI prefix, abbreviated as `J`.
#### Other
`electronvolt`/`electron-volt` (1.602176634e-19 J) with any SI prefix, abbreviated as `eV`.

### Power
`watt` (1 kg\*m<sup>2</sup>/s<sup>3</sup> or 1 J/s) with any SI prefix, abbreviated as `W`.

Gonna be honest, 90% of the reason I added any of the below units was to help with my physics homework.

### Electric Charge
#### Metric
`coulomb` (1 A\*s) with any SI prefix, abbreviated as `C`.
#### Other
`e` (1.602176634e-19 C).

### Electric Potential
`volt` (1 kg\*m<sup>2</sup>/A\*s<sup>3</sup> or 1 J/C) with any SI prefix, abbreviated as `V`.

### Capacitance
`farad` (1 s<sup>4</sup>\*A<sup>2</sup>/kg\*m<sup>2</sup> or 1 C/V) with any SI prefix, abbreviated as `F`.

### Resistance
`ohm` (1 kg\*m<sup>2</sup>/A<sup>2</sup>\*s<sup>3</sup> or 1 V/A) with any SI prefix, abbreviated as `Ω`.

### Electric Conductance
`siemens` (1 A<sup>2</sup>\*s<sup>3</sup>/kg\*m<sup>2</sup> or 1 Ω<sup>-1</sup>) with any SI prefix, abbreviated as `S`.

### Magnetic Flux
`weber` (1 kg\*m<sup>2</sup>/A\*s<sup>2</sup> or 1 V\*s) with any SI prefix, abbreviated as `Wb`.

### Magnetic Flux Density
`tesla` (1 kg/A\*s<sup>2</sup> or 1 Wb/m<sup>2</sup>) with any SI prefix, abbreviated as `T`.

### Inductance
`henry` (1 kg\*m<sup>2</sup>/A<sup>2</sup>\*s<sup>2</sup> or 1 V\*s/A) with any SI prefix, abbreviated as `H`.

## Combining Units
Any of the above units can be combined, in literally any permutation, to perform more complex conversions. For example:
```
z!conv 1 mi/hr to km/hr
> 1.61 km/hr
```
If you are combining multiple units in this form, please specify a unit or combination of units to convert to (i.e. do not simply input `z!conv 1 mi/hr`). There is no easy way to assume the best combination of units for a value. Also, assure that the units on both sides of the conversion are in fact equivalent (i.e. `z!conv 1 mi/hr to kg` will obviously not work).

### Formatting
A combined unit first has to be made up of valid units in Zephyrus's system, of course. Units may be multiplied together using an asterisk `*`, raised to an integer power with a carat `^`, and divided using a forward slash `/`. There is no need for parentheses; please do not use them. There can be only *one* forward slash in an input; instead of using `m/s/s`, use `m/s^2`. Everything on the right side of the slash will be read as the denominator of the unit, and everything on the left will be read as the numerator (i.e. the input `kg*m/s` is equivalent to a `kg*m` over a `s`, and the input `kg/m*s` is equivalent to a `kg` over a `m*s`).

A complex and valid, if nonsensical, combined unit may look something like `kg^2*m^3/ft*s^2*A`:

![the above formula](https://cdn.discordapp.com/attachments/328642054055788565/833508158546378772/latex.png)

## Converting to Base Units
Finally, `z!conv` also includes an option to convert a unit or combination of units into its base SI unit(s). This may be useful if you need to know the definition of a unit like the joule or ohm, or if you have a weird grouping of units you need to simplify down. Instead of providing a unit to convert to, use the word `base` as the `<unit2>` argument (e.g. `z!conv 1 J to base` > `1 kg*m^2/s^2`).
