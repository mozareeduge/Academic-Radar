"use client";

import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ProfileFact } from "@/types";

/** A suggested field for a fact card. Facts stay free-form — nothing here
 * is enforced server-side — this only decides which inputs the form shows. */
export interface FactField {
  key: string;
  label: string;
  placeholder?: string;
}

interface FactListEditorProps {
  sectionKey: string;
  title: string;
  description: string;
  fields: FactField[];
  facts: ProfileFact[];
  onChange: (facts: ProfileFact[]) => void;
  emptyLabel?: string;
  addLabel?: string;
}

function fieldValue(fact: ProfileFact, key: string): string {
  const raw = fact[key];
  if (typeof raw === "string") return raw;
  if (typeof raw === "number") return String(raw);
  return "";
}

/**
 * Editor for one CandidateProfile section (education, scholarly work, etc):
 * a list of free-form fact cards. The user only ever sees and edits fact
 * fields — provenance is never shown here because the server always stamps
 * it in as self-reported on save (see updateRadarProfile).
 */
export function FactListEditor({
  sectionKey,
  title,
  description,
  fields,
  facts,
  onChange,
  emptyLabel = "Nothing added yet.",
  addLabel = "Add entry",
}: FactListEditorProps) {
  function updateFact(index: number, key: string, value: string) {
    onChange(facts.map((fact, i) => (i === index ? { ...fact, [key]: value } : fact)));
  }

  function removeFact(index: number) {
    onChange(facts.filter((_, i) => i !== index));
  }

  function addFact() {
    onChange([...facts, {}]);
  }

  return (
    <div className="flex flex-col gap-3 border border-border p-4">
      <div>
        <h3 className="text-sm font-semibold text-muted-foreground">{title}</h3>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>

      {facts.length === 0 && (
        <p className="text-sm text-muted-foreground" data-testid={`${sectionKey}-empty`}>
          {emptyLabel}
        </p>
      )}

      {facts.length > 0 && (
        <div className="flex flex-col gap-4">
          {facts.map((fact, index) => (
            <div
              key={index}
              className="grid gap-3 border border-border/60 bg-muted/20 p-3 sm:grid-cols-2"
              data-testid={`${sectionKey}-entry-${index}`}
            >
              {fields.map((field) => {
                const inputId = `${sectionKey}-${index}-${field.key}`;
                return (
                  <div key={field.key} className="flex flex-col gap-1">
                    <Label htmlFor={inputId}>{field.label}</Label>
                    <Input
                      id={inputId}
                      value={fieldValue(fact, field.key)}
                      placeholder={field.placeholder}
                      onChange={(e) => updateFact(index, field.key, e.target.value)}
                    />
                  </div>
                );
              })}
              <div className="flex items-end justify-end sm:col-span-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFact(index)}
                  aria-label={`Remove ${title.toLowerCase()} entry ${index + 1}`}
                >
                  <Trash2 aria-hidden />
                  Remove
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div>
        <Button type="button" variant="outline" size="sm" onClick={addFact}>
          <Plus aria-hidden />
          {addLabel}
        </Button>
      </div>
    </div>
  );
}
