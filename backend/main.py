import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from supabase import create_client, Client
from google.api_core.exceptions import GoogleAPIError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from identity import identity_response, is_identity_query

try:
    from langchain_core.messages import HumanMessage, SystemMessage  # Newer LangChain builds
except ImportError:  # pragma: no cover - fallback for older LangChain versions
    from langchain.schema import HumanMessage, SystemMessage
from typing import Optional, List

import importlib
import types

try:
    import google.generativeai.protos  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - provide shim for newer SDK builds
    try:
        generative_language = importlib.import_module(
            "google.ai.generativelanguage"
        )
        shim = types.ModuleType("google.generativeai.protos")

        module_candidates: list[types.ModuleType | str] = [
            generative_language,
            "google.ai.generativelanguage.types",
            "google.ai.generativelanguage.types.content",
            "google.ai.generativelanguage.types.content_pb2",
            "google.ai.generativelanguage.types.generative_service",
            "google.ai.generativelanguage.types.generative_service_pb2",
            "google.ai.generativelanguage_v1.types",
            "google.ai.generativelanguage_v1.types.content",
            "google.ai.generativelanguage_v1.types.content_pb2",
            "google.ai.generativelanguage_v1.types.generative_service",
            "google.ai.generativelanguage_v1.types.generative_service_pb2",
            "google.ai.generativelanguage_v1beta.types",
            "google.ai.generativelanguage_v1beta.types.content",
            "google.ai.generativelanguage_v1beta.types.content_pb2",
            "google.ai.generativelanguage_v1beta.types.generative_service",
            "google.ai.generativelanguage_v1beta.types.generative_service_pb2",
        ]
        module_cache: dict[str, types.ModuleType | None] = {}

        def _resolve_symbol(name: str):
            for candidate in module_candidates:
                module: types.ModuleType | None
                if isinstance(candidate, str):
                    module = module_cache.get(candidate)
                    if module is None:
                        try:
                            module = importlib.import_module(candidate)
                        except ImportError:
                            module = None
                        module_cache[candidate] = module
                else:
                    module = candidate
                if module and hasattr(module, name):
                    return getattr(module, name)
            raise AttributeError(name)

        # Copy a core set of types that legacy callers expect.
        for attr in (
            "Blob",
            "Candidate",
            "Content",
            "FunctionCall",
            "FunctionResponse",
            "Part",
        ):
            try:
                setattr(shim, attr, _resolve_symbol(attr))
            except AttributeError:
                continue

        def _shim_getattr(name: str):
            return _resolve_symbol(name)

        def _shim_dir():
            names: set[str] = set()
            for candidate in module_candidates:
                module: types.ModuleType | None
                if isinstance(candidate, str):
                    module = module_cache.get(candidate)
                    if module is None:
                        try:
                            module = importlib.import_module(candidate)
                        except ImportError:
                            module = None
                        module_cache[candidate] = module
                else:
                    module = candidate
                if module:
                    names.update(name for name in dir(module) if not name.startswith("_"))
            return sorted(names)

        shim.__getattr__ = _shim_getattr  # type: ignore[attr-defined]
        shim.__dir__ = _shim_dir  # type: ignore[attr-defined]
        shim.__all__ = _shim_dir()

        sys.modules["google.generativeai.protos"] = shim
        google_generativeai = importlib.import_module("google.generativeai")
        setattr(google_generativeai, "protos", shim)
    except (ImportError, AttributeError):
        pass

from agents.csv_agent import CSVAgent, CSVAgentError

# Load environment variables from backend/.env regardless of current working directory.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

app = FastAPI()

CSV_STORAGE_DIR = BASE_DIR / "data" / "csv_sessions"
csv_agent = CSVAgent(storage_dir=CSV_STORAGE_DIR)
API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000")
GENERAL_CHAT_SYSTEM_PROMPT = (
    "You are Echo, an AI agent that helps users analyse and transform CSV datasets. "
    "When the user asks who you are or what you can do, introduce yourself as Echo and explain that you can "
    "perform mathematical operations on CSV data, create visualisations, and add or remove rows and columns. "
    "Never claim to be created by Google or to operate on Google systems."
)

# --- CORS Configuration ---
# Allows the frontend (running on a different port) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models (for request and response data validation) ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    dataset_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class CSVUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    summary: str
    preview_table: str

