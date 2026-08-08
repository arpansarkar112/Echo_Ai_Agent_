import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Help() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="container mx-auto max-w-4xl">
        <Button variant="ghost" asChild className="mb-8">
          <Link to="/"><ArrowLeft className="mr-2 h-4 w-4" /> Back to Home</Link>
        </Button>
        <h1 className="text-4xl font-bold mb-6">Help & Support</h1>
        <div className="prose prose-lg dark:prose-invert">
          <h2 className="text-2xl font-semibold mt-8 mb-4">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-bold">How do I start a new chat?</h3>
              <p>Navigate to the Dashboard and click the "New Chat" button to begin interacting with the Echo AI.</p>
            </div>
            <div>
              <h3 className="font-bold">What kind of files can I upload?</h3>
              <p>Echo currently supports CSV files for data analysis and visualization.</p>
            </div>
            <div>
              <h3 className="font-bold">Is my data secure?</h3>
              <p>Yes, all your uploaded data is kept private and processed securely through our backend architecture.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
