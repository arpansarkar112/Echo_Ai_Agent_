import os
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from typing import Optional, List

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

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

class ChatResponse(BaseModel):
    response: str
    session_id: str

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
        # Using gemini-pro as it is a stable and widely available model.
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.getenv("GOOGLE_API_KEY"))
        ai_response = llm.invoke([HumanMessage(content=user_message)])
        ai_message = ai_response.content

        # 4. Save AI message
        client.table("chat_messages").insert({
            "session_id": session_id,
            "role": "assistant",
            "content": ai_message
        }).execute()

        return ChatResponse(response=ai_message, session_id=str(session_id))

    except Exception as e:
        print("!!! CHAT ENDPOINT CRASHED !!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
