import functools
import inspect
from types import MethodType
from typing import Any, Callable, Dict, Optional

from autogen.agentchat import ConversableAgent
from fastagency.openapi.client import Client

_org_register_for_execution: Optional[Callable[..., None]] = None


def _preprocess_decorator(original_f: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(original_f)
    def wrapper(*args: Any, **kwargs: Dict[str, Any]) -> Any:
        kwargs["city"] = "San Francisco"  # type: ignore[assignment]

        return original_f(*args, **kwargs)

    return wrapper


def get_patch_patch_register_for_execution(client: Client) -> Callable[..., None]:
    def _patch_register_for_execution() -> None:
        global _org_register_for_execution

        if _org_register_for_execution is None:
            _org_register_for_execution = Client.register_for_execution

        def register_for_execution(
            self: Client,
            agent: ConversableAgent,
        ) -> None:
            global _org_register_for_execution

            patched_regiered_funcs = []
            for f in self.registered_funcs:
                # get input parameters of f
                sig = inspect.signature(f)
                param_names = list(sig.parameters.keys())

                if "city" in param_names:
                    patched_f = _preprocess_decorator(f)
                    patched_regiered_funcs.append(patched_f)
                else:
                    patched_regiered_funcs.append(f)

            self.registered_funcs = patched_regiered_funcs

            _org_register_for_execution(self, agent)

        # mock register_for_execution on the instance level
        client.register_for_execution = MethodType(register_for_execution, client)

    return _patch_register_for_execution
