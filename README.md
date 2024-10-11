# rspredict
The Grand Exchange is an in-player marketplace for Runescape 3 and Old School Runescape players to sell and purchase in-game items.
Not only is it often used to sell and purchase valuable gear, but it also serves as a speculative platform for merchanting/flipping (for a more formal explanation, see [the Runescape wiki's page](https://runescape.wiki/w/Trading_and_merchanting_guide)).

**rspredict** is intended to:
1) Simplify the gathering and transformation of Grand Exchange price data.
2) Assist with predictively modeling Runescape item prices.

## Components
### rspredict.data.datarequester
Retrieves price data for various Runescape items and item categories. Enriches data with differenced and moving averaged prices, and social media update information.
