# Echo 🤖
> Developed as part of the Bachelor’s Thesis at SeAMK – Degree Programme in Automation Engineering, 2025–2026
> Echo is your personal AI agent for automating tasks and intelligent conversations.

This is Echo, a full-stack AI chat application I've been working on. The goal is to create an intelligent agent that can not only hold natural conversations but also help automate RPA tasks. It's built with a React/Vite frontend and a Python/FastAPI backend.

## ✨ Features

-   **AI-Powered Intelligence**: An advanced AI agent that understands context and can perform robotic process automation (RPA) tasks.
-   **Natural Conversations**: Leverages Google's "gemini-1.5-flash" LLM for natural and intelligent chat responses.
-   **Instant Actions**: Automate complex workflows and tasks with simple commands.
-   **Secure & Private**: Uses Supabase for authentication and ensures data protection with end-to-end encryption.

## 🛠️ Tech Stack

I've used a modern stack for this project, separating the frontend and backend concerns.

-   **Frontend**:
    -   React & Vite
    -   TypeScript
    -   Tailwind CSS
    -   shadcn/ui for components
    -   Supabase Client for auth and DB interactions

-   **Backend**:
    -   Python 3.11+
    -   FastAPI
    -   Google Generative AI (Gemini)

-   **Database & Auth**:
    -   Supabase (PostgreSQL)

## 🚀 Getting Started

Here’s how you can get the project up and running on your local machine.

### Prerequisites

Make sure you have the following installed:
-   Node.js & npm
-   Python 3.11+ and `pip`

### Backend Setup

1.  **Navigate to the backend directory:**
    ```sh
    cd backend
    ```

2.  **Install Python dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a file named `.env` inside the `backend` directory and add the following keys. You'll need to get these from your Google AI and Supabase project settings.
    ```env
    GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
    SUPABASE_URL=YOUR_SUPABASE_PROJECT_URL
    SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
    ```

4.  **Run the backend server:**
    ```sh
    uvicorn main:app --reload --port 8000
    ```
    The backend API will be available at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the root directory and install dependencies:**
    ```sh
    npm install
    ```

2.  **Start the development server:**
    ```sh
    npm run dev
    ```
    The frontend will be available at `http://localhost:8081`.

## ☁️ Deployment Guide (for free!)

This guide will walk you through deploying the application to the web so anyone can access it with a link. We will use free services for this.

You have two parts to your project, and we need to deploy both:
1.  **Frontend (your website):** We'll use a service called **Vercel**.
2.  **Backend (your AI server):** We'll use a service called **Render**.

### Step 0: Push Your Code to GitHub

Before you can deploy, your project code needs to be in a GitHub repository. If you haven't done this yet:
1.  Create a new repository on [GitHub](https://github.com/new).
2.  Follow the instructions on GitHub to push your existing local project to the new repository.

---

### Step 1: Deploy the Backend on Render

Let's get your Python server online first.

1.  **Create a Render Account:**
    -   Go to [render.com](https://render.com/) and sign up for a free account. It's easiest to sign up using your GitHub account.

2.  **Create a New Web Service:**
    -   On your Render dashboard, click **"New +"** and then select **"Web Service"**.
    -   Connect your GitHub account and select your project's repository.

3.  **Configure the Backend Service:**
    Render will ask for some details. Fill them in exactly like this:
    -   **Name:** `echo-backend` (or any name you like).
    -   **Root Directory:** `backend` (This is important! It tells Render to look inside your `backend` folder).
    -   **Environment:** `Python 3`.
    -   **Region:** Choose the one closest to you.
    -   **Build Command:** `pip install -r requirements.txt`.
    -   **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 10000`.

4.  **Add Your Secrets (Environment Variables):**
    -   Scroll down to the "Environment" section.
    -   Click **"Add Environment Variable"** three times. You need to add the same keys and values from your local `backend/.env` file.
    -   **Key:** `GOOGLE_API_KEY`, **Value:** `Your_Google_API_Key_Here`
    -   **Key:** `SUPABASE_URL`, **Value:** `Your_Supabase_URL_Here`
    -   **Key:** `SUPABASE_ANON_KEY`, **Value:** `Your_Supabase_Anon_Key_Here`
    > **Important:** This is how you keep your secret keys safe. Never save them directly in your code.

5.  **Deploy!**
    -   Scroll to the bottom and click **"Create Web Service"**.
    -   Render will start building and deploying your backend. This might take a few minutes.
    -   Once it's done, you will get a public URL at the top of the page, something like `https://echo-backend.onrender.com`. **Copy this URL! You'll need it in the next step.**

---

### Step 2: Deploy the Frontend on Vercel

Now let's deploy the website that people will actually see.

1.  **Create a Vercel Account:**
    -   Go to [vercel.com](https://vercel.com/) and sign up for a free "Hobby" account. Again, it's easiest to use your GitHub account.

2.  **Create a New Project:**
    -   On your Vercel dashboard, click **"Add New..."** and select **"Project"**.
    -   Find your project's GitHub repository and click **"Import"**.

3.  **Configure the Frontend Project:**
    -   Vercel is smart and will probably figure out all the settings automatically. Just make sure they look like this:
        -   **Framework Preset:** `Vite`
        -   **Build Command:** `npm run build`
        -   **Output Directory:** `dist`

4.  **Add the Backend URL (Environment Variable):**
    -   Expand the "Environment Variables" section.
    -   Add one variable:
        -   **Name:** `VITE_API_URL`
        -   **Value:** Paste the URL of your Render backend that you copied earlier (e.g., `https://echo-backend.onrender.com`).

5.  **Deploy!**
    -   Click the **"Deploy"** button.
    -   Vercel will build and deploy your frontend. This is usually very fast.
    -   When it's finished, you'll get a big congratulations screen with your public website URL (e.g., `https://echo-your-name.vercel.app`).

### You're Done!

That's it! The Vercel URL is the link you can share with your teacher. When you open it, your Vercel frontend will be talking to your Render backend.

Whenever you push new code to your GitHub repository, Vercel and Render will automatically redeploy the changes for you. It's like magic!

---

Feel free to explore the code!

