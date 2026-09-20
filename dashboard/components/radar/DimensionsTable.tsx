import type { DimensionAssessment } from "@/types";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface DimensionsTableProps {
  dimensions: DimensionAssessment[];
}

export function DimensionsTable({ dimensions }: DimensionsTableProps) {
  return (
    <div className="border">
      <Table>
        <TableCaption className="sr-only">Assessment dimensions</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Dimension</TableHead>
            <TableHead>Assessment</TableHead>
            <TableHead>Evidence</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {dimensions.map((dim, i) => (
            <TableRow key={i}>
              <TableCell className="font-medium">{dim.name}</TableCell>
              <TableCell>
                {dim.unknown ? (
                  <span className="text-muted-foreground">Unknown</span>
                ) : dim.value !== null && dim.value !== undefined ? (
                  <span>{dim.value}</span>
                ) : (
                  <span className="text-muted-foreground">Unknown</span>
                )}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {dim.evidence_count ? `${dim.evidence_count} item(s)` : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
