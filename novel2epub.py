import time
import requests
import re
from bs4 import BeautifulSoup
from ebooklib import epub
import sys

current_site = input("Hiraeth LN Link: ")


lnFormat1 = r'volume-[0-9.]+-chapter-[0-9.]+-[0-9.]+'
lnFormat2 = r'volume-[0-9.]+-chapter-[0-9.]+'
checkLink = re.search(lnFormat1, current_site) or re.search(lnFormat2, current_site)

if not checkLink:
  print(f"Invalid link! Try putting the link of the very first chapter.")
  sys.exit()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetchPage(url):
  response = requests.get(url, headers=headers, timeout=15)
  response.raise_for_status()
  return BeautifulSoup(response.text, "html.parser")

def getBookTitle(soup):
  title = soup.find('meta', property='og:image:alt')
  return title['content'] if title else "Unknown Title"

def getVolumeNumber(chapter_title):
  match = re.search(r"Volume ([0-9]+)", chapter_title)
  return int(match.group(1)) if match else 1

def getChapterTitle(soup):
  return soup.find('li', class_="active").get_text(strip=True)

def getChapterContents(soup):
  content = soup.find('div', class_="text-left")
  paragraphs = content.find_all('p')
  return "\n\n".join(p.get_text(strip=True) for p in paragraphs)

def getNextChapterURL(soup):
  try:
    return soup.find('a', class_="btn next_page")['href']
  except TypeError:
    print(f"No next chapters found!")
    return None
  
def buildEpub(book_title, chapters):
  safe_title = re.sub(r'[<>:"/\\|?*]', '', book_title)
  book = epub.EpubBook()
  book.set_title(book_title)
  book.set_language("en")

  epub_chapters = []

  for i, chap in enumerate(chapters):
    page = epub.EpubHtml(
      title = chap["title"],
      file_name = f"chapter_{i}.xhtml"
    )
    paragraphs = "".join(f"<p>{p}</p>" for p in chap["body"].split("\n\n"))
    page.content = f"<h1>{chap['title']}</h1>{paragraphs}"

    book.add_item(page)
    epub_chapters.append(page)

  book.toc = epub_chapters

  book.spine = ["nav"]  + epub_chapters

  book.add_item(epub.EpubNcx())
  book.add_item(epub.EpubNav())

  epub.write_epub(f"{safe_title}.epub", book)
  print(f"[Saved] -> {safe_title}.epub")

def hasPara():
  return (len(sys.argv) > 1 and sys.argv[1].lower() == "--d")

volumes = {}
book_title = None

counter = 0

if not hasPara():
  print("Scraping.. This may take a while especially if there are tons of chapters!")

while current_site:
  soup = fetchPage(current_site)

  if not book_title:
    book_title = getBookTitle(soup)

  chapter_title = getChapterTitle(soup)
  volume_number = getVolumeNumber(chapter_title)
  chapter_contents = getChapterContents(soup)

  if volume_number not in volumes:
    volumes[volume_number] = []

  volumes[volume_number].append({"title": chapter_title, "body": chapter_contents})

  if hasPara(): 
    print(f"Currently scraping: {chapter_title}")

  current_site = getNextChapterURL(soup)
  counter = counter + 1
  time.sleep(1.0)

for volume_num, chapters in volumes.items():
  buildEpub(f"{book_title} - Volume {volume_num}", chapters)


print(f"Total volumes: {len(volumes)}")
print(f"Total chapters: {counter}")
