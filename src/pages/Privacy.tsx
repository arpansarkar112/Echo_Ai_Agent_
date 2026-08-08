import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Privacy() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="container mx-auto max-w-4xl">
        <Button variant="ghost" asChild className="mb-8">
          <Link to="/"><ArrowLeft className="mr-2 h-4 w-4" /> Back to Home</Link>
        </Button>
        <h1 className="text-4xl font-bold mb-6">Privacy Policy</h1>
        <div className="prose prose-lg dark:prose-invert">
          <p>Last updated: August 8, 2026</p>
          <h2 className="text-2xl font-semibold mt-8 mb-4">Data Collection</h2>
          <p>
            We collect information you provide directly to us when you create an account, update your profile, use the interactive features of our services, or otherwise communicate with us.
          </p>
          <h2 className="text-2xl font-semibold mt-8 mb-4">Use of Data</h2>
          <p>
            We use the information we collect to provide, maintain, and improve our services, including processing transactions and sending related information.
          </p>
          <h2 className="text-2xl font-semibold mt-8 mb-4">Contact Us</h2>
          <p>
            If you have any questions about this Privacy Policy, please contact us via our Contact page.
          </p>
        </div>
      </div>
    </div>
  );
}
