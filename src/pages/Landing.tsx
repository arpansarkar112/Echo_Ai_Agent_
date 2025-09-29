import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowRight, Brain, MessageSquare, Bot, Layers } from "lucide-react";
import { Link } from "react-router-dom";
import * as React from "react";

const features = [
	{
		icon: Brain,
		title: "AI-Powered Intelligence",
		description:
			"Implements LLM-based agent that understands user input and makes task-related decisions.",
	},
	{
		icon: MessageSquare,
		title: "Natural Language Interface",
		description:
			"Users can provide instructions in plain language instead of programming commands.",
	},
	{
		icon: Bot,
		title: "RPA Task Execution",
		description:
			"Currently supports CSV data processing and form filling. The framework is extensible for more tasks",
	},
	{
		icon: Layers,
		title: "Lightweight & Extensible",
		description:
			"Unlike traditional RPA platforms, this system is lightweight, open, and built to scale with new automation functions.",
	},
];

export default function Landing() {
	React.useEffect(() => {
		document.documentElement.classList.add("dark");
	}, []);

	return (
		<div className="min-h-screen">
			{/* Navigation */}
			<nav className="border-b border-border/40 bg-background/80 backdrop-blur-sm sticky top-0 z-50">
				<div className="container mx-auto px-4 h-16 flex items-center justify-between">
					<div className="flex items-center gap-2">
						<div className="w-8 h-8 gradient-primary rounded-lg flex items-center justify-center">
							<Bot className="h-4 w-4 text-white" />
						</div>
						<span className="text-xl font-bold">Echo</span>
					</div>

					<div className="flex items-center gap-4">
						<Button variant="ghost" asChild>
							<Link to="/auth">Sign In</Link>
						</Button>
						<Button asChild className="gradient-primary hover:shadow-glow">
							<Link to="/auth">Get Started</Link>
						</Button>
					</div>
				</div>
			</nav>

			{/* Hero Section */}
			<section className="relative py-20 overflow-hidden">
				<div className="absolute inset-0 bg-gradient-hero opacity-5"></div>
				<div className="container mx-auto px-4 text-center relative z-10">
					<h1 className="text-5xl md:text-7xl font-bold mb-6">
						Meet Echo
						<span className="block bg-gradient-hero bg-clip-text text-transparent">
							Automate RPA with AI
						</span>
					</h1>

					<p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
						Echo was developed to demonstrate how large language model (LLM)-powered
						AI agents can perform robotic process automation tasks. The system
						allows users to describe tasks in natural language, which the AI agent
						interprets and executes as automated processes.
					</p>

					<div className="flex flex-col sm:flex-row gap-4 justify-center">
						<Button
							size="lg"
							asChild
							className="gradient-primary hover:shadow-glow transition-smooth"
						>
							<Link to="/auth">
								Start Chatting
								<ArrowRight className="ml-2 h-4 w-4" />
							</Link>
						</Button>
					</div>
				</div>
			</section>

			{/* Features Section */}
			<section className="py-20">
				<div className="container mx-auto px-4">
					<div className="text-center mb-16">
						<h2 className="text-3xl md:text-4xl font-bold mb-4">
							Why chose Echo?
						</h2>
					</div>

					<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
						{features.map((feature, index) => (
							<Card
								key={index}
								className="shadow-card hover:shadow-elegant transition-smooth glass-effect"
							>
								<CardContent className="p-6">
									<div className="w-12 h-12 gradient-primary rounded-lg flex items-center justify-center mb-4">
										<feature.icon className="h-6 w-6 text-white" />
									</div>
									<h3 className="text-lg font-semibold mb-2">
										{feature.title}
									</h3>
									<p className="text-muted-foreground">
										{feature.description}
									</p>
								</CardContent>
							</Card>
						))}
					</div>
				</div>
			</section>

			{/* CTA Section */}
			<section className="py-20 bg-gradient-subtle">
				<div className="container mx-auto px-4 text-center">
					<h2 className="text-3xl md:text-4xl font-bold mb-4">
						Ready to build your first RPA Task?
					</h2>
					<p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
						Echo demonstrates the integration of AI agents and robotic process
						automation. It was designed to explore how natural language can be used
						to control automated workflows. You are welcome to test the system and
						evaluate its effectiveness.
					</p>

					<Button
						size="lg"
						asChild
						className="gradient-primary hover:shadow-glow transition-smooth"
					>
						<Link to="/auth">
							Get Started
							<ArrowRight className="ml-2 h-4 w-4" />
						</Link>
					</Button>
				</div>
			</section>

			{/* Footer */}
			<footer className="border-t border-border/40 py-8">
				<div className="container mx-auto px-4 text-center text-muted-foreground">
					<p>
						&copy; 2025 Echo. Developed as part of the Bachelor’s Thesis at SeAMK
						– Degree Programme in Automation Engineering, 2025–2026
					</p>
				</div>
			</footer>
		</div>
	);
}