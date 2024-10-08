from typing import Any, Callable, Dict, List, Optional, Tuple

from ..config import Config
from ..toolboxes import Toolbox
from ..tools._team_with_client_tools import create_client
from ..tools.patch_client import get_patch_register_for_execution
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
        create_toolbox_func: Callable[[int, int, Dict[str, Any]], Toolbox],
        openapi_url: str,
        kwargs_to_patch: Optional[Dict[str, Any]] = None,
        work_dir: str = "team_with_client",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        config_list: Optional[List[Dict[str, str]]] = None,
        recommended_modifications_and_answer_list: Optional[
            List[Tuple[Dict[str, Any], Optional[str]]]
        ] = None,
        client_functions: Optional[Tuple[str, ...]] = None,
    ):
        if recommended_modifications_and_answer_list is None:
            recommended_modifications_and_answer_list = []
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
        # google_sheets_api_url is openapi_url without the /openapi.json
        self.google_sheets_api_url = openapi_url.rsplit("/", 1)[0]
        self.kwargs_to_patch = kwargs_to_patch
        self.client_functions = client_functions

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
        if self.kwargs_to_patch:
            get_patch_register_for_execution(self.client, self.kwargs_to_patch)()

        for agent in self.members:
            if agent.name in self.roles_with_client:
                if agent.llm_config["tools"] is None:
                    agent.llm_config.pop("tools")
                self.client._register_for_llm(agent, functions=self.client_functions)

        self.client._register_for_execution(
            self.user_proxy, functions=self.client_functions
        )

    def _add_tools(self) -> None:
        kwargs = {
            "recommended_modifications_and_answer_list": self.recommended_modifications_and_answer_list,
            "google_sheets_api_url": self.google_sheets_api_url,
        }
        self.toolbox = self.create_toolbox_func(
            self.user_id,
            self.conv_id,
            kwargs,
        )
        for agent in self.members:
            if agent != self.user_proxy and agent.name in self.roles_with_toolbox:
                self.toolbox.add_to_agent(agent, self.user_proxy)
