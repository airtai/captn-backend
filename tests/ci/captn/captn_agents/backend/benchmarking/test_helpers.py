from tempfile import TemporaryDirectory

import pytest
from autogen.cache import Cache

from captn.captn_agents.backend.benchmarking.helpers import get_client_response
from captn.captn_agents.backend.teams import BriefCreationTeam, Team
from captn.captn_agents.backend.tools._functions import BaseContext


@pytest.mark.flaky
@pytest.mark.openai
def test_clients_response() -> None:
    try:
        BriefCreationTeam(task="task", user_id=12, conv_id=13)
        with TemporaryDirectory() as cache_dir:
            with Cache.disk(cache_path_root=cache_dir) as cache:
                clients_response = get_client_response(
                    user_id=12,
                    conv_id=13,
                    cache=cache,
                    client_system_message="Always reply with yes.",
                )
                context = BaseContext(
                    user_id=12,
                    conv_id=13,
                )
                response = clients_response(
                    message="Do you accept the suggestion?",
                    completed=False,
                    context=context,
                )

        assert "yes" in response.lower()
    finally:
        Team.pop_team(12, 13)
