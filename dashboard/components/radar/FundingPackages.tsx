import type { FundingAssessment } from "@/types";

interface FundingPackagesProps {
  assessments: FundingAssessment[];
}

export function FundingPackages({ assessments }: FundingPackagesProps) {
  return (
    <div className="rounded-md border mb-6">
      <div className="bg-muted/50 px-4 py-3 border-b">
        <h3 className="font-semibold">Funding Packages</h3>
      </div>
      <div className="divide-y">
        {assessments.map((assessment) => (
          <div key={assessment.id} className="p-4">
            <h4 className="font-medium mb-3">{assessment.funding_route_name}</h4>

            <div className="grid grid-cols-2 gap-4 text-sm mb-3">
              <div>
                <div className="text-muted-foreground text-xs mb-1">Award</div>
                <div className="font-mono">
                  {assessment.currency} {assessment.award}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground text-xs mb-1">Tuition</div>
                <div className="font-mono">{assessment.tuition}</div>
              </div>
            </div>

            <div className="mb-3 p-2 bg-muted/30 rounded text-sm">
              <div className="text-muted-foreground text-xs mb-1">
                Known Gap
              </div>
              <div className="font-mono">{assessment.known_gap}</div>
            </div>

            {assessment.unknown_cost_items.length > 0 && (
              <div>
                <div className="text-muted-foreground text-xs mb-2">
                  Unknown Cost Items
                </div>
                <ul className="text-sm space-y-1">
                  {assessment.unknown_cost_items.map((item: string, i: number) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                  <li className="flex gap-2">
                    <span className="text-muted-foreground">•</span>
                    <span className="text-muted-foreground">Unknown</span>
                  </li>
                </ul>
              </div>
            )}

            {assessment.fully_funded_allowed && (
              <div className="mt-3 text-xs text-muted-foreground italic">
                Fully funded allowed
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
