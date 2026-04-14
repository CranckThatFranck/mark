import ast
import json
import logging
from typing import Any, Callable


logger = logging.getLogger(__name__)


_PATCHED = False


def _get_field(container: Any, key: str, default=None):
    if isinstance(container, dict):
        return container.get(key, default)
    return getattr(container, key, default)


def _set_field(container: Any, key: str, value: Any):
    if isinstance(container, dict):
        container[key] = value
        return
    setattr(container, key, value)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _convert_scalar(raw: str):
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered == "null":
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        pass
    if (raw.startswith("\"") and raw.endswith("\"")) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def _parse_key_value_pairs(raw: str) -> dict[str, Any] | None:
    if not raw or "," not in raw and "=" not in raw and ":" not in raw:
        return None

    result = {}
    chunks = [part.strip() for part in raw.split(",") if part.strip()]
    if not chunks:
        return None

    for chunk in chunks:
        delimiter = "=" if "=" in chunk else ":" if ":" in chunk else None
        if delimiter is None:
            return None
        key_part, value_part = chunk.split(delimiter, 1)
        key = key_part.strip().strip("\"'")
        value = value_part.strip()
        if not key:
            return None
        result[key] = _convert_scalar(value)

    return result


def sanitize_tool_arguments(raw_arguments: Any, tool_name: str = "") -> dict[str, Any]:
    normalized_tool = str(tool_name or "").strip().lower()

    if raw_arguments is None:
        return {
            "arguments": "{}",
            "changed": True,
            "strategy": "none_to_empty_object",
        }

    if isinstance(raw_arguments, (dict, list)):
        payload = raw_arguments
        if normalized_tool == "execute" and isinstance(payload, list):
            payload = {"value": payload}
        return {
            "arguments": _canonical_json(payload),
            "changed": True,
            "strategy": "native_object",
        }

    if not isinstance(raw_arguments, str):
        return {
            "arguments": _canonical_json({"raw_arguments": str(raw_arguments)}),
            "changed": True,
            "strategy": "non_string_wrapped",
        }

    stripped = raw_arguments.strip()
    if not stripped:
        return {
            "arguments": "{}",
            "changed": True,
            "strategy": "empty_string_to_empty_object",
        }

    try:
        parsed_json = json.loads(stripped)
        if normalized_tool == "execute" and not isinstance(parsed_json, dict):
            wrapped = {"code": parsed_json} if isinstance(parsed_json, str) else {"value": parsed_json}
            canonical = _canonical_json(wrapped)
            return {
                "arguments": canonical,
                "changed": canonical != stripped,
                "strategy": "json_wrapped_for_execute",
            }

        canonical = _canonical_json(parsed_json)
        return {
            "arguments": canonical,
            "changed": canonical != stripped,
            "strategy": "canonical_json",
        }
    except json.JSONDecodeError:
        pass

    try:
        parsed_literal = ast.literal_eval(stripped)
        if normalized_tool == "execute" and isinstance(parsed_literal, str):
            parsed_literal = {"code": parsed_literal}
        elif normalized_tool == "execute" and not isinstance(parsed_literal, dict):
            parsed_literal = {"value": parsed_literal}

        canonical = _canonical_json(parsed_literal)
        return {
            "arguments": canonical,
            "changed": True,
            "strategy": "python_literal",
        }
    except Exception:
        pass

    wrapped_candidate = "{" + stripped + "}"
    for strategy, candidate in (("wrapped_json_like", wrapped_candidate), ("raw", stripped)):
        try:
            parsed = json.loads(candidate)
            if normalized_tool == "execute" and not isinstance(parsed, dict):
                parsed = {"code": parsed} if isinstance(parsed, str) else {"value": parsed}
            canonical = _canonical_json(parsed)
            return {
                "arguments": canonical,
                "changed": True,
                "strategy": strategy,
            }
        except Exception:
            pass
        try:
            parsed_literal = ast.literal_eval(candidate)
            if normalized_tool == "execute" and not isinstance(parsed_literal, dict):
                parsed_literal = {"code": parsed_literal} if isinstance(parsed_literal, str) else {"value": parsed_literal}
            canonical = _canonical_json(parsed_literal)
            return {
                "arguments": canonical,
                "changed": True,
                "strategy": f"{strategy}_literal",
            }
        except Exception:
            pass

    key_values = _parse_key_value_pairs(stripped)
    if key_values is not None:
        canonical = _canonical_json(key_values)
        if normalized_tool == "execute" and "code" not in key_values and "command" not in key_values:
            canonical = _canonical_json({"code": stripped, "parsed": key_values})
        return {
            "arguments": canonical,
            "changed": True,
            "strategy": "key_value_pairs",
        }

    if normalized_tool == "execute":
        return {
            "arguments": _canonical_json({"code": raw_arguments}),
            "changed": True,
            "strategy": "execute_wrapped_code",
        }

    return {
        "arguments": _canonical_json({"raw_arguments": raw_arguments}),
        "changed": True,
        "strategy": "raw_wrapped",
    }


