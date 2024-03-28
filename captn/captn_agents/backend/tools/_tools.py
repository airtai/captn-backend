from contextlib import contextmanager
from contextvars import ContextVar
import functools
import inspect
import types
from typing import Any, Callable, Iterator, List, NamedTuple, Optional, Tuple, TypeVar

from autogen.agentchat import ConversableAgent, UserProxyAgent

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])

class FunctionInfo(NamedTuple):
    function: Callable[..., Any]
    name: str
    description: str

class ToolboxContext:
    _context: ContextVar[Optional[Any]] = ContextVar("context")
    _context.set(None)

    @staticmethod
    def get_context() -> Any:
        return ToolboxContext._context.get()
        ...

    @contextmanager
    @staticmethod
    def set_context(context: Any) -> Iterator[None]:
        token = ToolboxContext._context.set(context)
        try:
            yield
        finally:
            ToolboxContext._context.reset(token)

def _args_kwargs_to_kwargs(func, args, kwargs):
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())

    # Map `args` to their corresponding parameter names
    args_as_kwargs = {}
    i = 0
    for arg in args:
        if param_names[i] == "context":
            i += 1
        args_as_kwargs[param_names[i]] = arg
        i += 1

    # Merge `args_as_kwargs` with `kwargs`, giving precedence to `kwargs`
    combined_kwargs = {**args_as_kwargs, **kwargs}

    return combined_kwargs

class Toolbox:
    def __init__(self) -> None:
        self._functions: List[FunctionInfo] = []

    def add_function(self, f: Callable[..., Any], description: str, *, name: Optional[str] = None) -> None:
        if name is None:
            name = f.__name__
        self._functions.append(FunctionInfo(f, name, description))

    def _inject_context(self, info: FunctionInfo) -> FunctionInfo:
        """Injects the context into the function if it has a context parameter.

        Check if the function has context as a parameter using inspect.signature.
        If it does, return a new function that injects the context into the function

        Args:
            info (FunctionInfo): The function to prepare.

        Returns:
            FunctionInfo: The prepared function.

        """
        f = info.function
        signature = inspect.signature(f)
        if "context" in signature.parameters.keys():
            signature = inspect.signature(f)
            new_params = [v for k, v in signature.parameters.items() if k != "context"]
            new_signature = signature.replace(parameters=new_params)

            # remove context from the signature and create a new function that injects the context
            @functools.wraps(f)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                context = ToolboxContext.get_context()
                new_kwargs = _args_kwargs_to_kwargs(f, args, kwargs)
                print(f"Injecting context {context} into {f.__name__}: {args=}, {kwargs=} -> {new_kwargs=}")
                return f(context=context, **new_kwargs)

            new_function = types.FunctionType(wrapper.__code__, wrapper.__globals__, f"{f.__name__}_injected", wrapper.__defaults__, wrapper.__closure__)
            new_function.__signature__ = new_signature

            info = FunctionInfo(new_function, info.name, info.description)

        return info

    def add_to_agent(self, agent: ConversableAgent, user_proxy: Optional[UserProxyAgent] = None) -> None:
        for info in self._functions:
            info = self._inject_context(info)
            agent.register_for_llm(name=info.name, description=info.description)(info.function)
            if user_proxy is not None:
                user_proxy.register_for_llm(name=info.name, description=info.description)(info.function)
