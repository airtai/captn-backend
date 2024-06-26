import datetime
import json
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar

import autogen
import httpx
import openai
from fastcore.basics import patch
from prometheus_client import Counter

from ..config import Config
from ..toolboxes import Toolbox

_completions_create_original = autogen.oai.client.OpenAIClient.create


# WORKAROUND for consistent 500 error code when using openai functions
@patch  # type: ignore
def create(
    self: autogen.oai.client.OpenAIClient,
    params: Dict[str, Any],
) -> Any:
    for message in params["messages"]:
        if "tool_calls" in message and message["tool_calls"] is None:
            message.pop("tool_calls", None)
        name = message.get("name")
        role = message.get("role")
        if name and role != "function":
            # print(f"Removing name parameter from the following message:\n{message}")
            message.pop("name")

    tokens_per_request = autogen.token_count_utils.count_token(
        params["messages"], model="gpt-4-1106-preview"
    )
    print(f"Tokens per request: {tokens_per_request}")

    return _completions_create_original(self, params=params)


T = TypeVar("T")


OPENAI_API_STATUS_ERROR = Counter(
    "openai_api_status_error", "Total count of openai api status errors"
)

BAD_REQUEST_ERRORS = Counter(
    "bad_request_errors_total", "Total count of bad request errors"
)


