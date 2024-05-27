import pytest

from captn.captn_agents.backend.config import Config


class TestConfig:
    _common_vars = [
        "AZURE_API_VERSION",
        "AZURE_API_ENDPOINT",
        "AZURE_GPT4_MODEL",
        "AZURE_GPT35_MODEL",
        "AZURE_OPENAI_API_KEY",
    ]
    _message = "Make sure you set the following environment variables: " + ", ".join(
        _common_vars
    )

    def test_config_list_gpt_3_5(self) -> None:
        config_list_gpt_3_5 = Config().config_list_gpt_3_5

        assert config_list_gpt_3_5 != [], self._message

    def test_config_list_gpt_3_5_fail(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AZURE_GPT35_MODEL")

        config_list_gpt_3_5 = Config().config_list_gpt_3_5

        assert config_list_gpt_3_5 == [], self._message

    def test_config_list_gpt_4(self) -> None:
        config_list_gpt_4 = Config().config_list_gpt_4

        assert config_list_gpt_4 != [], self._message

    def test_config_list_gpt_4_fail(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AZURE_GPT4_MODEL")

        config_list_gpt_4 = Config().config_list_gpt_4

        assert config_list_gpt_4 == [], self._message

    def test_config_list_gpt_4o(self) -> None:
        config_list_gpt_4o = Config().config_list_gpt_4o

        assert config_list_gpt_4o != [], self._message

    def test_config_list_gpt_4o_fail(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AZURE_GPT4O_MODEL")

        config_list_gpt_4o = Config().config_list_gpt_4o

        assert config_list_gpt_4o == [], self._message
