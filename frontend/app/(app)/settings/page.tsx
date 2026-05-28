import { EmptyState } from "@/components/empty-state";

export default function SettingsPage() {
  return (
    <section className="page-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Account</p>
          <h1>Settings</h1>
        </div>
      </div>
      <EmptyState title="Basic account controls are in the header">
        Supabase profile settings can be added after the auth foundation is wired.
      </EmptyState>
    </section>
  );
}
