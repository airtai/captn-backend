from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from captn.captn_agents.backend.end_to_end import _get_initial_team
from captn.captn_agents.backend.team import Team


@pytest.mark.parametrize(
    "class_name",
    ["default_team", "campaign_creation_team", "should raise"],
)
def test_get_initial_team(class_name: str) -> None:
    with TemporaryDirectory() as tmp_dir:
        kwargs = {
            "user_id": 123,
            "conv_id": 456,
            "root_dir": Path(tmp_dir),
            "task": "do your magic",
            "roles": None,
            "max_round": 80,
            "seed": 42,
            "temperature": 0.2,
            "human_input_mode": "NEVER",
            "class_name": class_name,
            "use_async": False,
        }

        if class_name == "should raise":
            with pytest.raises(ValueError, match="Unknown team name"):
                _get_initial_team(**kwargs)  # type: ignore[arg-type]
        else:
            initial_team, team_name, _ = _get_initial_team(**kwargs)  # type: ignore[arg-type]

            assert isinstance(initial_team, Team)
