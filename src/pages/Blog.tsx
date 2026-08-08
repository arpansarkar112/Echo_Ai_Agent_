import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Blog() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="container mx-auto max-w-4xl">
        <Button variant="ghost" asChild className="mb-8">
          <Link to="/"><ArrowLeft className="mr-2 h-4 w-4" /> Back to Home</Link>
        </Button>
        <h1 className="text-4xl font-bold mb-6">Echo Blog</h1>
        <div className="grid gap-6">
          <div className="p-6 border border-border rounded-xl">
            <h2 className="text-2xl font-bold mb-2">Welcome to Echo</h2>
            <p className="text-muted-foreground mb-4">Published on August 8, 2026</p>
            <p>We are excited to announce the launch of Echo, our new AI-powered platform for democratizing Robotic Process Automation.</p>
          </div>
          <div className="p-6 border border-border rounded-xl">
            <h2 className="text-2xl font-bold mb-2">How to use Echo with CSVs</h2>
            <p className="text-muted-foreground mb-4">Published on August 5, 2026</p>
            <p>Learn the best practices for uploading, analyzing, and plotting your CSV data with natural language commands.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
