# Echo AI Agent

Hi! I’m Arpan Sarkar and I'm from SeAMK. This is my first web app project: Echo AI Agent.

## What is Echo?
Echo is a web-based AI agent designed to automate repetitive tasks and make intelligent decisions using natural language. I built Echo to explore how large language models (LLMs) and robotic process automation (RPA) can work together to solve real-world problems.

## Background & Motivation
During my studies, I noticed that many automation tools are either too technical or limited in scope. The recent emergence of AI agents capable of automating RPA tasks also deeply motivated me. This project combines my interests in AI, software engineering, and user experience.

### Key Features

*   The application ensures a secure and personalized experience by providing a robust authentication system for user sign-up and login.
*   Users can engage in real-time conversations with an intelligent AI assistant through a modern, intuitive, and responsive chat window.
*   AI-generated responses are displayed with full support for Markdown, allowing for clearly formatted text that includes headings, lists, bold emphasis, and code blocks.
*   The platform automatically saves all user interactions, providing a complete and accessible history of past conversations on a dedicated page.
*   Users have the ability to select any previous chat session from their history, view the entire conversation log, and seamlessly continue the dialogue from where they left off.
*   The application gives users complete control over their chat history, including the functionality to permanently delete old or unwanted conversation sessions.
*   A dedicated profile page is available for users to view and manage their account information.
*  The user interface is designed with a polished aesthetic that includes support for both dark mode and Light Mode to accommodate user preference.

## Technologies Used
- **Frontend:** React (Vite), TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** Python (FastAPI), Supabase (PostgreSQL), Google Gemini API
- **Hosting:** Vercel (frontend), Render (backend)

## Live Demo
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

