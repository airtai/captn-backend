from typing import Any, Callable, Dict, List, Optional, Tuple

from ..config import Config
from ..toolboxes import Toolbox
from ..tools._team_with_client_tools import create_client
from ._team import Team

__all__ = ("TeamWithClient",)


class TeamWithClient(Team):
    _functions: Optional[List[Dict[str, Any]]] = []

    def __init__(
        self,
        *,
        task: str,
        user_id: int,
        conv_id: int,
        roles: List[Dict[str, str]],
        create_toolbox_func: Callable[[int, int], Toolbox],
        openapi_url: str,
        work_dir: str = "team_with_client",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        config_list: Optional[List[Dict[str, str]]] = None,
    ):
        recommended_modifications_and_answer_list: List[
            Tuple[Dict[str, Any], Optional[str]]
        ] = []
        function_map: Dict[str, Callable[[Any], Any]] = {}

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
        self.create_toolbox_func = create_toolbox_func
        self.openapi_url = openapi_url

        self._create_members()

        self.roles_with_client = []
        self.roles_with_toolbox = []
        for role in self.roles:
            name = role["Name"].lower()
            if role["use_client"]:
                self.roles_with_client.append(name)
            if role["use_toolbox"]:
                self.roles_with_toolbox.append(name)

        self._add_client()
        self._add_tools()

        self._create_initial_message()

    def _add_client(self) -> None:
        self.client = create_client(self.openapi_url)

        for agent in self.members:
            if agent.name in self.roles_with_client:
                if agent.llm_config["tools"] is None:
                    agent.llm_config.pop("tools")
                self.client.register_for_llm(agent)

        self.client.register_for_execution(self.user_proxy)

    def _add_tools(self) -> None:
        self.toolbox = self.create_toolbox_func(
            self.user_id,
            self.conv_id,
        )
        for agent in self.members:
            if agent != self.user_proxy and agent.name in self.roles_with_toolbox:
                self.toolbox.add_to_agent(agent, self.user_proxy)
