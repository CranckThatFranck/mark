import os
import uuid
from typing import Any

from config import now_timestamp
from config_manager import (
    build_public_credentials_catalog,
    load_credentials_state,
    mask_secret,
    save_credentials_state,
)

RUNTIME_GEMINI_ENV_KEYS = (
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
)


class CredentialValidationError(ValueError):
    pass


class GeminiCredentialStore:
    def __init__(self):
        self._state = load_credentials_state()

    def reload(self):
        self._state = load_credentials_state()

    def _save(self):
        self._state = save_credentials_state(self._state)

    def _find_key_index(self, key_id: str) -> int:
        for index, item in enumerate(self._state.get("keys", [])):
            if item.get("id") == key_id:
                return index
        return -1

    def get_public_catalog(self) -> dict[str, Any]:
        return build_public_credentials_catalog(self._state)

    def get_active_key_record(self) -> dict[str, Any] | None:
        active_id = self._state.get("active_key_id")
        for item in self._state.get("keys", []):
            if item.get("id") == active_id:
                return item
        if self._state.get("keys"):
            fallback = self._state["keys"][0]
            self._state["active_key_id"] = fallback.get("id")
            self._save()
            return fallback
        return None

    def resolve_active_key(self):
        active = self.get_active_key_record()
        if active:
            return {
                "source": "persisted",
                "id": active.get("id"),
                "label": active.get("label"),
                "masked": mask_secret(active.get("secret")),
                "secret": active.get("secret"),
            }

        for env_name in RUNTIME_GEMINI_ENV_KEYS:
            env_key = os.environ.get(env_name, "").strip()
            if env_key:
                return {
                    "source": "environment",
                    "id": f"environment:{env_name.lower()}",
                    "label": env_name,
                    "masked": mask_secret(env_key),
                    "secret": env_key,
                }

        return {
            "source": "missing",
            "id": None,
            "label": "missing",
            "masked": "",
            "secret": "",
        }

    def apply_to_environment(self) -> dict[str, Any]:
        resolved = self.resolve_active_key()
        secret = resolved.get("secret")
        if secret:
            for env_name in RUNTIME_GEMINI_ENV_KEYS:
                os.environ[env_name] = secret
        else:
            for env_name in RUNTIME_GEMINI_ENV_KEYS:
                os.environ.pop(env_name, None)
        return {
            "source": resolved.get("source"),
            "id": resolved.get("id"),
            "label": resolved.get("label"),
            "masked": resolved.get("masked"),
            "secret": secret or "",
        }

    def _validate_secret(self, secret: str):
        if not isinstance(secret, str) or not secret.strip():
            raise CredentialValidationError("Chave Gemini invalida")

    def add_key(self, key: str, label: str | None = None, set_active: bool = True):
        self._validate_secret(key)
        normalized_secret = key.strip()
        key_id = uuid.uuid4().hex[:12]
        now = now_timestamp()
        key_label = label.strip() if isinstance(label, str) and label.strip() else f"Gemini key {len(self._state.get('keys', [])) + 1}"

        entry = {
            "id": key_id,
            "label": key_label,
            "secret": normalized_secret,
            "created_at": now,
            "updated_at": now,
        }
        self._state.setdefault("keys", []).append(entry)

        if set_active or not self._state.get("active_key_id"):
            self._state["active_key_id"] = key_id

        self._save()
        return self.get_public_catalog()

    def update_key(self, key_id: str, label: str | None = None, key: str | None = None, set_active: bool = False):
        index = self._find_key_index(key_id)
        if index < 0:
            raise CredentialValidationError("Chave Gemini nao encontrada")

        target = self._state["keys"][index]
        if isinstance(label, str) and label.strip():
            target["label"] = label.strip()

        if key is not None:
            self._validate_secret(key)
            target["secret"] = key.strip()

        target["updated_at"] = now_timestamp()

        if set_active:
            self._state["active_key_id"] = key_id

        self._save()
        return self.get_public_catalog()

    def delete_key(self, key_id: str):
        index = self._find_key_index(key_id)
        if index < 0:
            raise CredentialValidationError("Chave Gemini nao encontrada")

        removed = self._state["keys"].pop(index)
        if self._state.get("active_key_id") == key_id:
            self._state["active_key_id"] = self._state["keys"][0]["id"] if self._state.get("keys") else None
        self._save()
        return removed.get("id"), self.get_public_catalog()

    def select_key(self, key_id: str):
        if self._find_key_index(key_id) < 0:
            raise CredentialValidationError("Chave Gemini nao encontrada")
        self._state["active_key_id"] = key_id
        self._save()
        return self.get_public_catalog()

    def rotate_key(self):
        keys = self._state.get("keys", [])
        if len(keys) < 2:
            raise CredentialValidationError("Nao ha chaves suficientes para rotacao")

        active_id = self._state.get("active_key_id")
        active_index = self._find_key_index(active_id) if active_id else -1
        next_index = 0 if active_index < 0 else (active_index + 1) % len(keys)
        self._state["active_key_id"] = keys[next_index]["id"]
        self._save()
        return self.get_public_catalog()

    def rotate_key_after_quota(self):
        keys = self._state.get("keys", [])
        if len(keys) < 2:
            return None

        active_id = self._state.get("active_key_id")
        active_index = self._find_key_index(active_id) if active_id else -1
        next_index = 0 if active_index < 0 else (active_index + 1) % len(keys)
        if active_index >= 0 and next_index == active_index:
            return None

        previous = keys[active_index] if active_index >= 0 else None
        target = keys[next_index]
        self._state["active_key_id"] = target["id"]
        self._save()

        return {
            "from_id": previous.get("id") if previous else None,
            "from_masked": mask_secret(previous.get("secret")) if previous else "",
            "to_id": target.get("id"),
            "to_masked": mask_secret(target.get("secret")),
        }
