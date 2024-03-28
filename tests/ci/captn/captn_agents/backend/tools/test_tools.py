
import inspect
from typing import Any, Iterator
from typing_extensions import Annotated
from unittest.mock import MagicMock
import pytest

from captn.captn_agents.backend.tools._tools import Toolbox, FunctionInfo, ToolboxContext

class TestToolboxContext():
    def test_get_context(self) -> None:
        context = object()
        with ToolboxContext.set_context(context):
            assert ToolboxContext.get_context() == context

class TestToolbox():
    @pytest.fixture(autouse=True)
    def setup(self) -> Iterator[None]:

        yield

    def test_inject_context_noop(self) -> None:
        toolbox = Toolbox()

        def function(i: int, s: str) -> None:
            pass

        new_info = toolbox._inject_context(FunctionInfo(function, "function", "description"))

        old_signature = inspect.signature(function)
        new_signature = inspect.signature(new_info.function)

        assert old_signature == new_signature

    def test_inject_context_successfully(self) -> None:
        toolbox = Toolbox()

        mock = MagicMock(return_value=3.14)
        def f(i: int, context: Any, s: str) -> float:
            return mock(i, context, s)

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

        with ToolboxContext.set_context(context):
            result = new_function(42, "hello")

            assert result == mock.return_value
            mock.assert_called_once_with(42, context, "hello")


    def test_add_function_with_simple_parameters(self) -> None:
        toolbox = Toolbox()

        def function(i: Annotated[int, "an integer parameter"], s: Annotated[str, "a greeting"]) -> str:
            return "ok"
