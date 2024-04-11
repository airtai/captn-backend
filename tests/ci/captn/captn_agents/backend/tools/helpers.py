import re
from typing import Any, Dict


def check_llm_config_total_tools(llm_config: Dict[str, Any], total_tools: int) -> None:
    assert "tools" in llm_config, f"{llm_config.keys()=}"
    assert (
        len(llm_config["tools"]) == total_tools
    ), f"{len(llm_config['tools'])=}, {llm_config['tools']=}"
    for i in range(len(llm_config["tools"])):
        assert (
            llm_config["tools"][i]["type"] == "function"
        ), f"{llm_config['tools'][i]['type']=}"


def check_llm_config_descriptions(
    llm_config: Dict[str, Any], name_desc_dict: Dict[str, str]
) -> None:
    names = [
        function_wrapper["function"]["name"] for function_wrapper in llm_config["tools"]
    ]
    for _, (name, desc) in enumerate(name_desc_dict.items()):
        if name not in names:
            raise AssertionError(f"{name=} not in {names=}")

        # get index of the function in the list names
        i = names.index(name)

        function_config = llm_config["tools"][i]["function"]

        assert function_config["name"] == name, function_config["name"]
        if desc is not None:
            assert (
                re.match(desc, function_config["description"]) is not None
            ), function_config["description"]
