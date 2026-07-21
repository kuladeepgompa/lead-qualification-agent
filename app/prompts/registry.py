"""Immutable prompt registry and safe lead-data rendering."""

import json
from dataclasses import dataclass

from app.schemas.lead import LeadInput


@dataclass(frozen=True, slots=True)
class PromptDefinition:
    """A versioned prompt definition used for reproducibility and auditability."""

    name: str
    version: str
    system_prompt: str

    def render_user_prompt(self, lead: LeadInput) -> str:
        """Serialize normalized lead fields as a data-only block."""

        lead_data = json.dumps(lead.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
        return f"<lead_data>{lead_data}</lead_data>"


def get_lead_qualification_prompt() -> PromptDefinition:
    """Return the active qualification prompt version."""

    from app.prompts.lead_qualification_v1 import LEAD_QUALIFICATION_V1

    return LEAD_QUALIFICATION_V1
