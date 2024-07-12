from os import environ
from typing import Any, Callable, Dict, List, Optional

from ....google_ads.client import get_conv_uuid
from ..toolboxes import Toolbox
from ..tools._gbb_google_sheets_team_tools import create_google_ads_expert_toolbox

# Currently only reply_to_client command within this toolbox
from ..tools._weather_team_tools import (
    create_weather_team_toolbox,
)
from ._shared_prompts import REPLY_TO_CLIENT_COMMAND
from ._team import Team
from ._team_with_client import TeamWithClient

GOOGLE_SHEETS_OPENAPI_URL = environ.get(
    "GOOGLE_SHEETS_OPENAPI_URL", "http://localhost:8000/openapi.json"
)


@Team.register_team("gbb_google_sheets_team")
class GBBGoogleSheetsTeam(TeamWithClient):
    _default_roles = [
        {
            "Name": "Google_sheets_expert",
            "Description": """Google Sheets expert.
Never introduce yourself when writing messages. E.g. do not write 'As a ...'""",
            "use_client": True,
            "use_toolbox": False,
        },
        {
            "Name": "Account_manager",
            "Description": """You are an account manager.
You are also SOLELY responsible for communicating with the client.

Based on the initial task, a number of proposed solutions will be suggested by the team. You must ask the team to write a detailed plan
including steps and expected outcomes.
Once the initial task given to the team is completed by implementing proposed solutions, you must write down the
accomplished work and execute the 'reply_to_client' command. That message will be forwarded to the client so make
sure it is understandable by non-experts.
Never introduce yourself when writing messages. E.g. do not write 'As an account manager'
""",
            "use_client": False,
            "use_toolbox": True,
        },
        {
            "Name": "Google_ads_expert",
            "Description": """Google Ads expert.
Never introduce yourself when writing messages. E.g. do not write 'As a ...'""",
            "use_client": False,
            # We will add additional toolbox for this agent
            # Toolbox won't be added in the parent class
            "use_toolbox": False,
        },
    ]

    _functions: Optional[List[Dict[str, Any]]] = []

    def __init__(
        self,
        *,
        task: str,
        user_id: int,
        conv_id: int,
        work_dir: str = "gbb_google_sheets_team",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        config_list: Optional[List[Dict[str, str]]] = None,
        create_toolbox_func: Callable[
            [int, int], Toolbox
        ] = create_weather_team_toolbox,
        openapi_url: str = GOOGLE_SHEETS_OPENAPI_URL,
    ):
        roles: List[Dict[str, Any]] = self._default_roles
        conv_uuid = get_conv_uuid(conv_id=conv_id)

        kwargs_to_patch = {
            "user_id": user_id,
            "conv_uuid": conv_uuid,
        }

        super().__init__(
            task=task,
            user_id=user_id,
            conv_id=conv_id,
            roles=roles,
            create_toolbox_func=create_toolbox_func,
            openapi_url=openapi_url,
            kwargs_to_patch=kwargs_to_patch,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            config_list=config_list,
        )

        self._add_google_ads_tools()

    def _add_google_ads_tools(self) -> None:
        self.google_ads_toolbox = create_google_ads_expert_toolbox(
            self.user_id,
            self.conv_id,
        )
        for agent in self.members:
            if agent.name == "google_ads_expert":
                self.google_ads_toolbox.add_to_agent(agent, self.user_proxy)

    @property
    def _task(self) -> str:
        return f"""You are a team in charge editing Google Sheets and creating new Google Ads resources.

Here is the current customers brief/information we have gathered for you as a starting point:
{self.task}
"""

    @property
    def _guidelines(self) -> str:
        return """### Guidelines
1. Do NOT repeat the content of the previous messages nor repeat your role.
2. When sending requests to the Google Sheets API, use user_id=-1, someone else will handle the authentication.
3.1. Your task is to 'get_all_file_names_get_all_file_names_get' endpoint from the Google Sheets API.
3.2. If you receive "User hasn't grant access yet!" from the Google Sheets API, use the Google Sheets API 'get_login_url_login_get' endpoint to authenticate
- Use user_id=-1 and conv_uuid="abc" (The correct values will be injected by the system).
- If you receive a login url, forward it to the client by using the 'reply_to_client' function.
- Do NOT use smart suggestions when forwarding the login url to the client!
4. Once you have the file names, you must determine the id of the Google spreadsheet template and the id of the spreadsheet with new routes.
Use reply_to_client command to check if you found the correct files by providing the file names. Do NOT mention all the files, only the ones that are relevant.
5. In the template spreadsheet, you must must check that 'Campaigns', 'ad Groups', 'Keywords' and 'Ads' titles exist (by using 'get_all_sheet_titles_get_all_sheet_titles_get').
6. In the spreadsheet with new routes, you must find the title of the sheet with new routes (by using 'get_all_sheet_titles_get_all_sheet_titles_get').
7. Once you have all the necessary information, use 'process_spreadsheet_process_spreadsheet_post' endpoint to process the spreadsheet.
- query parameters: user_id, template_spreadsheet_id, new_campaign_spreadsheet_id, new_campaign_sheet_title
8. Once the endpoint is successful write the message to the client that the new sheet has been created in the same spreadsheet as the new routes sheet.
9. If the user verifies that everything is correct, google_ads_expert should create Google Ads resources by using the 'create_google_ads_resources' function.

ALL ENDPOINT PARAMETERS ARE MANDATORY (even if the documentation says they are optional).
"""

    @property
    def _commands(self) -> str:
        return f"""## Commands
Only News_reporter has access to the following command:
1. {REPLY_TO_CLIENT_COMMAND}
"smart_suggestions": {{
    'suggestions': ['Use Sheet with title "New"'],
    'type': 'oneOf'
}}

2. Only Google_sheets_expert has access to Google Sheets API and can read and edit Google Sheets.

3. Only Google_ads_expert has access to the 'create_google_ads_resources' function.
"""

    @classmethod
    def get_capabilities(cls) -> str:
        return "Able to read and edit Google Sheets."

    @classmethod
    def get_brief_template(cls) -> str:
        return "We need id of Google spreadsheet template and id of the spreadsheet with new routes."
