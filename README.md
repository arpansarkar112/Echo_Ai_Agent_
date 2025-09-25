# Echo AI Agent

Hi! I’m Arpan Sarkar and I'm from SeAMK. This is my bachelor thesis project: Echo AI Agent.

## What is Echo?
Echo is a web-based AI agent designed to automate repetitive tasks and make intelligent decisions using natural language. I built Echo to explore how large language models (LLMs) and robotic process automation (RPA) can work together to solve real-world problems.

## Background & Motivation
During my studies, I noticed that many automation tools are either too technical or limited in scope. The recent emergence of AI agents capable of automating RPA tasks also deeply motivated me. My goal with Echo was to create an assistant that anyone can use—just type what you want, and Echo will figure out the rest. This project combines my interests in AI, software engineering, and user experience.

## Features
- **AI-Powered Intelligence:** Uses Google Gemini LLM to understand and process user instructions.
- **Natural Language Interface:** Interact with Echo using chat interface.
- **RPA Task Execution:** Automates tasks like CSV data processing, form filling, and more.
- **User Authentication:** Secure login and personalized profiles powered by Supabase.
- **Chat History:** View and manage your past conversations and tasks.
- **Extensible Design:** Built to be open and easy to extend for new use cases.

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

