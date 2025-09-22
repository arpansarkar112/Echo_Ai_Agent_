import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, TrendingUp, Activity, DollarSign } from "lucide-react";

const stats = [
  {
    title: "Total Users",
    value: "2,847",
    change: "+12.5%",
    icon: Users,
    trend: "up"
  },
  {
    title: "Revenue",
    value: "$43,829",
    change: "+8.2%",
    icon: DollarSign,
    trend: "up"
  },
  {
    title: "Active Sessions",
    value: "1,249",
    change: "+23.1%",
    icon: Activity,
    trend: "up"
  },
  {
    title: "Growth Rate",
    value: "34.2%",
    change: "+4.3%",
    icon: TrendingUp,
    trend: "up"
  }
];

export function DashboardStats() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.title} className="shadow-card hover:shadow-elegant transition-smooth">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
            <div className="flex items-center text-xs text-green-600">
              <TrendingUp className="h-3 w-3 mr-1" />
              {stat.change} from last month
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}