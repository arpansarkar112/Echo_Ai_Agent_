# Echo AI Agent

Hi! I’m Arpan Sarkar and I'm from SeAMK. This is my first web app project: Echo AI Agent.

Echo is a web-based AI agent designed to automate repetitive tasks (such as handling csv files) and make intelligent decisions using natural language. I built Echo to explore how large language models (LLMs) and Agentic Ai can work together to solve real-world problems.

## Background & Motivation
During my studies, I noticed that many automation tools are either too technical or limited in scope. The recent emergence of AI agents capable of automating RPA tasks also deeply motivated me. This project combines my interests in AI, software engineering, and web development.

### Key Features

*   The application ensures a secure and personalized experience by providing a robust authentication system for user sign-up and login.
*   Users can engage in real-time conversations with an intelligent AI assistant.
*   AI-generated responses are displayed with clear formatted text and standard fonts that includes headings, lists, bold emphasis, and code blocks.
*   The platform automatically saves all user interactions, providing a complete and accessible history of past conversations on a dedicated page.
*   Users have the ability to select any previous chat session from their history, view the entire conversation log, permanently delete old or unwanted conversation sessions, and continue the dialogue from where they left off.
*   A dedicated profile page is available for users to view and manage their account name.
*   The user interface is designed to support toggle between dark mode and Light Mode to accommodate user preference.
*   The users have access to a personally trained agent model which is trained to handle only csv files. Also, in the front-end the chat pages handle message streaming, dataset uploads/downloads, dataset switching, and inline rendering of markdown plus generated      charts, while guarding uploads behind active sessions.
*   The users can upload CSVs, fetch updated files, and load generated charts; datasets are scoped per session with access checks, and the planner executes rich intents such as set-cell, add-row, delete-row(s), row math, and bar/line plots.
*   This ai agent can always introduces itself properly as Echo.

## Technologies Used
- **Frontend:** React (Vite), TypeScript, Tailwind CSS, shadcn/ui, Radix UI primitives, React Hook Form + Zod, TanStack React Query, Supabase JS SDK, React Markdown (remark-gfm), Lucide icons, Recharts.
- **Backend:** Python (FastAPI), Supabase (PostgreSQL), Google Gemini API, Langchain-google-genai, Semantic Kernel, pandas, matplotlib, python-dotenv, python-multipart, uvicorn, tabulate.
- **Tooling & Build:** Vite + SWC, ESLint, TypeScript, Tailwind CSS Typography, PostCSS / Autoprefixer, Supabase CLI
- **Hosting:** Vercel (frontend), Render (backend)

## Live Demo
- **Domain:** [https://www.ask-echo.me/](https://www.ask-echo.me/)
- **Frontend:** [https://echo-ai-agent.vercel.app/](https://echo-ai-agent.vercel.app/)
- **Backend:** [https://echo-backend-cdmq.onrender.com/](https://echo-backend-cdmq.onrender.com/)

## How to Run Locally
1. Clone this repo:
    ```sh
    git clone https://github.com/arpansarkar112/Echo_Ai_Agent_.git
    ```
2. Install frontend dependencies:
    ```sh
    cd Echo_main
    npm install
    ```
3. Start the frontend:
    ```sh
    npm run dev
    ```
4. Start the backend:
    ```sh
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

## Deployment
I deployed the frontend on Vercel and the backend on Render. You can visit the live app using the links above. Both services offer free hosting for personal hobby projects.

## Why I Built This
I wanted to make automation accessible and intelligent. I hope it inspires others to build their own tools that make technology more human-friendly.

## Credits
This project was developed by **Arpan Sarkar**.

- **Contact:** [arpan.sarkar@seamk.fi](mailto:arpan.sarkar@seamk.fi)

---

Feel free to reach out if you have questions or feedback!

