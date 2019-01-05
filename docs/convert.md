# z!convert

``z!convert`` converts between units of measurement. The command is formatted:
```
z!convert <number> <unit1...> to <unit2...>
```
This returns a measurement in ``<unit2>`` equivalent to ``<number>`` ``<unit1>``. The command can also be formatted:
```
z!convert <number> <unit...>
```
If you don't include the word ``to``, everything after the number is read as one unit. This returns a measurement in the opposite system (metric to US, anything else to metric) equivalent to ``<number>`` ``<unit>``.

## Units
You can either use the full name of the unit, or the abbreviation. Abbreviations are case-sensitive.
### Length
#### Metric
``meter`` or ``metre`` with any SI prefix, abbreviated as ``m``.
#### Imperial / US
``inch``/``in`` (2.54 cm); ``foot``/``ft`` (12 in); ``yard``/``yd`` (3 ft); ``fathom``/``ftm`` (6 ft); ``mile``/``mi`` (5280 ft)
#### Other
``astronomical unit``/``au``/``AU``/``ua`` (149,597,870,700 m)

### Mass
#### Metric
``gram`` or ``gramme`` with any SI prefix, abbreviated as ``g``; ``tonne``/``metric ton`` (1000 kg)
#### Imperial / US
``ounce``/``oz`` (1/16 lb); ``pound``/``lb`` (453.59237 g); ``stone``/``st`` (14 lb); ``hundredweight``/``cwt`` (100 lb); ``short ton``/``ton`` (2000 lb); ``long ton`` (2240 lb)
#### Other
``atomic mass unit``/``amu``/``u`` (1.660539040 yg); ``dalton`` (1 amu) with any SI prefix, abbreviated as ``Da``

### Volume
#### Metric
``liter`` or ``litre`` with any SI prefix, abbreviated as ``L`` or ``l``.
#### US
The US system is [pretty different](https://en.wikipedia.org/wiki/Comparison_of_the_imperial_and_US_customary_measurement_systems) from the imperial system; all of these measurements are specifically American. Imperial measurements maaaay be added at some point. These are also all liquid volumes.

``teaspoon``/``tsp`` (4.92892159375 mL); ``tablespoon``/``tbsp`` (3 tsp); ``fluid ounce``/``fl oz`` (2 tbsp); ``cup``/``c`` (8 fl oz); ``pint``/``pt`` (2 c); ``quart``/``qt`` (2 pt); ``gallon``/``gal`` (4 qt); ``barrel``/``bbl`` (31 1/2 gal); ``hogshead`` (63 gal)
