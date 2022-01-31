from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    download_parent_dir: Path
    podcast_id: int
    parallel: int

    @classmethod
    def parse_args(cls, **kwargs):
        download_parent_dir = Path(kwargs["download_dir"])
        if not download_parent_dir.is_absolute():
            curr_cwd = Path.cwd()
            download_parent_dir = curr_cwd / download_parent_dir
            download_parent_dir.mkdir(parents=True, exist_ok=True)

        podcast_id = kwargs["podcast_id"]
        parallel = kwargs["parallel"]

        config = Config(
            download_parent_dir=download_parent_dir, podcast_id=podcast_id, parallel=parallel
        )
        config.download_dir.mkdir(parents=True, exist_ok=True)

        return config

    @property
    def podcast_landing_url(self) -> str:
        return f"https://www.audiolibrix.com/cs/Podcast/{self.podcast_id}/"

    @property
    def download_dir(self) -> Path:
        return self.download_parent_dir / str(self.podcast_id)