class CSVSessionDataset(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    created_at: str


class Session(BaseModel):
    session_id: str
    title: Optional[str]
    created_at: str

class Message(BaseModel):
    id: int
    role: str
    content: str
    created_at: str

class Profile(BaseModel):
    full_name: Optional[str] = None
    display_name: Optional[str] = None

# --- Supabase & Authentication Dependencies ---

def get_chat_model() -> ChatGoogleGenerativeAI:
    """
    Returns a Gemini chat model instance, raising a runtime error if the API key is missing.
    Keeping the construction here lets us validate configuration before we try to invoke the model.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        api_key = api_key.strip()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable is not configured on the backend.")

    model_name = os.getenv("GOOGLE_GENAI_MODEL", "gemini-pro-latest")
    return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)


def get_supabase_client() -> Client:
    """
    Creates a generic, non-authenticated Supabase client.
    Used for validating tokens, not for data operations.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in backend/.env")
    return create_client(url, key)

def get_authenticated_client(authorization: str = Header(...)) -> Client:
    """
    Creates a Supabase client that is authenticated with the user's token.
    This is the correct way to perform operations that respect Row Level Security.
    """
    try:
        token = authorization.split(" ")[1]
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in backend/.env")
        
        # Create a new client and immediately set the user's session
        client = create_client(url, key)
        client.auth.set_session(access_token=token, refresh_token=token)
        
        # Verify the token is valid by getting user info
        user_info = client.auth.get_user()
        if not user_info.user:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        return client
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {e}")


# --- API Endpoints ---

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, client: Client = Depends(get_authenticated_client)):
    """Handles a new chat message from the user."""
    try:
        user_id = client.auth.get_user().user.id
        session_id = chat_request.session_id
        user_message = chat_request.message
        dataset_id = chat_request.dataset_id or None

        # 1. Create a new session if one doesn't exist
        if not session_id:
            title = " ".join(user_message.split()[:5]) + "..."
            session_res = client.table("chat_sessions").insert({"user_id": user_id, "title": title}).execute()
            session_id = session_res.data[0]['id']

        # 2. Save user message
        client.table("chat_messages").insert({
            "session_id": session_id,
            "role": "user",
            "content": user_message
        }).execute()

        # 3. Get AI response
        if is_identity_query(user_message):
            ai_message = identity_response()
        elif dataset_id:
            try:
                ai_message = await csv_agent.analyze(
                    dataset_id=dataset_id,
                    question=user_message,
                    user_id=user_id,
                )
            except CSVAgentError as agent_error:
                raise HTTPException(status_code=400, detail=str(agent_error))
        else:
            # Using gemini-pro-latest model from Google Generative AI
            try:
                llm = get_chat_model()
            except RuntimeError as config_error:
                raise HTTPException(status_code=500, detail=str(config_error))

            try:
                ai_response = llm.invoke(
                    [
                        SystemMessage(content=GENERAL_CHAT_SYSTEM_PROMPT),
                        HumanMessage(content=user_message),
                    ]
                )
            except (ChatGoogleGenerativeAIError, GoogleAPIError) as llm_error:
                print("!!! GEMINI INVOCATION FAILED !!!")
                traceback.print_exc()
                print(f"Gemini error detail: {llm_error}")
                raise HTTPException(
                    status_code=503,
                    detail="Unable to contact Gemini. Please refresh the Google Generative AI API key."
                ) from llm_error

            ai_message = ai_response.content

        # 4. Save AI message
        client.table("chat_messages").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": ai_message
        }).execute()

        return ChatResponse(response=ai_message, session_id=str(session_id))

    except HTTPException:
        raise
    except Exception as e:
        print("!!! CHAT ENDPOINT CRASHED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/csv/upload", response_model=CSVUploadResponse)
async def upload_csv_dataset(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    client: Client = Depends(get_authenticated_client),
):
    """Upload a CSV file and register it with the CSV agent."""
    try:
        user_id = client.auth.get_user().user.id
        result = await csv_agent.ingest_file(
            upload=file,
            user_id=user_id,
            session_id=session_id,
        )

        # Record the ingestion as a system message for traceability
        client.table("chat_messages").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": (
                f"{result['summary']}\n\n{result['preview_table']}\n\n"
                f"Dataset ID: `{result['dataset_id']}`"
            )
        }).execute()

        return CSVUploadResponse(**result)
    except CSVAgentError as agent_error:
        raise HTTPException(status_code=400, detail=str(agent_error))
    except HTTPException:
        raise
    except Exception as exc:
        print("!!! CSV UPLOAD FAILED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/agent/csv/export/{dataset_id}")
async def export_csv_dataset(
    dataset_id: str,
    client: Client = Depends(get_authenticated_client),
):
    """Allow the user to download the current version of a CSV dataset."""
    try:
        user_id = client.auth.get_user().user.id
        metadata = csv_agent.get_dataset_metadata(dataset_id)
        if metadata.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Dataset not found for this user.")

        csv_path = csv_agent.get_dataset_path(dataset_id)
        filename = metadata.get("filename", f"{dataset_id}.csv")
        return FileResponse(
            path=csv_path,
            filename=filename,
            media_type="text/csv",
        )
    except CSVAgentError as agent_error:
        raise HTTPException(status_code=404, detail=str(agent_error))
    except HTTPException:
        raise
    except Exception as exc:
        print("!!! CSV EXPORT FAILED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/agent/csv/asset/{dataset_id}/{asset_name}")
