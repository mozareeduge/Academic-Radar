"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import AuthGate from "@/components/AuthGate";
import { FactListEditor, type FactField } from "@/components/radar/FactListEditor";
import { RouteEditorCard } from "@/components/radar/RouteEditorCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import {
  ApiError,
  createRadarRoute,
  fetchRadarProfile,
  fetchRadarRoutes,
  updateRadarProfile,
  updateRadarRoute,
} from "@/lib/api";
import type { ProfileFact, RadarProfile, RadarRoute, RadarRouteInput } from "@/types";

const EDUCATION_FIELDS: FactField[] = [
  { key: "degree", label: "Degree", placeholder: "e.g. MSc Physics" },
  { key: "institution", label: "Institution", placeholder: "e.g. University of Example" },
  { key: "year", label: "Year", placeholder: "e.g. 2022" },
];

const LANGUAGE_FIELDS: FactField[] = [
  { key: "language", label: "Language", placeholder: "e.g. English" },
  { key: "proficiency_level", label: "Proficiency", placeholder: "e.g. C1, IELTS 7.5" },
  { key: "test_date", label: "Test / evidence date", placeholder: "e.g. 2024-03-15" },
];

const SCHOLARLY_FIELDS: FactField[] = [
  { key: "title", label: "Title", placeholder: "Paper, thesis, or project title" },
  { key: "type", label: "Type", placeholder: "e.g. paper, master_thesis" },
  { key: "publication_year", label: "Year", placeholder: "e.g. 2024" },
  { key: "doi", label: "DOI / link", placeholder: "Optional" },
];

const ARTISTIC_FIELDS: FactField[] = [
  { key: "title", label: "Title", placeholder: "Work or exhibition title" },
  { key: "year", label: "Year", placeholder: "e.g. 2023" },
  { key: "medium", label: "Medium", placeholder: "e.g. Installation, exhibition" },
];

const PROFESSIONAL_FIELDS: FactField[] = [
  { key: "position", label: "Position", placeholder: "e.g. Research Engineer" },
  { key: "organization", label: "Organization", placeholder: "e.g. Example University" },
  { key: "duration_months", label: "Duration (months)", placeholder: "e.g. 18" },
  { key: "start_date", label: "Start date", placeholder: "Optional" },
];

const EMPTY_NEW_ROUTE = {
  name: "",
  routeStatement: "",
  coreProblem: "",
  maturity: "",
  methods: "",
  corpora: "",
  disciplines: "",
  overclaims: "",
};

function fromLines(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

/**
 * Strips out empty fields and empty entries before saving. A fact that a
 * user started typing and then blanked out (or an "Add entry" row nobody
 * filled in) should not be sent to the server as a fact with no content.
 * `provenance` is stripped too — the server always sets it (self-reported,
 * unverified) and would reject anything the client sends there.
 */
function cleanFacts(facts: ProfileFact[]): Record<string, unknown>[] {
  return facts
    .map((fact) => {
      const cleaned: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(fact)) {
        if (key === "provenance") continue;
        if (typeof value === "string" && value.trim() === "") continue;
        if (value === undefined || value === null) continue;
        cleaned[key] = value;
      }
      return cleaned;
    })
    .filter((fact) => Object.keys(fact).length > 0);
}

