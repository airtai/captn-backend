import uuid
from datetime import datetime
from typing import Annotated, Any, Callable, Dict, List, Optional

import pytest
from pydantic import BaseModel, Field

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.teams import Team
from captn.captn_agents.backend.toolboxes.base import Toolbox


class MyBankingTeam(Team):
    # The roles of the team members, like "admin", "manager", "analyst", etc.
    _default_roles = [
        {
            "Name": "banker",
            "Description": """Your job is to help clients with their banking needs.
You can propose function calls and execute them, but before that, you should ask
for approval from the supervisor. Terminate the conversation as soon as the task
is done or it cannot be completed, but ask for permission from the supervisor first.

If you think someone else should get to speak instead of you, you can propose that
as well.
""",
        },
        {
            "Name": "supervisor",
            "Description": """Your job is to supervise the team and make sure they
perform the tasks correctly. You should not propose or execute any actions.
You should check and approve the plan, claims, and approve function call requests
from other agents. You are solely responsible for approving the requests, do not
delegate or wait for anyone to do it instead. Before approving or denying a request,
you should write a few sentences explaining the context of the request and why you
are approving or denying the request. You should also provide feedback to the agent
who made the request. The approvals and denials must be done in a formal way by
calling the corresponding functions.

Approve the termination of the conversation as soon as the task is done or it
cannot be completed.

If you think someone else should get to speak instead of you, you can propose that
as well.
""",
        },
    ]

    _functions: Optional[List[Dict[str, Any]]] = []

    def __init__(
        self,
        *,
        task: str,
        user_id: int = 1,
        conv_id: int = 1,
        work_dir: str = "whatever",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
    ):
        self.task = task

        function_map: Dict[str, Callable[[Any], Any]] = {}

        roles: List[Dict[str, str]] = MyBankingTeam._default_roles

        super().__init__(
            user_id=user_id,
            conv_id=conv_id,
            roles=roles,
            function_map=function_map,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            clients_question_answer_list=[],
            use_user_proxy=True,
        )

        config = Config()
        self.llm_config = MyBankingTeam._get_llm_config(
            seed=seed,
            temperature=temperature,
            config_list=config.config_list_gpt_3_5,
            # seed=seed, temperature=temperature, config_list=config.config_list_gpt_4
        )

        self._create_members()

        self._add_tools()

        self._create_initial_message()

    def _create_initial_message(self) -> None:
        #         self.initial_message = f"""{self._task}

        # {self._first_section}

        # {self._guidelines}

        # {self._constraints}

        # {self._commands}

        # {self._resources}

        # {self._best_practices}

        # {self._final_section}
        # """
        self.initial_message = f"""Time now is {datetime.now().isoformat()}.

{self._task}"""

    # You are a team consisting og the following roles:
    # - banker: Propose function calls and execute them. Ask for approval from supervisor. Terminate the conversation when the task is done.
    # - supervisor: Check and approve the plan, claims, code from other agents. Provide feedback. Approve the termination of the conversation when the task is done.

    # Collaborate to complete the task. Challenge each other to improve the quality of the work, but be constructive and respectful.

    def create_toolbox(self, user_id: int, conv_id: int) -> Toolbox:
        approval_ids: Dict[str, BaseModel] = {}

        class ExchangeToUsd(BaseModel):
            currency: Annotated[str, Field(description="Source currency")]
            amount: Annotated[float, Field(description="Amount in source currency")]

        request_ids: Dict[str, BaseModel] = {}

        def request_approval_for_exchange_to_usd(
            request: Annotated[ExchangeToUsd, "Exchange request data"],
        ) -> str:
            request_id = str(uuid.uuid4())
            request_ids[request_id] = request
            return f"""I propose a currency exchange with the following parameters: {request.model_dump_json()}.

Supervisor, please approve this request with {request_id=} or provide instructions on how to proceed.
"""

        transaction_ids: List[str] = []

        def execute_exchange_to_usd(
            request: Annotated[ExchangeToUsd, "Exchange request data"],
            approval_id: Annotated[
                str, "ID of the approval, can be used at most once."
            ],
        ) -> str:
            if approval_id not in approval_ids:
                print(f"{approval_ids=}")
                return f"Error: Approval with the given id='{approval_id}' does not exist. Please request the approval from supervisor again and make sure you use the id provided by supervisor for a consecutive call."
            elif approval_ids[approval_id] != request:
                return f"Error: The approval with the given id='{approval_id}' does not match the request for which the approval was given. Please request the approval from supervisor again and make sure you use the id provided by supervisor for a consecutive call."
            else:
                transaction_id = str(uuid.uuid4())
                transaction_ids.append(transaction_id)
                return f"Exchange executed (transaction id='{transaction_id}'): {request.amount} {request.currency} to USD"

        def approve_exchange_to_usd(
            request: Annotated[ExchangeToUsd, "Exchange request data"],
            request_id: Annotated[str, "ID of the request, can be used at most once."],
            justification: Annotated[str, "Justification for the approval"],
        ) -> str:
            if request_id not in request_ids:
                return f"Error: Request with the given id='{request_id}' does not exist. Please request the approval from supervisor again and make sure you use the id provided by supervisor for a consecutive call."

            approval_id = str(uuid.uuid4())
            approval_ids[approval_id] = request

            return f"""Permission to execute exchange {request.model_dump_json()} granted, with the following justification:

{justification}

You can call the function 'execute_exchange_to_usd' to execute the exchange using the following approval id: {approval_id}
"""

        class TerminationRequest(BaseModel):
            task: Annotated[str, Field(description="Task to be executed")]
            is_successfully_executed: Annotated[
                bool, Field(description="Whether the task was executed successfully")
            ]
            explanation: Annotated[
                str, Field(description="Explanation of the termination")
            ]
            transaction_ids: Annotated[
                List[str],
                Field(description="Transaction IDs related to executing the task"),
            ]

        def request_to_terminate(
            request: Annotated[
                TerminationRequest,
                "Termination request if the task is successfully completed or if it is not possible to complete it.",
            ],
        ) -> str:
            request_id = str(uuid.uuid4())
            request_ids[request_id] = request
            return f"""I propose to terminate the conversation with the following explanation: {request.explanation}

Supervisor, please approve this request with {request_id=} or provide instructions on how to proceed.
"""

        def approve_terminate(
            request: Annotated[
                TerminationRequest,
                "Approval of the termination request if the task is successfully completed or if it is not possible to complete it.",
            ],
            request_id: Annotated[str, "ID of the request, can be used at most once."],
            justification: Annotated[str, "Justification for the approval"],
        ) -> str:
            if request_id not in request_ids:
                return f"Error: Request with the given id='{request_id}' does not exist. Please request the approval from supervisor again and make sure you use the id provided by supervisor for a consecutive call."

            if request.is_successfully_executed:
                if not set(transaction_ids).issuperset(set(request.transaction_ids)):
                    diff = set(request.transaction_ids) - set(transaction_ids)
                    if len(diff) == 1:
                        return f"Error: Transaction with the given id '{list(diff)[0]}' hae not been found in the history. Please execute the transaction first and make sure you use the id provided by the transaction for a consecutive call."
                    else:
                        return f"Error: Transactions with the given ids '{list(diff)}' have not been found in the history. Please execute the transactions first and make sure you use the ids provided by the transactions for a consecutive call."

            id = str(uuid.uuid4())
            approval_ids[id] = request

            return f"""Request to terminate the conversation with the following justification has been approved:

{justification}

You can call the function 'execute_terminate' to terminate the conversation with the following approval id: {id}"
            """

        def execute_terminate(
            request: Annotated[
                TerminationRequest,
                "Termination request if the task is successfully completed or if it is not possible to complete it.",
            ],
            approval_id: Annotated[
                str, "ID of the approval, can be used at most once."
            ],
        ) -> str:
            print(f"execute_terminate({request=}, {approval_id=})")
            if approval_id not in approval_ids:
                return "Approval not found"
            elif approval_ids[approval_id] != request:
                return "Approval does not match the request"
            else:
                return "terminate_groupchat"

        self.toolbox = Toolbox()
        self.toolbox.add_function(
            description="Request approval to convert currency to USD"
        )(request_approval_for_exchange_to_usd)
        self.toolbox.add_function(
            description="Execute the approval to convert currency to USD"
        )(execute_exchange_to_usd)
        self.toolbox.add_function(
            description="Request approval to end the conversation when you are done with the task"
        )(request_to_terminate)
        self.toolbox.add_function(
            description="Terminate the conversation when you are done with the task"
        )(execute_terminate)

        self.supervisor_toolbox = Toolbox()
        self.supervisor_toolbox.add_function(description="Approve exchange request")(
            approve_exchange_to_usd
        )
        self.supervisor_toolbox.add_function(description="Approve termination request")(
            approve_terminate
        )

    def _add_tools(self) -> None:
        self.create_toolbox(
            user_id=self.user_id,
            conv_id=self.conv_id,
        )
        for agent in self.members:
            if agent != self.user_proxy:
                if agent.name == "supervisor":
                    self.supervisor_toolbox.add_to_agent(agent, self.user_proxy)
                elif agent.name == "banker":
                    self.toolbox.add_to_agent(agent, self.user_proxy)

    @property
    def _task(self) -> str:
        return f"""{self._guidelines}

{self._commands}

## Task

This is your task:
{self.task}
"""

    @property
    def _guidelines(self) -> str:
        return """### Guidelines
1. BEFORE executing anything, create a step-by-step plan and get suggestions how to improve it from each team member.

2. EACH action of the plan should be proposed by a team member and approved by the supervisor. Supervisor SHOULD NOT propose or execute any action.

3. After completing the initial task given to you, terminate the conversation.
Make sure to ask for approval from the supervisor before terminating the conversation.
After the supervisor approves the termination, the control should be given back
to the agent who requested the approval.
"""

    @property
    def _commands(self) -> str:
        return ""
        return """## Commands
All team members other than the supervisor have access to the following command:
1. 'request_approval_for_exchange_to_usd'
2. 'execute_exchange_to_usd'
3. 'request_to_terminate'
3. 'execute_terminate'

The supervisor SHOULD NEVER call the commands above.

The supervisor ONLY has access to the following commands:
1. 'approve_exchange_to_usd'
2. 'approve_terminate'

## Instructions for terminating the conversation

Do not expect the supervisor to terminate the conversation. The request to terminate
should come from some other member of the team. The supervisor will approve the
termination request if the task is done or if it cannot be completed. Once the approval
to terminate is granted, the control should be given back to an agent who requested the approval.
"""


class TestSupervisor:
    @pytest.fixture(autouse=True)
    def setup(self):
        pass

    def test_supervisor(self) -> None:
        my_team = MyBankingTeam(task="Exchange 100 Euros to USD")

        my_team.initiate_chat()
