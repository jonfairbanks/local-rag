import hashlib
import json
import os

import streamlit as st
import streamlit.components.v1 as components

PERSISTED_SETTING_TYPES = {
    "ollama_endpoint": str,
    "embedding_backend": str,
    "ollama_embedding_model": str,
    "embedding_model": str,
    "other_embedding_model": str,
    "selected_model": str,
    "top_k": int,
    "chat_mode": str,
    "chunk_size": int,
    "chunk_overlap": int,
    "advanced": bool,
}
BROWSER_STORAGE_KEY = "local-rag:settings"
_COMPONENT_PATH = os.path.join(os.path.dirname(__file__), "browser_storage_component")
_browser_storage_component = components.declare_component(
    "browser_storage", path=_COMPONENT_PATH
)


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise ValueError("invalid boolean")


def apply_persisted_settings(state, raw_settings):
    """Apply valid browser-persisted settings before defaults initialize."""
    for key, expected_type in PERSISTED_SETTING_TYPES.items():
        if key not in raw_settings:
            continue
        raw_value = raw_settings[key]
        if key == "ollama_endpoint" and raw_value == "":
            continue
        try:
            if expected_type is bool:
                value = _coerce_bool(raw_value)
            else:
                value = expected_type(raw_value)
        except (TypeError, ValueError):
            continue
        state[key] = value


def serialize_persisted_settings(state):
    """Return only browser-persistable user settings from session state."""
    return {
        key: state[key]
        for key in PERSISTED_SETTING_TYPES
        if key in state
        and state[key] is not None
        and not (key == "ollama_endpoint" and state[key] == "")
    }


def deserialize_persisted_settings(payload):
    """Return persisted settings from a browser localStorage JSON payload."""
    if not payload:
        return {}
    try:
        settings = json.loads(payload)
    except (TypeError, ValueError):
        return {}
    if not isinstance(settings, dict):
        return {}
    return settings


def browser_storage_payload(settings):
    """Return the JSON string stored in browser localStorage."""
    return json.dumps(settings)


def option_index(options, selected_value):
    """Return the selectbox index for a restored value, or a stable fallback."""
    if not options:
        return None
    try:
        return options.index(selected_value)
    except ValueError:
        return 0


def should_refresh_models_for_endpoint(state, models_key):
    """Return whether cached Ollama models belong to a different endpoint."""
    endpoint = state.get("ollama_endpoint")
    endpoint_key = f"{models_key}_endpoint"
    return models_key not in state or state.get(endpoint_key) != endpoint


def restore_settings_from_browser_storage():
    """Hydrate session state from browser localStorage once per session."""
    if st.session_state.get("browser_settings_restored"):
        return

    payload = _browser_storage_component(
        action="get",
        storage_key=BROWSER_STORAGE_KEY,
        key="restore_browser_settings",
    )
    if payload is None:
        st.stop()

    storage_payload = payload
    if isinstance(payload, dict) and "value" in payload:
        storage_payload = payload["value"]

    raw_settings = deserialize_persisted_settings(storage_payload)
    apply_persisted_settings(st.session_state, raw_settings)
    st.session_state["browser_settings_restored"] = True


def persist_settings_to_browser_storage():
    """Keep supported settings in browser localStorage so app restarts restore them."""
    if not st.session_state.get("browser_settings_restored"):
        return

    serialized = serialize_persisted_settings(st.session_state)
    storage_hash = hashlib.sha256(
        json.dumps(serialized, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    _browser_storage_component(
        action="set",
        storage_key=BROWSER_STORAGE_KEY,
        value=browser_storage_payload(serialized),
        key=f"persist_browser_settings_{storage_hash}",
    )
