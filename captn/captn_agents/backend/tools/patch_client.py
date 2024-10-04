import functools
from types import MethodType
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from autogen.agentchat import ConversableAgent
from fastagency.api.openapi.client import OpenAPI

_org_register_for_execution: Optional[Callable[..., None]] = None


def _preprocess_decorator(
    original_f: Callable[..., Any], kwargs_to_patch: Dict[str, Any]
) -> Callable[..., Any]:
    @functools.wraps(original_f)
    def wrapper(*args: Any, **kwargs: Dict[str, Any]) -> Any:
        for k, v in kwargs_to_patch.items():
            if k in kwargs:
                kwargs[k] = v

        return original_f(*args, **kwargs)

    return wrapper


def get_patch_register_for_execution(
    client: OpenAPI, kwargs_to_patch: Dict[str, Any]
) -> Callable[..., None]:
    def _patch_register_for_execution() -> None:
        global _org_register_for_execution

        if _org_register_for_execution is None:
            _org_register_for_execution = OpenAPI._register_for_execution

        def register_for_execution(
            self: OpenAPI,
            agent: ConversableAgent,
            functions: Iterable[str | Mapping[str, Mapping[str, str]]] | None = None,
        ) -> None:
            global _org_register_for_execution

            patched_regiered_funcs = []
            for f in self.registered_funcs:
                patched_f = _preprocess_decorator(f, kwargs_to_patch)
                patched_regiered_funcs.append(patched_f)

            self.registered_funcs = patched_regiered_funcs

            _org_register_for_execution(self, agent, functions)

        # mock register_for_execution on the instance level
        client._register_for_execution = MethodType(register_for_execution, client)

    return _patch_register_for_execution