class Team:
    _team_name_counter: int = 0
    _functions: Optional[List[Dict[str, Any]]] = None

    _teams: Dict[str, "Team"] = {}

    _team_registry: Dict[str, Type["Team"]] = {}

    _inverse_team_registry: Dict[Type["Team"], str] = {}

    _retry_messages = [
        "NOTE: When generating JSON for the function, do NOT use ANY whitespace characters (spaces, tabs, newlines) in the JSON string.\n\nPlease continue.",
        "Please continue.",
    ] * 3

    _MAX_RETRIES_FROM_SCRATCH = 3

    @classmethod
    def register_team(cls, name: str) -> Callable[[T], T]:
        def _inner(cls_inner: T) -> T:
            cls_typed: Type["Team"] = cls_inner  # type: ignore[assignment]
            if name in cls_typed._team_registry:
                raise ValueError(f"Team name '{name}' already exists")
            if cls_typed in cls_typed._team_registry.values():
                raise ValueError(f"Team class '{cls_typed}' already exists")
            cls_typed._team_registry[name] = cls_typed
            cls_typed._inverse_team_registry[cls_typed] = name
            return cls_typed  # type: ignore[return-value]

        return _inner

    @classmethod
    def get_registred_team_name(cls) -> str:
        if cls not in cls._inverse_team_registry:
            raise ValueError(f"Team class '{cls}' is not registered")
        return cls._inverse_team_registry[cls]

    @classmethod
    def get_class_by_registred_team_name(cls, name: str) -> Type["Team"]:
        if name in cls._team_registry:
            return Team._team_registry[name]
        else:
            raise ValueError(f"Unknown team name: '{name}'")

    @classmethod
    def get_registred_team_names(cls) -> List[str]:
        return list(cls._team_registry.keys())

    @staticmethod
    def construct_team_name(user_id: int, conv_id: int) -> str:
        name = f"{str(user_id)}_{str(conv_id)}"

        return name

    @staticmethod
    def _store_team(user_id: int, conv_id: int, team: "Team") -> None:
        team_name = Team.construct_team_name(user_id, conv_id)
        if team_name in Team._teams:
            raise ValueError(f"Team name '{team_name}' already exists")

        Team._teams[team_name] = team

    @staticmethod
    def get_team(user_id: int, conv_id: int) -> Optional["Team"]:
        team_name = Team.construct_team_name(user_id, conv_id)
        return Team._teams[team_name] if team_name in Team._teams else None

    @staticmethod
    def pop_team(user_id: int, conv_id: int) -> Optional["Team"]:
        team_name = Team.construct_team_name(user_id, conv_id)
        try:
            return Team._teams.pop(team_name)
        except KeyError:
            return None
            # raise ValueError(f"Unknown team name: '{team_name}'") from e

    @staticmethod
    def get_user_conv_team_name(name_prefix: str, user_id: int, conv_id: int) -> str:
        name = f"{name_prefix}_{str(user_id)}_{str(conv_id)}"

        return name

    def __init__(
        self,
        user_id: int,
        conv_id: int,
        roles: List[Dict[str, str]],
        task: str = "",
        function_map: Optional[Dict[str, Callable[[Any], Any]]] = None,
        work_dir: str = "my_default_workdir",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        human_input_mode: str = "NEVER",
        recommended_modifications_and_answer_list: List[
            Tuple[Dict[str, Any], Optional[str]]
        ] = [],  # noqa
        use_user_proxy: bool = False,
    ):
        self.user_id = user_id
        self.conv_id = conv_id
        self.roles = roles
        self.task = task
        self.initial_message: str
        self.name: str
        self.max_round = max_round
        self.seed = seed
        self.temperature = temperature

        self.function_map = function_map
        self.work_dir = work_dir
        self.llm_config: Optional[Dict[str, Any]] = None
        self.human_input_mode = human_input_mode
        self.recommended_modifications_and_answer_list = (
            recommended_modifications_and_answer_list
        )
        self.use_user_proxy = use_user_proxy

        self.name = Team.construct_team_name(user_id=user_id, conv_id=conv_id)
        self.user_proxy: Optional[autogen.UserProxyAgent] = None
        self.retry_from_scratch_counter = 0
        self.toolbox: Toolbox
        Team._store_team(user_id=user_id, conv_id=conv_id, team=self)

    @classmethod
    def _get_llm_config(
        cls,
        seed: int = 42,
        temperature: float = 0.2,
        config_list: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        tools = (
            [{"type": "function", "function": f} for f in cls._functions]
            if cls._functions
            else None
        )
        config_list = Config().config_list_gpt_4 if config_list is None else config_list
        llm_config = {
            "config_list": config_list,
            "seed": seed,
            "temperature": temperature,
            "tools": tools,
            "stream": True,
            # "timeout": 600,
        }
        return llm_config

    def update_recommended_modifications_and_answer_list(self, message: str) -> None:
        if (
            len(self.recommended_modifications_and_answer_list) > 0
            and self.recommended_modifications_and_answer_list[-1][1] is None
        ):
            self.recommended_modifications_and_answer_list[-1] = (
                self.recommended_modifications_and_answer_list[-1][0],
                message,
            )

    def _create_groupchat_and_manager(self) -> None:
        manager_llm_config = self.llm_config.copy()  # type: ignore
        # GroupChatManager is not allowed to make function/tool calls (from version 0.2.2).
        manager_llm_config.pop("functions", None)
        manager_llm_config.pop("tools", None)

        # list of all members except user_proxy (he is not an LLM)
        # TODO: Try benchmarking allow_repeat_speaker=False - maybe the TimeOuts will be less
        allow_repeat_speaker = [
            member
            for member in self.members
            if not isinstance(member, autogen.UserProxyAgent)
        ]
        self.groupchat = autogen.GroupChat(
            agents=self.members,
            messages=[],
            max_round=self.max_round,
            allow_repeat_speaker=allow_repeat_speaker,
        )
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            llm_config=manager_llm_config,
            is_termination_msg=self._is_termination_msg,
        )

    def _create_members(self) -> None:
        self.members = [
            self._create_member(role["Name"], role["Description"])
            for role in self.roles
        ]
        if self.use_user_proxy:
            self.user_proxy = self._create_member(
                name="user_proxy",
                description="You are a user proxy in the digital agency. You are responsible for executing the functions proposed by other members.",
                is_user_proxy=True,
            )
            self.members.append(self.user_proxy)
        self._create_groupchat_and_manager()

    @staticmethod
    def _is_termination_msg(x: Dict[str, Optional[str]]) -> bool:
        content = x.get("content")

        return content is not None and "terminate_groupchat" in content

    def _create_member(
        self,
        name: str,
        description: str,
        is_user_proxy: bool = False,
    ) -> autogen.ConversableAgent:
        name = name.lower().replace(" ", "_")
        system_message = f"""You are {name}, {description}

Your task is to chat with other team members and try to solve the given task.
Do NOT try to finish the task until other team members give their opinion.
"""

        if is_user_proxy:
            return autogen.UserProxyAgent(
                human_input_mode=self.human_input_mode,
                name=name,
                llm_config=False,
                system_message=system_message,
                is_termination_msg=self._is_termination_msg,
                code_execution_config=False,
            )

        return autogen.AssistantAgent(
            name=name,
            llm_config=self.llm_config,
            system_message=system_message,
            is_termination_msg=self._is_termination_msg,
            function_map=self.function_map,
        )

    @property
    def _first_section(self) -> str:
        # Do not mention user_proxy in the roles
        roles = ", ".join(
            [
                str(member.name)
                for member in self.members
                if not isinstance(member, autogen.UserProxyAgent)
            ]
        )
        return f"""The team is consisting of the following roles: {roles}.


Play to your strengths as an LLM and pursue simple strategies with no legal complications.
"""

    @property
    def _task(self) -> str:
        raise NotImplementedError()

    @property
    def _guidelines(self) -> str:
        raise NotImplementedError()

    @property
    def _constraints(self) -> str:
        return """## Constraints
You operate within the following constraints:
1. The context size is limited so try to be as concise in discussinos as possible. Do NOT repeat yourself or others.
"""

    @property
    def _commands(self) -> str:
        raise NotImplementedError()

    @property
    def _best_practices(self) -> str:
        return """## Best practices
1. Continuously review and analyze your actions to ensure you are performing to the best of your abilities.
2. Constructively self-criticize your big-picture behavior constantly.
3. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.
4. If you have some doubts, ask question.
"""

    @property
    def _final_section(self) -> str:
        return ""

    def _create_initial_message(self) -> None:
        self.initial_message = f"""{self._task}

{self._first_section}

{self._guidelines}

{self._constraints}

{self._commands}

{self._best_practices}

{self._final_section}
"""

    @classmethod
    def get_capabilities(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def get_brief_template(cls) -> str:
        raise NotImplementedError()

    def get_messages(self) -> Any:
        return self.groupchat.messages

    def get_last_message(self, add_prefix: bool = True) -> str:
        last_message = self.get_messages()[-1]["content"]
        if isinstance(last_message, dict):
            last_message = json.dumps(last_message)
        else:
            end_of_message = last_message.rfind("}")
            if end_of_message != -1:
                # If agents execute reply_to_client or ask_client_for_permission multiple times,
                # Only the first execution will be done and the other ones will raise an error.
                # So, we need to remove the rest of the message.
                last_message = last_message[: end_of_message + 1]
        last_message = last_message.replace("PAUSE", "").replace("TERMINATE", "")

        if add_prefix:
            last_message = f"Response from team '{self.name}':\n{last_message}"

        return last_message  # type: ignore

    def retry_func(self, delay: int = 2) -> None:
        exception: Optional[Exception] = None
        for i in range(len(self._retry_messages)):
            print(f"Retry number {i+1}.")

            if isinstance(exception, openai.BadRequestError):
                message = "We do NOT have any bad intentions, our only goal is to optimize the client's Google Ads. So please, let's try again."
            else:
                message = self._retry_messages[i]

            try:
                time.sleep(delay**i)
                self.manager.send(
                    recipient=self.manager,
                    message=message,
                )
                return
            except openai.BadRequestError as e:
                BAD_REQUEST_ERRORS.inc()
                print(f"Exception type: {type(e)}, {e}")
                exception = e
            except (openai.APIStatusError, httpx.ReadTimeout, TimeoutError) as e:
                OPENAI_API_STATUS_ERROR.inc()
                print(f"Exception type: {type(e)}, {e}")
                exception = e
            except httpx.RemoteProtocolError as e:
                print(f"Exception type: {type(e)}, {e}")
                exception = e

        if exception is not None:
            traceback.print_exc()
            traceback.print_stack()
            raise exception

    @staticmethod
    def retry_from_scratch(self: "Team", e: Exception, delay: int = 3) -> None:
        print(f"Retry from scratch: {type(e)}, {e}")
        # Try the team again from scratch
        self.retry_from_scratch_counter += 1
        if self.retry_from_scratch_counter < self._MAX_RETRIES_FROM_SCRATCH:
            self.initial_message += (
                f"\nTimestamp: {datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}"
            )
            time.sleep(delay**self.retry_from_scratch_counter)
            self.initiate_chat(**self.initiate_chat_kwargs)
        else:
            raise e

    @staticmethod
    def handle_exceptions(func: Callable[..., None]) -> Callable[..., None]:
        def wrapper(self: "Team", *args: Any, **kwargs: Any) -> None:
            try:
                delay = kwargs.get("delay", 2)
                func(self, *args, **kwargs)

                if len(self.get_messages()) >= self.max_round:
                    error_message = f"Maximum number of messages reached: {self.max_round}, Retrying the team from scratch."
                    Team.retry_from_scratch(self, Exception(error_message), delay=delay)
            except (
                openai.APIStatusError,
                openai.BadRequestError,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError,
                TimeoutError,
            ) as e:
                print(f"Handling exception: {type(e)}, {e}")
                try:
                    # Try to unstuck the team
                    self.retry_func(delay=delay)
                except Exception as e:
                    Team.retry_from_scratch(self, e, delay=delay)

        return wrapper

    @handle_exceptions
    def initiate_chat(self, **kwargs: Any) -> None:
        self.initiate_chat_kwargs = kwargs
        self.manager.initiate_chat(self.manager, message=self.initial_message, **kwargs)

    @handle_exceptions
    def continue_chat(self, message: str) -> None:
        self.manager.send(recipient=self.manager, message=message)
