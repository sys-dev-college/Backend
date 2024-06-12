from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

config = Config("alembic.ini")
script = ScriptDirectory.from_config(config)
REVISION = ":head"
starting_rev, revision = REVISION.split(":", 2)


def upgrade(rev, _context):
    return script._upgrade_revs(revision, rev)


with EnvironmentContext(
    config,
    script,
    fn=upgrade,
    as_sql=False,
    starting_rev=starting_rev,
    destination_rev=revision,
):
    script.run_env()
