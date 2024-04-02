import functools
import inspect
import logging
import types
from typing import Any, Callable, Dict, NamedTuple, Optional, TypeVar

from autogen.agentchat import ConversableAgent, UserProxyAgent

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


class FunctionInfo(NamedTuple):
    function: Callable[..., Any]
    name: str
    description: str


def _args_kwargs_to_kwargs(
    func: Callable[..., Any], args: Any, kwargs: Any
) -> Dict[str, Any]:
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())

    if "context" in param_names:
        if len(param_names) != len(args) + len(kwargs) + 1:
            raise ValueError(
                f"Wrong number of arguments for function '{func.__name__}' ({len(args) + len(kwargs)}), should be {len(param_names) - 1}."
            )

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
        self._functions: Dict[str, FunctionInfo] = {}
        self._context: Optional[Any] = None

    def add_function(
        self, description: str, *, name: Optional[str] = None
    ) -> Callable[[F], F]:
        def decorator(
            f: F, name: Optional[str] = name, description: str = description
        ) -> F:
            if name is None:
                name = f.__name__
            if name in self._functions:
                raise ValueError(f"Function with name {name} already added.")
            self._functions[name] = FunctionInfo(f, name, description)

            return f

        return decorator

    def get_function_info(self, name: str) -> FunctionInfo:
        return self._functions[name]

    def get_function(self, name: str) -> Callable[..., Any]:
        return self._functions[name].function

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
                context = self.get_context()
                new_kwargs = _args_kwargs_to_kwargs(f, args, kwargs)
                print(
                    f"Injecting context {context} into {f.__name__}: {args=}, {kwargs=} -> {new_kwargs=}"
                )
                return f(context=context, **new_kwargs)

            new_function = types.FunctionType(
                wrapper.__code__,
                wrapper.__globals__,
                f"{f.__name__}_injected",
                wrapper.__defaults__,
                wrapper.__closure__,
            )
            new_function.__signature__ = new_signature  # type: ignore[attr-defined]

            info = FunctionInfo(new_function, info.name, info.description)

        return info

    def add_to_agent(
        self, agent: ConversableAgent, user_proxy: Optional[UserProxyAgent] = None
    ) -> Dict[str, FunctionInfo]:
        if "tools" not in agent.llm_config or agent.llm_config["tools"] is None:
            agent.llm_config["tools"] = []

        # inject context into all the functions where needed
        retval = {
            name: self._inject_context(info) for name, info in self._functions.items()
        }

        # register the functions with the agent and user_proxy if needed
        for info in retval.values():
            agent.register_for_llm(name=info.name, description=info.description)(
                info.function
            )
            if user_proxy is not None:
                user_proxy.register_for_execution(name=info.name)(info.function)
            else:
                logger.warning(
                    f"UserProxyAgent not provided. Registering {info.name} for execution with {agent.name}."
                )
                agent.register_for_llm(name=info.name, description=info.description)(
                    info.function
                )

        print(f"add_to_agent(): {retval=}")

        return retval

    def set_context(self, context: Any) -> None:
        self._context = context

    def get_context(self) -> Optional[Any]:
        return self._context