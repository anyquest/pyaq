from typing import List
from pydantic import BaseModel
from typing import Dict, Any, Optional
from enum import Enum


class ActivityType(Enum):
    ANY = "any"
    READ = "read"
    WRITE = "write"
    STORE = "store"
    RETRIEVE = "retrieve"
    SUMMARIZE = "summarize"
    EXTRACT = "extract"
    GENERATE = "generate"
    FUNCTION = "function"
    CALL = "call"
    RETURN = "return"


class ToolType(Enum):
    ANY = "any"
    WEB = "web"
    REST = "rest"


class ModelProvider(Enum):
    ANY = "any"
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    LLAVA = "llava"


class MemoryType(Enum):
    ANY = "any"
    CHROMADB = "chromadb"


class Model(BaseModel):
    model: str
    provider: ModelProvider
    parameters: Dict[str, Any] = {}


class ToolDef(BaseModel):
    type: ToolType
    models: Optional[List[str]] = None
    parameters: Dict[str, Any] = {}


class MemoryDef(BaseModel):
    type: MemoryType
    models: Optional[List[str]] = None
    parameters: Dict[str, Any] = {}


class ActivityInput(BaseModel):
    activity: str
    map: Optional[str] = None


class Activity(BaseModel):
    type: ActivityType
    tools: Optional[List[str]] = None
    inputs: Optional[List[ActivityInput]] = None
    models: Optional[List[str]] = None
    memory: Optional[List[str]] = None
    parameters: Dict[str, Any] = {}


class AppInfo(BaseModel):
    id: str
    title: str
    version: str
    profile: Optional[str] = None


class App(BaseModel):
    aq: str
    info: AppInfo
    models: Optional[Dict[str, Model]] = None
    memory: Optional[Dict[str, MemoryDef]] = None
    tools: Optional[Dict[str, ToolDef]] = None
    activities: Dict[str, Activity]

