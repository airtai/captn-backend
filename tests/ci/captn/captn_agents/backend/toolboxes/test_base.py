import inspect
import unittest
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Iterator
from unittest.mock import MagicMock

import pytest
from autogen.agentchat import AssistantAgent, UserProxyAgent
from typing_extensions import Annotated

from captn.captn_agents.backend.toolboxes.base import (
    FunctionInfo,
    Toolbox,
    _args_kwargs_to_kwargs,
)


def test_args_kwargs_to_kwargs() -> None:
    def f1(i: int, s: str) -> None:
        pass  # pragma: no cover

    assert _args_kwargs_to_kwargs(f1, (42, "hello"), {}) == {"i": 42, "s": "hello"}
    assert _args_kwargs_to_kwargs(f1, (42,), {"s": "hello"}) == {"i": 42, "s": "hello"}
    assert _args_kwargs_to_kwargs(f1, (), {"i": 42, "s": "hello"}) == {
        "i": 42,
        "s": "hello",
    }

    def f2(i: int, context: Any, s: str) -> None:
        pass  # pragma: no cover

    assert _args_kwargs_to_kwargs(f2, (42, "hello"), {}) == {"i": 42, "s": "hello"}
    assert _args_kwargs_to_kwargs(f2, (42,), {"s": "hello"}) == {"i": 42, "s": "hello"}
    assert _args_kwargs_to_kwargs(f2, (), {"i": 42, "s": "hello"}) == {
        "i": 42,
        "s": "hello",
    }