export default function RadarProfilePage() {
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingRouteId, setSavingRouteId] = useState<string | null>(null);
  const [addingRoute, setAddingRoute] = useState(false);

  const [profileId, setProfileId] = useState<string | null>(null);
  const [constraints, setConstraints] = useState("");
  const [education, setEducation] = useState<ProfileFact[]>([]);
  const [languageEvidence, setLanguageEvidence] = useState<ProfileFact[]>([]);
  const [scholarlyWork, setScholarlyWork] = useState<ProfileFact[]>([]);
  const [artisticWork, setArtisticWork] = useState<ProfileFact[]>([]);
  const [professionalEvidence, setProfessionalEvidence] = useState<ProfileFact[]>([]);

  const [routes, setRoutes] = useState<RadarRoute[]>([]);
  const [newRoute, setNewRoute] = useState(EMPTY_NEW_ROUTE);

  const applyProfile = useCallback((p: RadarProfile) => {
    setProfileId(p.id);
    setConstraints(p.fixed_constraints ?? "");
    setEducation(p.education ?? []);
    setLanguageEvidence(p.language_evidence ?? []);
    setScholarlyWork(p.scholarly_work ?? []);
    setArtisticWork(p.artistic_curatorial_work ?? []);
    setProfessionalEvidence(p.professional_technical_evidence ?? []);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [profileResult, routesResult] = await Promise.allSettled([
        fetchRadarProfile(),
        fetchRadarRoutes(),
      ]);

      if (profileResult.status === "fulfilled") {
        applyProfile(profileResult.value);
      } else {
        const reason = profileResult.reason;
        // No profile yet is expected for a brand-new owner — the form just
        // starts empty and the first Save creates it.
        if (!(reason instanceof ApiError && reason.status === 404)) {
          setError(reason instanceof ApiError ? reason.message : "Could not load your profile");
        }
      }

      setRoutes(routesResult.status === "fulfilled" ? routesResult.value.items : []);
    } finally {
      setLoading(false);
    }
  }, [applyProfile]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function handleSaveProfile() {
    setSavingProfile(true);
    setError(null);
    try {
      const saved = await updateRadarProfile({
        fixed_constraints: constraints,
        education: cleanFacts(education),
        language_evidence: cleanFacts(languageEvidence),
        scholarly_work: cleanFacts(scholarlyWork),
        artistic_curatorial_work: cleanFacts(artisticWork),
        professional_technical_evidence: cleanFacts(professionalEvidence),
      });
      applyProfile(saved);
      toast("Profile saved", { variant: "success" });
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Could not save your profile";
      setError(msg);
      toast("Could not save profile", { description: msg, variant: "destructive" });
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleSaveRoute(routeId: string, patch: RadarRouteInput) {
    setSavingRouteId(routeId);
    setError(null);
    try {
      const updated = await updateRadarRoute(routeId, patch);
      setRoutes((prev) => prev.map((r) => (r.id === routeId ? updated : r)));
      toast("Route saved", { variant: "success" });
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Could not save this route";
      setError(msg);
      toast("Could not save route", { description: msg, variant: "destructive" });
    } finally {
      setSavingRouteId(null);
    }
  }

  async function handleAddRoute() {
    if (!newRoute.name.trim()) {
      setError("Give your new research route a name before adding it.");
      return;
    }
    setAddingRoute(true);
    setError(null);
    try {
      const created = await createRadarRoute({
        name: newRoute.name.trim(),
        route_statement: newRoute.routeStatement || null,
        core_problem: newRoute.coreProblem || null,
        maturity: newRoute.maturity || null,
        operations_methods: fromLines(newRoute.methods),
        relevant_corpora_material: fromLines(newRoute.corpora),
        target_disciplines: fromLines(newRoute.disciplines),
        prohibited_overclaims: fromLines(newRoute.overclaims),
      });
      setRoutes((prev) => [...prev, created]);
      setNewRoute(EMPTY_NEW_ROUTE);
      toast("Route added", { variant: "success" });
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Could not add this route";
      setError(msg);
      toast("Could not add route", { description: msg, variant: "destructive" });
    } finally {
      setAddingRoute(false);
    }
  }

  return (
    <AuthGate>
      <div className="flex min-w-0 flex-col gap-6">
        <div>
          <Link
            href="/radar"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
          >
            <ArrowLeft className="size-4" aria-hidden />
            Radar
          </Link>
        </div>

        <div>
          <h1 className="text-2xl font-semibold">Your academic profile</h1>
          <p className="text-sm text-muted-foreground">
            What Radar knows about you and the research directions you&apos;re pursuing.
            Everything here is self-reported — nothing is treated as independently
            verified until someone checks it.
          </p>
        </div>

        {error && (
          <div
            role="alert"
            className="flex flex-col gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between"
          >
            <span>{error}</span>
            <Button type="button" size="sm" variant="outline" onClick={() => void load()}>
              Retry
            </Button>
          </div>
        )}

        {loading && (
          <div className="flex flex-col gap-3" aria-label="Loading your profile">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        )}

        {!loading && (
          <>
            <section className="flex flex-col gap-3 border border-border p-4">
              <div>
                <h2 className="text-sm font-semibold text-muted-foreground">
                  Fixed constraints
                </h2>
                <p className="text-xs text-muted-foreground">
                  Anything that rules opportunities in or out no matter what — visa
                  needs, language requirements, funding requirements, location limits.
                </p>
              </div>
              <Label htmlFor="constraints" className="sr-only">
                Fixed constraints
              </Label>
              <Textarea
                id="constraints"
                rows={3}
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
                placeholder="e.g. English language proficiency (IELTS 7.0+); needs full funding; UK or EU only"
              />
            </section>

            <FactListEditor
              sectionKey="education"
              title="Education"
              description="Degrees you've completed or are completing."
              fields={EDUCATION_FIELDS}
              facts={education}
              onChange={setEducation}
              emptyLabel="No education entries yet."
              addLabel="Add degree"
            />

            <FactListEditor
              sectionKey="language"
              title="Language evidence"
              description="Certificates or other evidence of language proficiency."
              fields={LANGUAGE_FIELDS}
              facts={languageEvidence}
              onChange={setLanguageEvidence}
              emptyLabel="No language evidence yet."
              addLabel="Add language"
            />

            <FactListEditor
              sectionKey="scholarly"
              title="Scholarly work"
              description="Papers, theses, and other research outputs."
              fields={SCHOLARLY_FIELDS}
              facts={scholarlyWork}
              onChange={setScholarlyWork}
              emptyLabel="No scholarly work yet."
              addLabel="Add scholarly work"
            />

            <FactListEditor
              sectionKey="artistic"
              title="Artistic / curatorial work"
              description="Exhibitions, installations, or other creative practice."
              fields={ARTISTIC_FIELDS}
              facts={artisticWork}
              onChange={setArtisticWork}
              emptyLabel="No artistic or curatorial work yet."
              addLabel="Add work"
            />

            <FactListEditor
              sectionKey="professional"
              title="Professional / technical experience"
              description="Roles, positions, and technical work history."
              fields={PROFESSIONAL_FIELDS}
              facts={professionalEvidence}
              onChange={setProfessionalEvidence}
              emptyLabel="No professional experience yet."
              addLabel="Add role"
            />

            <div className="flex justify-end">
              <Button type="button" onClick={() => void handleSaveProfile()} disabled={savingProfile}>
                {savingProfile ? "Saving…" : profileId ? "Save profile" : "Create profile"}
              </Button>
            </div>

            <div className="border-t border-border pt-6">
              <div className="mb-3">
                <h2 className="text-lg font-semibold">Research routes</h2>
                <p className="text-sm text-muted-foreground">
                  The distinct research directions you&apos;re pursuing. Radar matches
                  each route against opportunities separately.
                </p>
              </div>

              {routes.length === 0 && (
                <p className="mb-4 text-sm text-muted-foreground" data-testid="routes-empty">
                  No research routes yet — add one below.
                </p>
              )}

              <div className="flex flex-col gap-4">
                {routes.map((route) => (
                  <RouteEditorCard
                    key={route.id}
                    route={route}
                    saving={savingRouteId === route.id}
                    onSave={handleSaveRoute}
                  />
                ))}
              </div>

              <div className="mt-4 flex flex-col gap-3 border border-dashed border-border p-4">
                <h3 className="text-sm font-semibold text-muted-foreground">Add a new route</h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="flex flex-col gap-1.5 sm:col-span-2">
                    <Label htmlFor="new-route-name">New route name</Label>
                    <Input
                      id="new-route-name"
                      value={newRoute.name}
                      onChange={(e) => setNewRoute((r) => ({ ...r, name: e.target.value }))}
                      placeholder="e.g. Quantum Simulation and Error Correction"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5 sm:col-span-2">
                    <Label htmlFor="new-route-statement">Route statement</Label>
                    <Textarea
                      id="new-route-statement"
                      rows={2}
                      value={newRoute.routeStatement}
                      onChange={(e) => setNewRoute((r) => ({ ...r, routeStatement: e.target.value }))}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5 sm:col-span-2">
                    <Label htmlFor="new-route-problem">Core problem</Label>
                    <Textarea
                      id="new-route-problem"
                      rows={2}
                      value={newRoute.coreProblem}
                      onChange={(e) => setNewRoute((r) => ({ ...r, coreProblem: e.target.value }))}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="new-route-maturity">Maturity</Label>
                    <Input
                      id="new-route-maturity"
                      value={newRoute.maturity}
                      placeholder="e.g. EXPLORATORY, ACTIVE"
                      onChange={(e) => setNewRoute((r) => ({ ...r, maturity: e.target.value }))}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="new-route-methods">Methods (one per line)</Label>
                    <Textarea
                      id="new-route-methods"
                      rows={2}
                      value={newRoute.methods}
                      onChange={(e) => setNewRoute((r) => ({ ...r, methods: e.target.value }))}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="new-route-corpora">Corpora / sources (one per line)</Label>
                    <Textarea
                      id="new-route-corpora"
                      rows={2}
                      value={newRoute.corpora}
                      onChange={(e) => setNewRoute((r) => ({ ...r, corpora: e.target.value }))}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="new-route-disciplines">Target disciplines (one per line)</Label>
                    <Textarea
                      id="new-route-disciplines"
                      rows={2}
                      value={newRoute.disciplines}
                      onChange={(e) => setNewRoute((r) => ({ ...r, disciplines: e.target.value }))}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="new-route-overclaims">Prohibited overclaims (one per line)</Label>
                    <Textarea
                      id="new-route-overclaims"
                      rows={2}
                      value={newRoute.overclaims}
                      onChange={(e) => setNewRoute((r) => ({ ...r, overclaims: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button type="button" size="sm" onClick={() => void handleAddRoute()} disabled={addingRoute}>
                    {addingRoute ? "Adding…" : "Add route"}
                  </Button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </AuthGate>
  );
}
