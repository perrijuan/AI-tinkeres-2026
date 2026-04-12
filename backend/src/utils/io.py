from typing import Any


def model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[return-value]
    if hasattr(model, "dict"):
        return model.dict()  # type: ignore[return-value]
    if isinstance(model, dict):
        return model
    raise TypeError(f"Unsupported model type: {type(model)}")

