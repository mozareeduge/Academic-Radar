import { CircleHelp, Landmark, TriangleAlert } from "lucide-react";
import type { FundingAssessment } from "@/types";

interface FundingPackagesProps {
  assessments: FundingAssessment[];
}

function money(amount: string | null, currency: string): string {
  return amount === null ? "Unknown" : `${amount} ${currency}`;
}

function stateIcon(state: string) {
  if (state === "FORMALLY_BLOCKED" || state === "FUNDING_GAP") {
    return <TriangleAlert className="size-4 text-destructive" aria-hidden />;
  }
  if (state === "ELIGIBILITY_UNKNOWN") {
    return <CircleHelp className="size-4 text-muted-foreground" aria-hidden />;
  }
  return <Landmark className="size-4 text-muted-foreground" aria-hidden />;
}

export function FundingPackages({ assessments }: FundingPackagesProps) {
  if (assessments.length === 0) {
    return (
      <div className="border border-border p-4 text-sm text-muted-foreground">
        No funding assessments are linked to this case yet.
      </div>
    );
  }

  return (
    <section className="border border-border" aria-label="Funding assessments">
      <div className="border-b border-border bg-muted/50 px-4 py-3">
        <h3 className="font-semibold">Funding assessments</h3>
      </div>
      <div className="divide-y divide-border">
        {assessments.map((assessment) => (
          <article key={assessment.id} className="p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <h4 className="break-all font-medium">{assessment.funding_route_id}</h4>
                <p className="mt-1 text-xs text-muted-foreground">
                  Assessment {assessment.id}
                </p>
              </div>
              <span className="inline-flex items-center gap-1 border border-border bg-muted px-2 py-1 text-xs font-medium">
                {stateIcon(assessment.state)}
                {assessment.state}
              </span>
            </div>

            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-xs text-muted-foreground">Award</dt>
                <dd className="mt-1 font-mono">{money(assessment.award_amount, assessment.currency)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Tuition</dt>
                <dd className="mt-1 font-mono">{money(assessment.tuition_amount, assessment.currency)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Uncovered gap</dt>
                <dd className="mt-1 font-mono">{money(assessment.uncovered_gap, assessment.currency)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Duration</dt>
                <dd className="mt-1">{assessment.duration_months === null ? "Unknown" : `${assessment.duration_months} months`}</dd>
              </div>
            </dl>

            {(assessment.known_costs || assessment.unknown_costs) && (
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="border border-border bg-muted/30 p-3 text-xs">
                  <div className="font-medium">Known costs</div>
                  <pre className="mt-2 whitespace-pre-wrap break-words font-mono text-muted-foreground">
                    {assessment.known_costs ? JSON.stringify(assessment.known_costs, null, 2) : "None recorded"}
                  </pre>
                </div>
                <div className="border border-border bg-muted/30 p-3 text-xs">
                  <div className="font-medium">Unknown costs</div>
                  <pre className="mt-2 whitespace-pre-wrap break-words font-mono text-muted-foreground">
                    {assessment.unknown_costs ? JSON.stringify(assessment.unknown_costs, null, 2) : "None recorded"}
                  </pre>
                </div>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
