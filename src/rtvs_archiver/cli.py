import asyncio
from pathlib import Path
from urllib.parse import urljoin, urlparse

import aiofiles as aiofiles
import click
import tqdm.asyncio
from aiohttp import ClientSession, TCPConnector
from lxml import html

from rtvs_archiver.config import Config

BASE_URL = "https://www.audiolibrix.com/"


@click.command()
@click.option(
    "--download-dir",
    required=True,
    type=click.Path(),
    help="Directory to download archived podcasts (absolute or relative to current "
    "working directory at execution time).",
)
@click.option("--podcast-id", default=726, type=int, help="Podcast ID to be archived.")
@click.option("--parallel", default=16, type=int, help="Number of parallel downloads.")
def main(**kwargs):
    config = Config.parse_args(**kwargs)
    click.echo(f"Going to archive podcasts to directory: {config.download_dir}")

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(archive_podcasts(config))
    finally:
        loop.close()

    click.echo(f"All podcasts archived")


async def archive_podcasts(config: Config):
    tasks = []

    connector = TCPConnector(limit=config.parallel)
    async with ClientSession(connector=connector) as session:
        page = await session.get(config.podcast_landing_url)
        tree = html.fromstring(await page.text())
        page_links = list(tree.xpath("//a[contains(@class, 'page-link')]"))
        max_page_ind = max(int(p.text) for p in page_links)

        page_rel_url = page_links[0].attrib["href"]
        page_url = urljoin(BASE_URL, page_rel_url)
        # strip params
        page_url = urljoin(page_url, urlparse(page_url).path)

        for page_ind in range(max_page_ind):

            podcast_page = await session.get(page_url, params={"page": page_ind})
            podcast_raw = await podcast_page.text()
            podcast_tree = html.fromstring(podcast_raw)

            for i, episode_url in enumerate(parse_episodes(podcast_tree)):
                position = i + i * page_ind
                podcast_page_url = urljoin(BASE_URL, episode_url)
                podcast_page = await session.get(podcast_page_url)
                podcast_tree = html.fromstring(await podcast_page.text())

                podcast_url = parse_podcast(podcast_tree)
                podcast_name = Path(episode_url).stem

                task = asyncio.create_task(
                    download_podcast(config, session, podcast_name, podcast_url, position)
                )
                tasks.append(task)

        await asyncio.gather(*tasks)


async def download_podcast(
    config: Config, session: ClientSession, podcast_name: str, podcast_url: str, position: int
):
    async with session.get(podcast_url) as r:
        total_size = int(r.headers["Content-Length"])
        chunk_size = 1024
        total = int(total_size / chunk_size)

        filename = config.download_dir / f"{podcast_name}.mp3.part"
        final_filename = config.download_dir / f"{podcast_name}.mp3"

        if final_filename.exists():
            return

        pbar = tqdm.asyncio.tqdm(
            unit="KB", total=total, leave=True, desc=podcast_name, position=position
        )

        async with aiofiles.open(filename, "wb") as fd:
            async for chunk in r.content.iter_chunked(n=chunk_size):
                await fd.write(chunk)
                pbar.update()

        filename.rename(final_filename)


def parse_episodes(tree):
    (episodes,) = tree.xpath('//div[@id="all-episodes"]')
    # TODO: replace with xpath query
    for e in episodes.xpath("div")[0].getchildren():
        relative_url = e.getchildren()[0].getchildren()[0].attrib["href"]
        yield relative_url


def parse_podcast(tree):
    (podcast,) = tree.xpath('//a[contains(@href,"radio-arch-pp.stv.livebox.sk")]')
    return podcast.attrib["href"]


if __name__ == "__main__":
    main()
