import type { ReactNode } from "react";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type AdminFormFieldProps = {
  children: ReactNode;
  className?: string;
  hint?: string;
  htmlFor?: string;
  label: string;
};

export function AdminFormField({ children, className, hint, htmlFor, label }: AdminFormFieldProps) {
  return (
    <div className={cn("grid gap-1.5", className)}>
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function AdminInput(props: React.ComponentProps<typeof Input>) {
  return <Input {...props} />;
}

export function AdminTextarea({ className, rows = 4, ...props }: React.ComponentProps<typeof Textarea>) {
  return (
    <Textarea
      className={cn("min-h-24", className)}
      rows={rows}
      {...props}
    />
  );
}
