REPLY_TO_CLIENT_COMMAND = """'reply_to_client': Ask the client for additional information, params: (message: string, completed: bool, smart_suggestions: Optional[Dict[str, Union[str, List[str]]]])
The 'message' parameter must contain all information useful to the client, because the client does not see your team's conversation (only the information sent in the 'message' parameter)
As we send this message to the client, pay attention to the content inside it. We are a digital agency and the messages we send must be professional.
Never reference 'client' within the message:
e.g. "We need to ask client for the approval" should be changed to "Do you approve these changes?"
It is VERY important that you use the 'smart_suggestions' parameter!
Use it so the client can easily choose between multiple options and make a quick reply by clicking on the suggestion.
e.g.:"""

GET_INFO_FROM_THE_WEB_COMMAND = """'get_info_from_the_web_page': Retrieve wanted information from the web page, params: (url: string)
It should be used only for the clients web page(s), final_url(s) etc.
This command should be used for retrieving the information from clients web page.
If this command fails to retrieve the information, only then you should ask the client for the additional information about his business/web page etc."""

MODIFICATION_FUNCTIONS_INSTRUCTIONS = """The following commands make permanent changes. In all of them you must use the following two parameters:
- clients_approval_message: With this message, the client confirms that he is aware of the changes you will make
(if the message is not detailed enough, we are threatened with a lawsuit)
- modification_question: This parameter MUST be the SAME string as the 'proposed_changes' parameter you have used in the 'ask_client_for_permission' function!
If you do not use the same string, the modification will NOT be made! Do NOT forget this!"""
