import click
import requests as requests
from tqdm import tqdm
from lxml import html
from urllib.parse import urljoin

URL = "https://www.audiolibrix.com/"
LANDING_URL = "https://www.audiolibrix.com/cs/Podcast/726/pomala-hudba-fm"


@click.command()
def main():
    page = requests.get(LANDING_URL)
    tree = html.fromstring(page.content)

    for e_url in parse_episodes(tree):
        podcast_page_url = urljoin(URL, e_url)
        podcast_page = requests.get(podcast_page_url)
        podcast_tree = html.fromstring(podcast_page.content)

        podcast_url = parse_podcast(podcast_tree)
        download_podcast(podcast_url)


def download_podcast(podcast_url: str):
    r = requests.get(podcast_url, stream=True)

    total_size = int(r.headers["Content-Length"])
    chunk_size = 1024
    total = int(total_size / chunk_size)

    # TODO: implement downloading to target directory
    with open(filename, 'wb') as fd:
        for chunk in tqdm(r.iter_content(chunk_size=chunk_size), unit="KB", total=total, desc=filename):
            fd.write(chunk)


def parse_episodes(tree):
    (episodes,) = tree.xpath('//div[@id="all-episodes"]')
    # TODO: replace with xpath query
    for e in episodes.xpath('div')[0].getchildren():
        relative_url = e.getchildren()[0].getchildren()[0].attrib['href']
        print(relative_url)
        yield relative_url


def parse_podcast(tree):
    (podcast,) = tree.xpath('//a[contains(@href,"radio-arch-pp.stv.livebox.sk")]')
    return podcast.attrib['href']


if __name__ == "__main__":
    main()
