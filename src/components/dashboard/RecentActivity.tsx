import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const activities = [
  {
    id: 1,
    user: "John Smith",
    action: "signed up for Pro plan",
    time: "2 minutes ago",
    initials: "JS"
  },
  {
    id: 2,
    user: "Sarah Johnson",
    action: "updated profile settings",
    time: "15 minutes ago",
    initials: "SJ"
  },
  {
    id: 3,
    user: "Mike Davis",
    action: "completed onboarding",
    time: "1 hour ago",
    initials: "MD"
  },
  {
    id: 4,
    user: "Emma Wilson",
    action: "invited 3 team members",
    time: "2 hours ago",
    initials: "EW"
  },
  {
    id: 5,
    user: "Alex Chen",
    action: "created new project",
    time: "4 hours ago",
    initials: "AC"
  }
];

export function RecentActivity() {
  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity) => (
            <div key={activity.id} className="flex items-center space-x-4">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary/10 text-primary">
                  {activity.initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium leading-none">
                  {activity.user}
                </p>
                <p className="text-xs text-muted-foreground">
                  {activity.action}
                </p>
              </div>
              <div className="text-xs text-muted-foreground">
                {activity.time}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}