def _sanitize_single_tool_call(tool_call: Any) -> dict[str, Any] | None:
    function_data = _get_field(tool_call, "function")
    if function_data is None:
        return None

    tool_name = str(_get_field(function_data, "name", "") or "")
    current_arguments = _get_field(function_data, "arguments")
    sanitized = sanitize_tool_arguments(current_arguments, tool_name)

    if not sanitized["changed"]:
        return None

    _set_field(function_data, "arguments", sanitized["arguments"])
    return {
        "tool_name": tool_name or "unknown",
        "strategy": sanitized["strategy"],
    }


def _sanitize_message_payload(message: Any) -> list[dict[str, Any]]:
    updates = []

    tool_calls = _get_field(message, "tool_calls")
    if isinstance(tool_calls, list):
        for tool_call in tool_calls:
            update = _sanitize_single_tool_call(tool_call)
            if update:
                updates.append(update)

    legacy_call = _get_field(message, "function_call")
    if legacy_call is not None:
        tool_name = str(_get_field(legacy_call, "name", "") or "")
        current_arguments = _get_field(legacy_call, "arguments")
        sanitized = sanitize_tool_arguments(current_arguments, tool_name)
        if sanitized["changed"]:
            _set_field(legacy_call, "arguments", sanitized["arguments"])
            updates.append(
                {
                    "tool_name": tool_name or "unknown",
                    "strategy": f"legacy_{sanitized['strategy']}",
                }
            )

    return updates


def _sanitize_choice_payload(choice: Any) -> list[dict[str, Any]]:
    updates = []

    for message_key in ("message", "delta"):
        message = _get_field(choice, message_key)
        if message is None:
            continue

        updates.extend(_sanitize_message_payload(message))

    return updates


def sanitize_completion_payload(payload: Any) -> list[dict[str, Any]]:
    choices = _get_field(payload, "choices")
    if not isinstance(choices, list):
        return []

    updates = []
    for index, choice in enumerate(choices):
        for update in _sanitize_choice_payload(choice):
            update["choice_index"] = index
            updates.append(update)
    return updates


def sanitize_outbound_messages(messages: Any) -> list[dict[str, Any]]:
    if not isinstance(messages, list):
        return []

    updates = []
    for index, message in enumerate(messages):
        for update in _sanitize_message_payload(message):
            update["message_index"] = index
            updates.append(update)

    return updates


def _emit_updates(updates: list[dict[str, Any]], callback: Callable[[dict[str, Any]], None] | None):
    if not updates:
        return
    notify = callback or (lambda payload: logger.info(f"Tool call sanitized: {payload}"))
    for update in updates:
        notify(update)


def _wrap_sync_stream(stream_result, callback: Callable[[dict[str, Any]], None] | None):
    for chunk in stream_result:
        updates = sanitize_completion_payload(chunk)
        for update in updates:
            update["phase"] = "response"
        _emit_updates(updates, callback)
        yield chunk


async def _wrap_async_stream(stream_result, callback: Callable[[dict[str, Any]], None] | None):
    async for chunk in stream_result:
        updates = sanitize_completion_payload(chunk)
        for update in updates:
            update["phase"] = "response"
        _emit_updates(updates, callback)
        yield chunk


def install_litellm_tool_sanitizer(callback: Callable[[dict[str, Any]], None] | None = None) -> bool:
    global _PATCHED
    if _PATCHED:
        return True

    try:
        import litellm
    except Exception as exc:
        logger.warning(f"LiteLLM indisponivel para patch de saneamento: {exc}")
        return False

    original_completion = getattr(litellm, "completion", None)
    original_acompletion = getattr(litellm, "acompletion", None)

    if original_completion is None:
        logger.warning("LiteLLM completion nao encontrado; saneamento nao instalado")
        return False

    def completion_wrapper(*args, **kwargs):
        request_updates = sanitize_outbound_messages(kwargs.get("messages"))
        for update in request_updates:
            update["phase"] = "request"
        _emit_updates(request_updates, callback)

        stream_mode = bool(kwargs.get("stream"))
        response = original_completion(*args, **kwargs)
        if stream_mode:
            return _wrap_sync_stream(response, callback)

        updates = sanitize_completion_payload(response)
        for update in updates:
            update["phase"] = "response"
        _emit_updates(updates, callback)
        return response

    litellm.completion = completion_wrapper

    if callable(original_acompletion):

        async def acompletion_wrapper(*args, **kwargs):
            request_updates = sanitize_outbound_messages(kwargs.get("messages"))
            for update in request_updates:
                update["phase"] = "request"
            _emit_updates(request_updates, callback)

            stream_mode = bool(kwargs.get("stream"))
            response = await original_acompletion(*args, **kwargs)
            if stream_mode:
                return _wrap_async_stream(response, callback)

            updates = sanitize_completion_payload(response)
            for update in updates:
                update["phase"] = "response"
            _emit_updates(updates, callback)
            return response

        litellm.acompletion = acompletion_wrapper

    _PATCHED = True
    logger.info("Patch de saneamento de tool calls LiteLLM instalado")
    return True
