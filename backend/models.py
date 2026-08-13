from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    """Schema for creating a new ticket"""
    title: str = Field(..., min_length=1, max_length=255)
    created_by: Optional[str] = None

class TicketUpdate(BaseModel):
    """Schema for updating an existing ticket"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|closed)$")

class TicketResponse(BaseModel):
    """Schema for ticket response"""
    ticket_id: int
    title: str
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    message: str = Field(..., min_length=1)
    author: Optional[str] = None

class MessageResponse(BaseModel):
    """Schema for message response"""
    message_id: int
    ticket_id: int
    message_text: str
    author: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True