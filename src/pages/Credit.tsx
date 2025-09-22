import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Credit() {
  return (
    <div className="flex justify-center items-center h-full">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Credits</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <p className="font-semibold">Developed by Arpan Sarkar</p>
          <p>
            Contact:{" "}
            <a href="mailto:arpan.sarkar@seamk.fi" className="text-blue-500 hover:underline">
              arpan.sarkar@seamk.fi
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
