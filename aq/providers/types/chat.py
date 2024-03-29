from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


class FunctionCall(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str
    function: FunctionCall


class Content(BaseModel):
    type: Literal["text", "image_url"] = "text"
    text: Optional[str] = None
    image_url: Optional[str] = None


class ChatCompletionMessage(BaseModel):
    role: str
    content: Optional[str | List[Content]] = ""
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class Property(BaseModel):
    type: Literal["string"] = "string"
    description: str
    enum: Optional[List[str]] = None


class Parameters(BaseModel):
    type: Literal["object"] = "object"
    properties: Dict[str, Property]
    required: List[str]


class Function(BaseModel):
    name: str
    description: str
    parameters: Parameters


class Tool(BaseModel):
    type: Literal["function"] = "function"
    function: Function


class ResponseFormat(BaseModel):
    type: Literal["json_object"] = "json_object"


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessage]
    tools: Optional[List[Tool]] = None
    response_format: Optional[ResponseFormat] = None
    tool_choice: Optional[str] = None
    temperature: float = 0.5
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    max_tokens: int = 1000


class Choice(BaseModel):
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    choices: List[Choice]
    usage: Usage


class Error(BaseModel):
    code: Optional[str | int] = None
    message: str

