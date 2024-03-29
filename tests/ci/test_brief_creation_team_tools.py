from typing import Any, Dict

from autogen.agentchat import AssistantAgent

from captn.captn_agents.backend.config import Config
from captn.captn_agents.backend.tools._brief_creation_team_tools import (
    add_delagate_task,
    add_get_brief_template,
)


class TestTools:
    def setup(self) -> None:
        self.llm_config = {
            "config_list": Config().config_list_gpt_3_5,
        }

    def test_llm_config(self) -> None:
        def _check_llm_config(
            llm_config: Dict[str, Any], name_desc_dict: Dict[str, str]
        ) -> None:
            assert "tools" in llm_config, f"{llm_config.keys()=}"
            assert len(llm_config["tools"]) == 2, f"{llm_config['tools']=}"
            assert (
                llm_config["tools"][0]["type"] == "function"
            ), f"{llm_config['tools'][0]['type']=}"

            for i, (name, desc) in enumerate(name_desc_dict.items()):
                function_config = llm_config["tools"][i]["function"]

                assert function_config["name"] == name, function_config
                assert function_config["description"] == desc, function_config[
                    "description"
                ]

        agent = AssistantAgent(name="agent", llm_config=self.llm_config)

        add_get_brief_template(agent=agent)
        add_delagate_task(agent=agent, user_id=123, conv_id=567)

        llm_config = agent.llm_config
        name_desc_dict = {
            "get_brief_template": "Get the brief template which will be used by the selected team",
            "delagate_task": "Delagate the task to the selected team",
        }
        _check_llm_config(llm_config, name_desc_dict)
