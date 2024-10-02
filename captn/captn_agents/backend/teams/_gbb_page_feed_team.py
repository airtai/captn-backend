from typing import Any, Callable, Dict, List, Optional

from ..toolboxes import Toolbox
from ..tools._gbb_page_feed_team_tools import create_page_feed_team_toolbox
from ._gbb_google_sheets_team import GOOGLE_SHEETS_OPENAPI_URL, GBBGoogleSheetsTeam
from ._shared_prompts import REPLY_TO_CLIENT_COMMAND


# @Team.register_team("gbb_page_feed_team")
class GBBPageFeedTeam(GBBGoogleSheetsTeam):
    def __init__(
        self,
        *,
        task: str,
        user_id: int,
        conv_id: int,
        work_dir: str = "gbb_page_feed_team",
        max_round: int = 80,
        seed: int = 42,
        temperature: float = 0.2,
        config_list: Optional[List[Dict[str, str]]] = None,
        create_toolbox_func: Callable[
            [int, int, Dict[str, Any]], Toolbox
        ] = create_page_feed_team_toolbox,
        openapi_url: str = GOOGLE_SHEETS_OPENAPI_URL,
    ):
        super().__init__(
            task=task,
            user_id=user_id,
            conv_id=conv_id,
            work_dir=work_dir,
            max_round=max_round,
            seed=seed,
            temperature=temperature,
            config_list=config_list,
            create_toolbox_func=create_toolbox_func,
            openapi_url=openapi_url,
        )

    @property
    def _task(self) -> str:
        return f"""You are a team in charge of updating Google Ads Page Feeds using a Google Sheets template.

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
4. Once you have the file names, you must determine the id of the Google spreadsheet template and the id of the spreadsheet with page feeds.
- page feed spreadsheet usually starts with "Permalinks_Stations_Table"
- Use reply_to_client command to check if you found the correct files by providing the file names. Do NOT mention all the files, only the ones that are relevant.
  - If you think you found the correct files, use one smart suggestion ["These are the correct files."].
- Do NOT forget this step, because the client needs to confirm that you have found the correct files, otherwise you will be penalized!
- ALWAYS add final sentence "If these are NOT the correct files, please paste the whole URL of the correct files."
5. In the template spreadsheet, you must must check that 'Accounts' and 'Page Feeds' titles exist (by using 'get_all_sheet_titles_get_all_sheet_titles_get').
- mandatory input parameters: user_id, spreadsheet_id
6. In the spreadsheet with page feeds, you must find the title of the sheet with page feeds (by using 'get_all_sheet_titles_get_all_sheet_titles_get').
- If there are multiple sheets within the spreadsheet, ask the client to choose the correct sheet.
7. Once you have the correct sheet title, you must validate the data in the page feed sheet by using 'validate_page_feed_data' function.
8. If the data is correct, you must update the page feeds in Google Ads by using 'update_page_feeds' function.

ALL ENDPOINT PARAMETERS ARE MANDATORY (even if the documentation says they are optional).

OFTEN MISTAKES:
- Do NOT forget the 'modification_function_parameters' when calling 'ask_client_for_permission' function!
- If the client wants to change the Google Ads account or refresh token, use 'change_google_ads_account_or_refresh_token' function.
- If the client wants to change the Google Sheets account, use 'get_login_url_login_get' function with 'force_new_login' parameter set to True.

ADDITIONAL NOTES:
- ALWAYS use hyperlinks to the Google Sheets UI when referring it to the client.
e.g. "Are these the correct files?\n\n1. PAGE FEEDS: [new-routes](https://docs.google.com/spreadsheets/d/insert_correct_sheet_id) \n\n2. TEMPLATES: [template](https://docs.google.com/spreadsheets/d/insert_correct_sheet_id)"
- ALWAYS use names of the sheets and google ads customer account names when referring them to the client. You can add id-s in the brackets.
"""

    @property
    def _commands(self) -> str:
        return f"""## Commands
Only Account_manager has access to the following commands:
1. {REPLY_TO_CLIENT_COMMAND}
"smart_suggestions": {{
    'suggestions': ['Use Sheet with title "New"'],
    'type': 'oneOf'
}}
2. ask_client_for_permission: Ask the client for permission to make the changes. Use this method before calling 'create_google_ads_resources'
params: (resource_details: str, function_name: str, modification_function_parameters: Dict[str, Any])
ALL parameters are mandatory, do NOT forget to include 'modification_function_parameters'. If you forget this parameter, you will be penalized!
'modification_function_parameters' should be a dictionary with the following keys:
{{
    "customer_ids_to_update":
}}

'resource_details' should use human readable names and add id-s in the brackets.

function_name: 'update_page_feeds'


3. Only Google_sheets_expert has access to Google Sheets API and can read and edit Google Sheets.
- 'get_login_url_login_get' - which will return the login url for the Google Sheets API (This can't be used for Google Ads account)
If you want to refresh google sheets token or change google sheets use 'get_login_url_login_get' with 'force_new_login' parameter set to True.

4. Only Google_ads_expert has access to the following commands:
- 'validate_page_feed_data':
parameters: template_spreadsheet_id, page_feed_spreadsheet_id, page_feed_sheet_title
- 'update_page_feeds':
parameters: customer_ids_to_update
- 'change_google_ads_account_or_refresh_token' - to change Google Ads account or refresh token (This can't be used for Google Sheets account)
"""

    @classmethod
    def get_capabilities(cls) -> str:
        return "Able update Google Ads Page Feeds."

    @classmethod
    def get_brief_template(cls) -> str:
        return "The client wants to update Google Ads Page Feeds using a Google Sheets template."