async def get_csv_asset(
    dataset_id: str,
    asset_name: str,
    client: Client = Depends(get_authenticated_client),
):
    """Serve generated assets (plots, etc.) for a dataset."""
    try:
        user_id = client.auth.get_user().user.id
        metadata = csv_agent.get_dataset_metadata(dataset_id)
        if metadata.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="Asset not found for this user.")

        asset_path = (CSV_STORAGE_DIR / dataset_id / "assets") / asset_name
        if not asset_path.exists():
            raise HTTPException(status_code=404, detail="Asset not found.")

        media_type = "image/png" if asset_path.suffix.lower() == ".png" else "application/octet-stream"
        return FileResponse(
            path=asset_path,
            filename=asset_path.name,
            media_type=media_type,
        )
    except CSVAgentError as agent_error:
        raise HTTPException(status_code=404, detail=str(agent_error))
    except HTTPException:
        raise
    except Exception as exc:
        print("!!! CSV ASSET FETCH FAILED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/agent/csv/session/{session_id}", response_model=List[CSVSessionDataset])
async def list_session_datasets(
    session_id: str,
    client: Client = Depends(get_authenticated_client),
):
    """Return the CSV datasets previously uploaded for this chat session."""
    try:
        user_id = client.auth.get_user().user.id
        datasets = csv_agent.list_session_datasets(session_id=session_id, user_id=user_id)
        return [
            CSVSessionDataset(**dataset)
            for dataset in datasets
        ]
    except HTTPException:
        raise
    except Exception as exc:
        print("!!! LIST CSV DATASETS FAILED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/sessions", response_model=List[Session])
async def get_sessions(client: Client = Depends(get_authenticated_client)):
    """Fetches all past chat sessions for the logged-in user."""
    try:
        user_id = client.auth.get_user().user.id
        res = client.table("chat_sessions").select("id, title, created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
        sessions = [{"session_id": s['id'], "title": s['title'], "created_at": s['created_at']} for s in res.data]
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", response_model=List[Message])
async def get_session_messages(session_id: str, client: Client = Depends(get_authenticated_client)):
    """Fetches all messages for a specific chat session."""
    try:
        user_id = client.auth.get_user().user.id
        # Verify the user owns the session before fetching messages
        session_res = client.table("chat_sessions").select("id").eq("id", session_id).eq("user_id", user_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found or access denied")

        messages_res = client.table("chat_messages").select("*").eq("session_id", session_id).order("created_at", desc=False).execute()
        return messages_res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, client: Client = Depends(get_authenticated_client)):
    """Deletes a specific chat session and all its messages."""
    try:
        user_id = client.auth.get_user().user.id
        # Verify the user owns the session before deleting
        session_res = client.table("chat_sessions").select("id").eq("id", session_id).eq("user_id", user_id).execute()
        if not session_res.data:
            raise HTTPException(status_code=404, detail="Session not found or access denied")

        # The 'on delete cascade' in the database schema will handle deleting messages
        client.table("chat_sessions").delete().eq("id", session_id).execute()
        
        return
    except Exception as e:
        print(f"!!! DELETE SESSION {session_id} CRASHED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile", response_model=Profile)
async def get_profile(client: Client = Depends(get_authenticated_client)):
    """Fetches the profile for the logged-in user."""
    try:
        user_id = client.auth.get_user().user.id
        # Use a standard select and check the result, which is more robust
        res = client.table("profiles").select("full_name, display_name").eq("id", user_id).execute()
        
        # If no data is returned, it means no profile exists yet.
        if not res.data:
            # Manually insert a profile for the user if one doesn't exist.
            # This handles cases for users who signed up before the profile table was created.
            client.table("profiles").insert({"id": user_id}).execute()
            return Profile() # Return a default empty profile for the frontend
            
        return res.data[0]
    except Exception as e:
        print("!!! GET PROFILE CRASHED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/profile", response_model=Profile)
async def update_profile(profile: Profile, client: Client = Depends(get_authenticated_client)):
    """Updates the profile for the logged-in user."""
    try:
        user_id = client.auth.get_user().user.id
        profile_data = profile.dict(exclude_unset=True)
        
        # The Supabase client now correctly handles the 'updated_at' field automatically
        # if the column is configured to default to now() or has a trigger.
        # If not, you might need to add it manually:
        # profile_data['updated_at'] = 'now()'
        
        res = client.table("profiles").update(profile_data).eq("id", user_id).execute()
        
        # The update operation returns the updated data in res.data
        if not res.data:
            raise HTTPException(status_code=404, detail="Profile not found to update")

        return res.data[0]
    except Exception as e:
        print("!!! UPDATE PROFILE CRASHED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
