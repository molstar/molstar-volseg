from pathlib import Path

from pydantic import BaseSettings

# from preprocessor.src.tools.deploy_db.deploy import _get_git_revision_hash, _get_git_tag


class _Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 9000
    DEV_MODE: bool = False
    DB_PATH: Path = Path(__file__).absolute().parent.parent.parent / "test-data/db"
    # NOTE: maybe we can get default values already here by using _get_git_tag() and _get_git_revision_hash()?
    # currently it does not work:
    # Traceback (most recent call last):
    #   File "/home/aaxx/cellstar-volume-server/server/serve.py", line 3, in <module>
        # from app.settings import settings
    #   File "/home/aaxx/cellstar-volume-server/server/app/settings.py", line 5, in <module>
    #     from preprocessor.src.tools.deploy_db.deploy import _get_git_revision_hash, _get_git_tag
    # ImportError: cannot import name '_get_git_revision_hash' from 'preprocessor.src.tools.deploy_db.deploy' (/sw/cellstar-volume-server/preprocessor/src/tools/deploy_db/deploy.py)

    # GIT_TAG: str = _get_git_tag()
    # GIT_SHA: str = _get_git_revision_hash()
    GIT_TAG: str = ''
    GIT_SHA: str = ''


settings = _Settings()
