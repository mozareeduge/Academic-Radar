"use client";

import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { RadarRoute, RadarRouteInput, RouteState } from "@/types";

const ROUTE_STATES: RouteState[] = ["ACTIVE", "EXPLORATORY", "DORMANT", "RETIRED"];

function toLines(value?: string[] | null): string {
  return (value ?? []).join("\n");
}

function fromLines(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

interface RouteEditorCardProps {
  route: RadarRoute;
  saving: boolean;
  onSave: (routeId: string, patch: RadarRouteInput) => Promise<void>;
}

/**
 * One research route (MozareRoute), fully editable — including retiring it
 * (state = RETIRED), which is how a route gets "deactivated": there is no
 * separate delete, matching the domain model (routes are never destroyed,
 * only moved to a terminal state so history/cases stay intact).
 */
export function RouteEditorCard({ route, saving, onSave }: RouteEditorCardProps) {
  const id = useId();
  const [name, setName] = useState(route.name);
  const [state, setState] = useState<string>(route.state);
  const [routeStatement, setRouteStatement] = useState(route.route_statement ?? "");
  const [coreProblem, setCoreProblem] = useState(route.core_problem ?? "");
  const [maturity, setMaturity] = useState(route.maturity ?? "");
  const [methods, setMethods] = useState(toLines(route.operations_methods));
  const [corpora, setCorpora] = useState(toLines(route.relevant_corpora_material));
  const [disciplines, setDisciplines] = useState(toLines(route.target_disciplines));
  const [overclaims, setOverclaims] = useState(toLines(route.prohibited_overclaims));

  async function handleSave() {
    await onSave(route.id, {
      name,
      state,
      route_statement: routeStatement || null,
      core_problem: coreProblem || null,
      maturity: maturity || null,
      operations_methods: fromLines(methods),
      relevant_corpora_material: fromLines(corpora),
      target_disciplines: fromLines(disciplines),
      prohibited_overclaims: fromLines(overclaims),
    });
  }

  return (
    <div className="flex flex-col gap-3 border border-border p-4" data-testid={`route-card-${route.id}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="border border-border bg-muted px-2 py-1 text-xs font-medium uppercase tracking-wide">
          {route.state}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-name`}>Route name</Label>
          <Input id={`${id}-name`} value={name} onChange={(e) => setName(e.target.value)} />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-state`}>Route state</Label>
          <Select value={state} onValueChange={(v) => setState(v ?? route.state)}>
            <SelectTrigger id={`${id}-state`} className="w-full" aria-label="Route state">
              <SelectValue placeholder="Select a state" />
            </SelectTrigger>
            <SelectContent>
              {ROUTE_STATES.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor={`${id}-statement`}>Route statement</Label>
          <Textarea
            id={`${id}-statement`}
            rows={2}
            value={routeStatement}
            onChange={(e) => setRouteStatement(e.target.value)}
            placeholder="What are you investigating on this route?"
          />
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor={`${id}-problem`}>Core problem</Label>
          <Textarea
            id={`${id}-problem`}
            rows={2}
            value={coreProblem}
            onChange={(e) => setCoreProblem(e.target.value)}
            placeholder="What problem does this route address?"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-maturity`}>Maturity</Label>
          <Input
            id={`${id}-maturity`}
            value={maturity}
            placeholder="e.g. EXPLORATORY, ACTIVE"
            onChange={(e) => setMaturity(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-methods`}>Methods (one per line)</Label>
          <Textarea id={`${id}-methods`} rows={3} value={methods} onChange={(e) => setMethods(e.target.value)} />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-corpora`}>Corpora / sources (one per line)</Label>
          <Textarea id={`${id}-corpora`} rows={3} value={corpora} onChange={(e) => setCorpora(e.target.value)} />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-disciplines`}>Target disciplines (one per line)</Label>
          <Textarea
            id={`${id}-disciplines`}
            rows={3}
            value={disciplines}
            onChange={(e) => setDisciplines(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${id}-overclaims`}>Prohibited overclaims (one per line)</Label>
          <Textarea
            id={`${id}-overclaims`}
            rows={3}
            value={overclaims}
            onChange={(e) => setOverclaims(e.target.value)}
          />
        </div>
      </div>

      <div className="flex justify-end">
        <Button type="button" size="sm" onClick={() => void handleSave()} disabled={saving}>
          {saving ? "Saving…" : "Save route"}
        </Button>
      </div>
    </div>
  );
}
