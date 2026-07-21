from pydantic import BaseModel


class WebhookConfig(BaseModel):
    repo_name: str
