import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState([]);
  const [filter, setFilter] = useState("pending");
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load(status = filter) {
    try {
      const data = await api.reviews(status || undefined);
      setReviews(data);
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load(filter);
  }, [filter]);

  async function update(id, status, verified_condition) {
    setBusyId(id);
    try {
      const current = reviews.find((r) => r.id === id);
      await api.updateReview(id, {
        asset_id: current.asset_id,
        status,
        verified_condition,
        reviewer_notes:
          status === "verified"
            ? "Verified by authorized reviewer; outcome stored for feedback loop."
            : "Rejected / deferred after human review.",
        notice_draft: current.notice_draft,
      });
      await load(filter);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6 animate-rise">
      <section>
        <h1 className="font-display text-4xl text-ink">Human review & feedback</h1>
        <p className="mt-2 max-w-2xl text-slateish/75">
          High-risk assets are routed for verification before any official notice. Verified outcomes
          feed the model improvement loop.
        </p>
      </section>

      <div className="flex gap-2">
        {["pending", "verified", "rejected", ""].map((s) => (
          <button
            key={s || "all"}
            type="button"
            onClick={() => setFilter(s)}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              filter === s ? "bg-teal text-white" : "bg-white border border-slateish/15"
            }`}
          >
            {s || "all"}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-critical">{error}</p>}

      <div className="space-y-3">
        {reviews.map((r) => (
          <article
            key={r.id}
            className="rounded-2xl border border-slateish/10 bg-white/90 p-4 shadow-soft"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-semibold">
                  <Link className="text-teal hover:underline" to={`/assets/${r.asset_id}`}>
                    {r.asset_code} — {r.asset_name}
                  </Link>
                </h2>
                <p className="text-xs uppercase tracking-wide text-slateish/55">Status: {r.status}</p>
              </div>
              {r.status === "pending" && (
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={busyId === r.id}
                    onClick={() => update(r.id, "verified", "poor")}
                    className="rounded-lg bg-critical px-3 py-1.5 text-xs font-medium text-white"
                  >
                    Verify as poor
                  </button>
                  <button
                    type="button"
                    disabled={busyId === r.id}
                    onClick={() => update(r.id, "verified", "good")}
                    className="rounded-lg bg-low px-3 py-1.5 text-xs font-medium text-white"
                  >
                    Verify as good
                  </button>
                  <button
                    type="button"
                    disabled={busyId === r.id}
                    onClick={() => update(r.id, "rejected", null)}
                    className="rounded-lg border border-slateish/20 px-3 py-1.5 text-xs"
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
            {r.notice_draft && (
              <pre className="mt-3 overflow-auto rounded-xl bg-mist/70 p-3 text-xs whitespace-pre-wrap text-slateish/80">
                {r.notice_draft}
              </pre>
            )}
          </article>
        ))}
        {!reviews.length && (
          <p className="text-sm text-slateish/60">No reviews in this filter.</p>
        )}
      </div>
    </div>
  );
}
