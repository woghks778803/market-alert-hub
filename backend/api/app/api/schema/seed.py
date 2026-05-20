from pydantic import BaseModel

class CreateOk(BaseModel):
    requested_base: str
    requested_count: int | None



