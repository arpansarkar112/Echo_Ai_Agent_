import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function About() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="container mx-auto max-w-4xl">
        <Button variant="ghost" asChild className="mb-8">
          <Link to="/"><ArrowLeft className="mr-2 h-4 w-4" /> Back to Home</Link>
        </Button>
        <h1 className="text-4xl font-bold mb-6">About Echo</h1>
        <div className="prose prose-lg dark:prose-invert">
          <p>
            Echo is an advanced AI Agent platform designed to democratize Robotic Process Automation (RPA) through natural language processing.
            Our mission is to enable users of all technical backgrounds to automate complex data tasks—such as CSV analysis, transformation, and reporting—simply by asking.
          </p>
          <h2 className="text-2xl font-semibold mt-8 mb-4">Our Vision</h2>
          <p>
            We believe that automation should not require writing code. By leveraging state-of-the-art Large Language Models (LLMs), Echo acts as your intelligent assistant, translating your intent into executable workflows with precision and speed.
          </p>
          <h2 className="text-2xl font-semibold mt-8 mb-4">Core Technology</h2>
          <p>
            Built on a highly scalable microservices architecture, Echo utilizes a Python/FastAPI backend for high-performance data processing and a React frontend for an intuitive, real-time user experience. Our integration with Semantic Kernel allows for dynamic prompt execution and tool orchestration.
          </p>
        </div>
      </div>
    </div>
  );
}
