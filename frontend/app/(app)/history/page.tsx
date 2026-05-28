import { HistoryClient } from "@/components/history-client";

export default function HistoryPage() {
  return (
    <section className="page-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">History</p>
          <h1>Previous conversions</h1>
        </div>
      </div>
      <HistoryClient />
    </section>
  );
}
