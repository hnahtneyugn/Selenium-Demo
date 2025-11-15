
A demo application using Selenium to crawl data from a website. This demo is done in Brave Browser, by using Chromedriver with Brave binary.

Websites to crawl:
- https://quotes.toscrape.com/
- https://books.toscrape.com/

**NOTE**: Prices and ratings of books were randomly assigned and have no real meaning.

Data crawled is in the `data` folder, while log files are in the `logs` folder.

## Quotes

Steps to collect quotes:
1. Navigate to  https://quotes.toscrape.com/
2. Create a loop through every pages.
3. For each quote inside a page, crawl the quote, its author, and its tags using CSS Selector for HTML elements.
4. Strip unnecessary double-quotes from each quote.
5. Check the next page:
	1. If there is a next page, navigate to it.
	2. Otherwise, we're in the last page. Break the loop.
6. Quit the browser.

Number of quotes collected: 100 quotes.
For each quote:
- Content
- Author
- Tags

A quote example:

```json
{
	"Text": "It is not a lack of love, but a lack of friendship that makes unhappy marriages.",
	"Author": "Friedrich Nietzsche",
	"Tags": [
		"friendship",
		"lack-of-friendship",
		"lack-of-love",
		"love",
		"marriage",
		"unhappy-marriage"
	]
}
```
## Books

Steps to collect quotes:
1. Navigate to  https://books.toscrape.com/
2. Collect all categories from the main page.
3. Create a loop through every categories.
4. For each category, loop through every pages.
5. For each book inside a page, crawl the book title, description, ratings, price, stock (whether it is in stock or not) using CSS Selector for HTML elements.
6. Check the next page (this is done for each category):
	1. If there is a next page, navigate to it.
	2. Otherwise, we're in the last page. Break the loop and move on to the next category.
7. Quit the browser.

Number of books collected: 1000 books.
For each book:
- Title
- Rating (1-5 stars)
- Price (in GBP)
- Stock (Are there any books left in stock?)
- Description of the books

A book example:

```json
{
	"title": "A Flight of Arrows (The Pathfinders #2)",
	"rating": 5,
	"price": "£55.53",
	"stock": "In stock",
	"description": "October 1776--August 1777It is said that what a man sows he will reap--and for such a harvest there is no set season. No one connected to Reginald Aubrey is untouched by the crime he committed twenty years ago. Not William, the Oneida child Reginald stole and raised as his own. Identity shattered, enlisted in the British army, William trains with Loyalist refugees eager to October 1776--August 1777It is said that what a man sows he will reap--and for such a harvest there is no set season. No one connected to Reginald Aubrey is untouched by the crime he committed twenty years ago. Not William, the Oneida child Reginald stole and raised as his own. Identity shattered, enlisted in the British army, William trains with Loyalist refugees eager to annihilate the rebels who forced them into exile. Coming to terms with who and what he is proves impossible, but if he breaks his Loyalist oath, he'll be no better than the man who constructed his life of lies.Not Anna, Reginald's adopted daughter, nor Two Hawks, William's twin, both who long for Reginald to accept their love despite the challenges they will face, building a marriage that bridges two cultures. Not Good Voice and Stone Thrower, freed of bitterness by a courageous act of forgiveness, but still yearning for their firstborn son and fearful for the future of their Oneida people.As the British prepare to attack frontier New York and Patriot regiments rally to defend it, two families separated by culture, united by love, will do all in their power to reclaim the son marching toward them in the ranks of their enemies. ...more"
}
```

