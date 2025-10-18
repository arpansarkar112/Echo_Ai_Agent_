import type { Components } from "react-markdown";
import { defaultUrlTransform, type UrlTransform } from "react-markdown";
import remarkGfm from "remark-gfm";
import type { PluggableList } from "unified";

import { cn } from "@/lib/utils";

export const markdownPlugins: PluggableList = [remarkGfm];

export const allowDataUrl: UrlTransform = (url) => {
  if (url.startsWith("data:")) {
    return url;
  }
  return defaultUrlTransform(url);
};

export const markdownComponents: Components = {
  table: ({ node: _node, className, ...props }) => (
    <div className="my-4 overflow-x-auto rounded-md border border-border bg-muted/40">
      <table
        {...props}
        className={cn("min-w-full border-collapse text-sm", className)}
      />
    </div>
  ),
  thead: ({ node: _node, className, ...props }) => (
    <thead {...props} className={cn("bg-muted/60", className)} />
  ),
  tr: ({ node: _node, className, ...props }) => (
    <tr {...props} className={cn("odd:bg-background even:bg-muted/20", className)} />
  ),
  th: ({ node: _node, className, ...props }) => (
    <th
      {...props}
      className={cn(
        "border border-border px-3 py-2 text-left font-semibold text-foreground",
        className,
      )}
    />
  ),
  td: ({ node: _node, className, ...props }) => (
    <td
      {...props}
      className={cn(
        "border border-border px-3 py-2 text-foreground",
        className,
      )}
    />
  ),
};
