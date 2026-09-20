import type { GateAssessment } from "@/types";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface GatesTableProps {
  gates: GateAssessment[];
}

function getStatusIcon(status: string): string {
  switch (status) {
    case "PASS":
      return "✓";
    case "FAIL":
      return "✕";
    case "UNKNOWN":
      return "?";
    case "STALE":
      return "↻";
    case "NOT_APPLICABLE":
      return "—";
    default:
      return "";
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case "PASS":
      return "Pass";
    case "FAIL":
      return "Fail";
    case "UNKNOWN":
      return "Unknown";
    case "STALE":
      return "Needs recheck";
    case "NOT_APPLICABLE":
      return "Not applicable";
    default:
      return status;
  }
}

export function GatesTable({ gates }: GatesTableProps) {
  return (
    <div className="border">
      <Table>
        <TableCaption className="sr-only">Formal gates and requirements</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Gate</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Evidence basis</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {gates.map((gate, i) => (
            <TableRow key={i}>
              <TableCell className="font-medium">{gate.name}</TableCell>
              <TableCell className="flex items-center gap-2">
                <span aria-hidden="true">{getStatusIcon(gate.status)}</span>
                <span>{getStatusLabel(gate.status)}</span>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {gate.reason || "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