class TestToolbox:
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:
        def f(
            i: Annotated[int, "an integer parameter"], s: Annotated[str, "a greeting"]
        ) -> str:
            return "ok"

        @dataclass
        class MyContext:
            id: int
            name: str
            mobile: str

        def g(
            i: Annotated[int, "an integer parameter"],
            context: MyContext,
            s: Annotated[str, "a greeting"],
        ) -> str:
            return "ok"

        self.f = f
        self.g = g

        yield

    def test_inject_context_noop(self) -> None:
        toolbox = Toolbox()

        def function(i: int, s: str) -> None:
            pass

        new_info = toolbox._inject_context(
            FunctionInfo(function, "function", "description")
        )

        old_signature = inspect.signature(function)
        new_signature = inspect.signature(new_info.function)

        assert old_signature == new_signature

    def test_inject_context_successfully(self) -> None:
        toolbox = Toolbox()

        mock = MagicMock(return_value=3.14)

        def f(i: int, context: Any, s: str) -> float:
            return mock(i, context, s)  # type: ignore[no-any-return]

        new_info = toolbox._inject_context(FunctionInfo(f, "function", "description"))

        old_signature = inspect.signature(f)
        new_signature = inspect.signature(new_info.function)

        assert "context" in old_signature.parameters.keys()
        assert "context" not in new_signature.parameters.keys()

        new_function = new_info.function
        context = object()

        result = f(42, context, "hello")
        mock.assert_called_once_with(42, context, "hello")
        mock.reset_mock()

        toolbox.set_context(context)
        result = new_function(42, "hello")

        assert result == mock.return_value
        mock.assert_called_once_with(42, context, "hello")

    def test_add_function_with_simple_parameters(self) -> None:
        toolbox = Toolbox()

        toolbox.add_function("this is description of the function f")(self.f)
        assert set(toolbox._function_infos.keys()) == {"f"}

        f_info = toolbox.get_function_info("f")
        assert toolbox.functions.f == self.f  # type: ignore[attr-defined]
        assert f_info.function._origin == self.f  # type: ignore[attr-defined]
        assert f_info.name == "f"
        assert f_info.description == "this is description of the function f"

        toolbox.add_function("this is description of the function g")(self.g)
        assert set(toolbox._function_infos.keys()) == {"f", "g"}

        g_info = toolbox.get_function_info("g")
        assert toolbox.functions.g == self.g  # type: ignore[attr-defined]
        assert g_info.function._origin == self.g  # type: ignore[attr-defined]
        assert g_info.name == "g"
        assert g_info.description == "this is description of the function g"

    def test_add_function_with_custom_name(self) -> None:
        toolbox = Toolbox()

        toolbox.add_function(
            "this is description of the function f", name="function_f"
        )(self.f)
        assert toolbox.functions.function_f == self.f  # type: ignore[attr-defined]

        f_info = toolbox.get_function_info("function_f")
        assert f_info.function._origin == self.f  # type: ignore[attr-defined]
        assert f_info.name == "function_f"
        assert f_info.description == "this is description of the function f"

        toolbox.add_function("this is description of the function", name="function_g")(
            self.g
        )
        assert toolbox.functions.function_g == self.g  # type: ignore[attr-defined]

        g_info = toolbox.get_function_info("function_g")
        assert g_info.function._origin == self.g  # type: ignore[attr-defined]
        assert g_info.name == "function_g"
        assert g_info.description == "this is description of the function"

    def test_add_function_with_same_name(self) -> None:
        toolbox = Toolbox()

        toolbox.add_function(
            "this is description of the function f", name="function_f"
        )(self.f)

        with pytest.raises(ValueError):
            toolbox.add_function(
                "this is description of the function", name="function_f"
            )(self.g)

    def test_add_function_with_same_function(self) -> None:
        toolbox = Toolbox()

        toolbox.add_function("this is description of the function f")(self.f)

        toolbox.add_function(
            "this is description of the function f", name="yet_another_f"
        )(self.f)

        f_info = toolbox.get_function_info("f")
        yet_another_f_info = toolbox.get_function_info("yet_another_f")
        assert f_info.function._origin == yet_another_f_info.function._origin == self.f  # type: ignore[attr-defined]
        assert f_info.name == "f"
        assert yet_another_f_info.name == "yet_another_f"
        assert (
            f_info.description
            == yet_another_f_info.description
            == "this is description of the function f"
        )

    @pytest.fixture
    def agent_mocks(self) -> Dict[str, MagicMock]:
        # agent

        agent = MagicMock()
        agent.register_for_llm = MagicMock()

        register_for_llm = MagicMock()

        def agent_side_effect(*args: Any, **kwargs: Any) -> Callable[..., Any]:
            def _inner(f: Callable[..., Any]) -> Callable[..., Any]:
                register_for_llm(*args, **kwargs, function=f)
                return f

            return _inner

        agent.register_for_llm.side_effect = agent_side_effect

        # user proxy

        user_proxy = MagicMock()
        user_proxy.register_for_execution = MagicMock()

        register_for_execution = MagicMock()

        def user_proxy_side_effect(*args: Any, **kwargs: Any) -> Callable[..., Any]:
            def _inner(f: Callable[..., Any]) -> Callable[..., Any]:
                register_for_execution(*args, **kwargs, function=f)
                return f

            return _inner

        user_proxy.register_for_execution.side_effect = user_proxy_side_effect

        return dict(  # noqa: C408 unnecessary dict call
            agent=agent,
            register_for_llm=register_for_llm,
            user_proxy=user_proxy,
            register_for_execution=register_for_execution,
        )

    def test_add_functions_to_agent_with_mock(
        self, agent_mocks: Dict[str, MagicMock]
    ) -> None:
        # create a mock agent and user_proxy
        agent = agent_mocks["agent"]
        register_for_llm = agent_mocks["register_for_llm"]
        user_proxy = agent_mocks["user_proxy"]
        register_for_execution = agent_mocks["register_for_execution"]

        toolbox = Toolbox()

        toolbox.add_function("this is description of the function f")(self.f)
        toolbox.add_function("this is description of the function g")(self.g)

        registered_functions = toolbox.add_to_agent(agent, user_proxy)
        assert len(registered_functions) == 2
        assert "f" in registered_functions
        assert "g" in registered_functions

        wrapped_f = registered_functions["f"].function
        assert wrapped_f._origin == self.f  # type: ignore[attr-defined]
        assert (
            FunctionInfo(wrapped_f, "f", "this is description of the function f")
            == registered_functions["f"]
        )

        agent.register_for_llm.assert_any_call(
            name="f", description="this is description of the function f"
        )
        register_for_llm.assert_any_call(
            name="f",
            description="this is description of the function f",
            function=wrapped_f,
        )

        user_proxy.register_for_execution.assert_any_call(name="f")
        register_for_execution.assert_any_call(name="f", function=wrapped_f)

        agent.register_for_llm.assert_any_call(
            name="g", description="this is description of the function g"
        )
        register_for_llm.assert_any_call(
            name="g",
            description="this is description of the function g",
            function=registered_functions["g"].function,
        )

    def test_add_functions_to_agent_with_openai(self) -> None:
        agent = AssistantAgent(
            name="agent",
            llm_config={
                "model": "gpt-3.5-turbo",
                "api_key": "dummy",  # pragma: allowlist secret
            },
        )
        user_proxy = UserProxyAgent(name="user_proxy")

        toolbox = Toolbox()

        f = MagicMock(return_value="ok from f")

        @wraps(self.f)
        def wrapper_f(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        g = MagicMock(return_value="ok from g")

        @wraps(self.g)
        def wrapper_g(*args: Any, **kwargs: Any) -> Any:
            return g(*args, **kwargs)

        toolbox.add_function("this is description of the function f")(wrapper_f)
        toolbox.add_function("this is description of the function g")(wrapper_g)

        func_info_map = toolbox.add_to_agent(agent, user_proxy)

        tools = agent.llm_config["tools"]
        functions = [tool["function"]["name"] for tool in tools]
        assert functions == ["f", "g"]

        function_map = {name: info.function for name, info in func_info_map.items()}
        assert list(function_map.keys()) == ["f", "g"]
        assert function_map["f"]._origin == toolbox.functions.f  # type: ignore[attr-defined]

        context = object()
        toolbox.set_context(context)

        actual = user_proxy.function_map["f"](42, "hello")
        assert actual == "ok from f"
        f.assert_called_once_with(42, "hello")

        actual = user_proxy.function_map["g"](123, "hi")
        assert actual == "ok from g"
        g.assert_called_once_with(i=123, context=context, s="hi")

        with pytest.raises(
            ValueError, match="Wrong number of arguments for function 'g'"
        ):
            user_proxy.function_map["g"](123, context, "hi")

        # test mockup
        with unittest.mock.patch.object(
            toolbox.functions, "f", return_value="mocked"
        ) as mock_f:
            actual = user_proxy.function_map["f"](42, "hello")
            assert actual == "mocked"
            mock_f.assert_called_once_with(42, "hello")
