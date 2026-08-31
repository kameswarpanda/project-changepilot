"""PatchPlan model defining structured code generation output from Code Generator Agent."""
from typing import List, Optional
from pydantic import BaseModel, Field
from .change_plan import ChangeType


class FilePatch(BaseModel):
    """Specific file patch content."""
    file_path: str = Field(..., description="Relative file path to create, modify, or delete")
    change_type: ChangeType = Field(..., description="Action to perform: CREATE, MODIFY, or DELETE")
    content: Optional[str] = Field(default=None, description="Complete new file content for CREATE or MODIFY (None for DELETE)")
    patch_content: Optional[str] = Field(default=None, description="Alias for content")
    explanation: Optional[str] = Field(default=None, description="Specific reasoning for the code in this patch")


class PatchPlan(BaseModel):
    """Structured patch proposal containing discrete file patches."""
    story_id: str = Field(..., description="Story identifier matching ChangePlan")
    summary: str = Field(..., description="Summary of generated implementation")
    file_patches: List[FilePatch] = Field(..., min_length=1, description="List of exact file patches to apply")
    notes: Optional[str] = Field(default=None, description="Implementation notes or verification instructions")
