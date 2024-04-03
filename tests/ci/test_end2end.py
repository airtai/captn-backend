from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from captn.captn_agents.backend import Team
from captn.captn_agents.backend.end_to_end import _get_team


@pytest.mark.parametrize(
    "class_name",
    ["default_team", "campaign_creation_team", "should raise"],
)
def test_get_initial_team(class_name: str) -> None:
    Team._teams.clear()
    with TemporaryDirectory() as tmp_dir:
        kwargs = {
            "user_id": 123,
            "conv_id": 456,
            "root_dir": Path(tmp_dir),
            "task": "do your magic",
            "max_round": 80,
            "seed": 42,
            "temperature": 0.2,
            "class_name": class_name,
        }

        if class_name == "should raise":
            with pytest.raises(ValueError, match="Unknown team name"):
                _get_team(**kwargs)  # type: ignore[arg-type]
        else:
            initial_team, _ = _get_team(**kwargs)  # type: ignore[arg-type]

            assert isinstance(initial_team, Team)
