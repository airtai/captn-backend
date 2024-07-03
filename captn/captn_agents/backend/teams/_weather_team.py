from typing import Any, Callable, Dict, List, Optional, Tuple

from fastagency.openapi.client import Client

from ..config import Config
from ..tools._weather_team_tools import create_weather_team_client
from ._team import Team


@Team.register_team("weather_team")
class WeatherTeam(Team):
    _default_roles = [
        {
            "Name": "Weather_forecaster",
            "Description": """You are a weather forecaster.
Never introduce yourself when writing messages. E.g. do not write 'As a ...'""",
        },
        {
            "Name": "News_reporter",
            "Description": """You are a news reporter.
You are also SOLELY responsible for communicating with the client.

Based on the initial task, a number of proposed solutions will be suggested by the team. You must ask the team to write a detailed plan
including steps and expected outcomes.
Once the initial task given to the team is completed by implementing proposed solutions, you must write down the
accomplished work and execute the 'reply_to_client' command. That message will be forwarded to the client so make
sure it is understandable by non-experts.
Never introduce yourself when writing messages. E.g. do not write 'As an account manager'
""",
        },
    ]

    _functions: Optional[List[Dict[str, Any]]] = []

    def __init__(
        self,
        *,
        task: str,
        user_id: int,
        conv_id: int,
        work_dir: str = "weather_team",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        config_list: Optional[List[Dict[str, str]]] = None,
        create_client_func: Callable[[], Client] = create_weather_team_client,
    ):
        recommended_modifications_and_answer_list: List[
            Tuple[Dict[str, Any], Optional[str]]
        ] = []
        function_map: Dict[str, Callable[[Any], Any]] = {}

        roles: List[Dict[str, str]] = self._default_roles

        super().__init__(
            user_id=user_id,
            conv_id=conv_id,
            roles=roles,
            task=task,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            recommended_modifications_and_answer_list=recommended_modifications_and_answer_list,
            use_user_proxy=True,
        )

        if config_list is None:
            config = Config()
            config_list = config.config_list_gpt_4o

        self.llm_config = self._get_llm_config(
            seed=seed, temperature=temperature, config_list=config_list
        )
        self.create_client_func = create_client_func

        self._create_members()

        self._add_client()

        self._create_initial_message()

    def _add_client(self) -> None:
        self.client = self.create_client_func()

        self.client.register_for_execution(self.user_proxy)
        for agent in self.members:
            if agent != self.user_proxy:
                self.client.register_for_llm(agent)

    @property
    def _task(self) -> str:
        return f"""You are a team in charge of weather forecasting.

Here is the current customers brief/information we have gathered for you as a starting point:
{self.task}
"""

    @property
    def _guidelines(self) -> str:
        return """### Guidelines
1. Do NOT repeat the content of the previous messages nor repeat your role.
"""

    @property
    def _commands(self) -> str:
        return ""

    @classmethod
    def get_capabilities(cls) -> str:
        return "Weather forecasting for any city."

    @classmethod
    def get_brief_template(cls) -> str:
        return (
            "We only need the name of the city for which you want the weather forecast."
        )
