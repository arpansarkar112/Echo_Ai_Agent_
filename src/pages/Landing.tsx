import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowRight, Brain, MessageSquare, Bot, Layers, CheckCircle2, Star, UserCircle, LogOut, Settings } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const features = [
  { icon: Brain, title: "AI-Powered Intelligence", description: "Implements LLM-based agent that understands user input and makes task-related decisions." },
  { icon: MessageSquare, title: "Natural Language Interface", description: "Users can provide instructions in plain language instead of programming commands." },
  { icon: Bot, title: "RPA Task Execution", description: "Currently supports only CSV data processing. The framework is extensible for more tasks." },
  { icon: Layers, title: "Lightweight & Extensible", description: "Built to scale with new automation functions without overhead." },
];

const testimonials = [
  { name: "Alex R.", role: "Data Analyst", text: "Echo saves me hours of manual CSV sorting. I just ask for what I need!" },
  { name: "Sarah M.", role: "Operations Manager", text: "The natural language interface is a game changer for our non-technical staff." },
  { name: "John D.", role: "Developer", text: "Clean API and extensible framework. Exactly what I was looking for." },
];

export default function Landing() {
  const { session, signOut } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  const handleLogout = async () => {
    await signOut();
    navigate("/");
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="border-b border-border/40 bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 gradient-primary rounded-lg flex items-center justify-center">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <span className="text-xl font-bold">Echo</span>
            </Link>
          </div>

          <div className="hidden md:flex items-center gap-6 text-sm font-medium">
            {!session ? (
              <>
                <Link to="/" className="hover:text-primary transition-colors">Home</Link>
                <Link to="/about" className="hover:text-primary transition-colors">About</Link>
                <Link to="/contact" className="hover:text-primary transition-colors">Contact</Link>
                <Button variant="ghost" asChild><Link to="/auth">Sign In</Link></Button>
              </>
            ) : (
              <>
                <Link to="/" className="hover:text-primary transition-colors">Home</Link>
                <Link to="/dashboard" className="hover:text-primary transition-colors">Dashboard</Link>
                <Link to="/blog" className="hover:text-primary transition-colors">Blog</Link>
                <Link to="/help" className="hover:text-primary transition-colors">Help</Link>
                
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="rounded-full">
                      <UserCircle className="h-6 w-6" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>My Account</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <Link to="/dashboard/profile" className="cursor-pointer w-full flex items-center">
                        <UserCircle className="mr-2 h-4 w-4" /> Profile
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link to="/dashboard/settings" className="cursor-pointer w-full flex items-center">
                        <Settings className="mr-2 h-4 w-4" /> Settings
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-destructive focus:text-destructive">
                      <LogOut className="mr-2 h-4 w-4" /> Log out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative min-h-[70vh] flex flex-col justify-center overflow-hidden py-20">
          <div className="absolute inset-0 bg-gradient-hero opacity-5"></div>
          <div className="container mx-auto px-4 text-center relative z-10">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 animate-in fade-in slide-in-from-bottom-4 duration-1000">
              Meet Echo
              <span className="block bg-gradient-hero bg-clip-text text-transparent mt-2">
                Automate RPA with AI
              </span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-5 duration-1000 delay-150">
              Echo is an intelligent AI agent that performs Robotic Process Automation tasks like handling CSV files through simple natural language commands.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-300">
              <Button size="lg" asChild className="gradient-primary hover:shadow-glow transition-smooth">
                <Link to={session ? "/dashboard" : "/auth"}>
                  {session ? "Go to Dashboard" : "Start Chatting"}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link to="/about">Learn More</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Statistics Section */}
        <section className="py-12 border-y border-border/40 bg-muted/30">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div><p className="text-4xl font-bold text-primary">10k+</p><p className="text-muted-foreground mt-2">Tasks Automated</p></div>
              <div><p className="text-4xl font-bold text-primary">99%</p><p className="text-muted-foreground mt-2">Accuracy</p></div>
              <div><p className="text-4xl font-bold text-primary">50+</p><p className="text-muted-foreground mt-2">Supported Formats</p></div>
              <div><p className="text-4xl font-bold text-primary">24/7</p><p className="text-muted-foreground mt-2">Availability</p></div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Why choose Echo?</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">Discover the power of natural language automation.</p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature, index) => (
                <Card key={index} className="shadow-card hover:shadow-elegant transition-smooth glass-effect h-full">
                  <CardContent className="p-6 flex flex-col items-center text-center">
                    <div className="w-12 h-12 gradient-primary rounded-xl flex items-center justify-center mb-6">
                      <feature.icon className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="text-lg font-semibold mb-3">{feature.title}</h3>
                    <p className="text-muted-foreground text-sm flex-1">{feature.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* How it Works Section */}
        <section className="py-20 bg-muted/20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold mb-4">How It Works</h2>
            </div>
            <div className="max-w-3xl mx-auto space-y-8">
              {[
                { step: "01", title: "Upload Data", desc: "Securely upload your CSV files to your workspace." },
                { step: "02", title: "Give Instructions", desc: "Type what you want to do in plain English." },
                { step: "03", title: "Get Results", desc: "Echo executes the task and provides clean output and charts." },
              ].map((item, i) => (
                <div key={i} className="flex gap-6 items-start bg-background p-6 rounded-2xl border border-border">
                  <div className="text-4xl font-bold text-primary/30">{item.step}</div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                    <p className="text-muted-foreground">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="py-20">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold mb-12 text-center">What Our Users Say</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {testimonials.map((t, i) => (
                <Card key={i} className="bg-background">
                  <CardContent className="p-6">
                    <div className="flex gap-1 mb-4 text-yellow-500">
                      {[1,2,3,4,5].map(star => <Star key={star} className="h-4 w-4 fill-current" />)}
                    </div>
                    <p className="italic mb-6">"{t.text}"</p>
                    <div>
                      <p className="font-semibold">{t.name}</p>
                      <p className="text-sm text-muted-foreground">{t.role}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-20 bg-muted/20">
          <div className="container mx-auto px-4 max-w-3xl">
            <h2 className="text-3xl font-bold mb-8 text-center">Frequently Asked Questions</h2>
            <div className="space-y-4">
              {[
                { q: "Is Echo free to use?", a: "We offer a generous free tier for basic usage. Premium features require a subscription." },
                { q: "What data formats are supported?", a: "Currently, we fully support CSV files, with JSON and Excel support coming soon." },
                { q: "Is my data secure?", a: "Yes, we use enterprise-grade encryption and never use your private data to train our models." },
              ].map((faq, i) => (
                <div key={i} className="p-6 bg-background rounded-xl border border-border">
                  <h3 className="font-bold flex items-center gap-2"><CheckCircle2 className="h-5 w-5 text-primary" /> {faq.q}</h3>
                  <p className="text-muted-foreground mt-2 ml-7">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Newsletter Section */}
        <section className="py-20">
          <div className="container mx-auto px-4 max-w-xl text-center">
            <h2 className="text-2xl font-bold mb-4">Stay Updated</h2>
            <p className="text-muted-foreground mb-6">Subscribe to our newsletter for the latest AI automation features.</p>
            <div className="flex gap-2">
              <input type="email" placeholder="Enter your email" className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary" />
              <Button>Subscribe</Button>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-gradient-subtle border-t border-border/40">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to automate your workflows?</h2>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Join thousands of users who have streamlined their data tasks using plain English.
            </p>
            <Button size="lg" asChild className="gradient-primary hover:shadow-glow transition-smooth">
              <Link to="/auth">
                Get Started Now
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 bg-muted/10 py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8 mb-8 text-sm">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Bot className="h-5 w-5 text-primary" />
                <span className="text-lg font-bold">Echo</span>
              </div>
              <p className="text-muted-foreground">Democratizing RPA with Artificial Intelligence.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground">Product</h4>
              <ul className="space-y-2 text-muted-foreground">
                <li><Link to="/features" className="hover:text-primary">Features</Link></li>
                <li><Link to="/pricing" className="hover:text-primary">Pricing</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground">Resources</h4>
              <ul className="space-y-2 text-muted-foreground">
                <li><Link to="/blog" className="hover:text-primary">Blog</Link></li>
                <li><Link to="/help" className="hover:text-primary">Help Center</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-foreground">Company</h4>
              <ul className="space-y-2 text-muted-foreground">
                <li><Link to="/about" className="hover:text-primary">About</Link></li>
                <li><Link to="/contact" className="hover:text-primary">Contact</Link></li>
                <li><Link to="/privacy" className="hover:text-primary">Privacy Policy</Link></li>
              </ul>
            </div>
          </div>
          <div className="text-center text-muted-foreground text-sm pt-8 border-t border-border/40">
            <p>&copy; {new Date().getFullYear()} Echo. Developed by Arpan Sarkar.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}