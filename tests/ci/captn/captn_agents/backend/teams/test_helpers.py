from tempfile import TemporaryDirectory

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.teams import BriefCreationTeam

from .helpers import get_client_response


@pytest.mark.flaky
@pytest.mark.openai
def test_clients_response() -> None:
    team = BriefCreationTeam(task="task", user_id=12, conv_id=13)

    with TemporaryDirectory() as cache_dir:
        with Cache.disk(cache_path_root=cache_dir) as cache:
            clients_response = get_client_response(
                team=team,
                cache=cache,
                client_system_message="Always reply with yes.",
            )
            response = clients_response(
                message="Do you accept the suggestion?",
                completed=False,
            )

    assert "yes" in response.lower()
