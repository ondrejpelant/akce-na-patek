import { fetchStatus, type StatusRow } from "@/lib/queries";
import { relativeTimeSince } from "@/lib/format";

export const instant = false;

export const metadata = { title: "Status · Akce na pátek" };

export default async function StatusPage() {
  const rows = await fetchStatus();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Status aktualizací</h1>
      <p className="text-sm text-neutral-600">
        Poslední běh pro každý aktivní obchod. Spouští se ručně přes{" "}
        <code className="rounded bg-neutral-100 px-1">aktualizuj.bat</code>.
      </p>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-neutral-200 text-left text-xs uppercase tracking-wide text-neutral-500">
              <th className="py-2 pr-3">Obchod</th>
              <th className="py-2 pr-3">Status</th>
              <th className="py-2 pr-3">Položek</th>
              <th className="py-2 pr-3">Změn</th>
              <th className="py-2 pr-3">Poslední běh</th>
              <th className="py-2 pr-3">Trvání</th>
              <th className="py-2 pr-3">Poznámka</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <StatusRowView key={row.code} row={row} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusRowView({ row }: { row: StatusRow }) {
  const started = row.last_started_at ? new Date(row.last_started_at) : null;
  const finished = row.last_finished_at ? new Date(row.last_finished_at) : null;
  const duration =
    started && finished ? formatDuration(finished.getTime() - started.getTime()) : "—";

  return (
    <tr className={`border-b border-neutral-100 ${row.is_active ? "" : "opacity-50"}`}>
      <td className="py-2 pr-3 font-medium">{row.name}</td>
      <td className="py-2 pr-3">
        <StatusBadge status={row.last_status} />
      </td>
      <td className="py-2 pr-3 tabular-nums">{row.last_items_found ?? "—"}</td>
      <td className="py-2 pr-3 tabular-nums">{row.last_items_changed ?? "—"}</td>
      <td className="py-2 pr-3 text-neutral-600">
        {started ? relativeTimeSince(started) : "—"}
      </td>
      <td className="py-2 pr-3 tabular-nums text-neutral-600">{duration}</td>
      <td className="max-w-[20ch] truncate py-2 pr-3 text-xs text-neutral-500" title={row.last_error ?? ""}>
        {row.last_error ?? ""}
      </td>
    </tr>
  );
}

function StatusBadge({ status }: { status: StatusRow["last_status"] }) {
  if (!status) return <span className="text-xs text-neutral-400">—</span>;
  const styles: Record<NonNullable<StatusRow["last_status"]>, string> = {
    running: "bg-blue-100 text-blue-800",
    ok: "bg-emerald-100 text-emerald-800",
    partial: "bg-amber-100 text-amber-800",
    failed: "bg-rose-100 text-rose-800",
  };
  const labels: Record<NonNullable<StatusRow["last_status"]>, string> = {
    running: "Běží",
    ok: "OK",
    partial: "Partial",
    failed: "Chyba",
  };
  return (
    <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

function formatDuration(ms: number): string {
  if (ms < 0) return "—";
  const seconds = Math.round(ms / 1000);
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}
