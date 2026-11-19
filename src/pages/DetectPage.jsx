import { useState } from "react";
import { api } from "../api/client";

export default function DetectPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [annotated, setAnnotated] = useState("");
  const [detections, setDetections] = useState([]);
  const [assetId, setAssetId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function onFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setAnnotated("");
    setDetections([]);
  }

  async function runDetect() {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const [dets, blob] = await Promise.all([
        api.detect(file, assetId ? Number(assetId) : undefined),
        api.annotate(file),
      ]);
      setDetections(dets);
      setAnnotated(URL.createObjectURL(blob));
    } catch (e) {
      setError(e.message || "Detection failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 animate-rise">
      <section>
        <h1 className="font-display text-4xl text-ink">Visual damage detection</h1>
        <p className="mt-2 max-w-2xl text-slateish/75">
          YOLO-ready CV module for potholes, cracks, and surface defects (RDD-style labels D00 /
          D10 / D20 / D40). Uses Ultralytics weights when present; otherwise OpenCV heuristics for
          demo.
        </p>
      </section>

      <div className="rounded-2xl border border-slateish/10 bg-white/90 p-5 shadow-soft">
        <div className="flex flex-wrap items-end gap-4">
          <label className="block text-sm">
            <span className="mb-1 block text-slateish/60">Road / bridge image</span>
            <input type="file" accept="image/*" onChange={onFile} />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slateish/60">Link asset ID (optional)</span>
            <input
              className="rounded-lg border border-slateish/15 px-3 py-2"
              value={assetId}
              onChange={(e) => setAssetId(e.target.value)}
              placeholder="e.g. 12"
            />
          </label>
          <button
            type="button"
            disabled={!file || busy}
            onClick={runDetect}
            className="rounded-lg bg-teal px-4 py-2 text-sm font-medium text-white transition hover:bg-tealdeep disabled:opacity-50"
          >
            {busy ? "Detecting…" : "Run detection"}
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-critical">{error}</p>}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <h2 className="mb-2 text-sm font-medium text-slateish/70">Original</h2>
          {preview ? (
            <img src={preview} alt="upload" className="w-full rounded-xl border border-slateish/10" />
          ) : (
            <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-slateish/20 text-sm text-slateish/50">
              Upload an image to begin
            </div>
          )}
        </div>
        <div>
          <h2 className="mb-2 text-sm font-medium text-slateish/70">Annotated</h2>
          {annotated ? (
            <img
              src={annotated}
              alt="annotated"
              className="w-full rounded-xl border border-slateish/10"
            />
          ) : (
            <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-slateish/20 text-sm text-slateish/50">
              Detections appear here
            </div>
          )}
        </div>
      </div>

      {!!detections.length && (
        <div className="overflow-hidden rounded-2xl border border-slateish/10 bg-white shadow-soft">
          <table className="w-full text-left text-sm">
            <thead className="bg-mist/80 text-slateish/70">
              <tr>
                <th className="px-3 py-2">Defect</th>
                <th className="px-3 py-2">Confidence</th>
                <th className="px-3 py-2">Severity</th>
              </tr>
            </thead>
            <tbody>
              {detections.map((d) => (
                <tr key={d.id} className="border-t border-slateish/10">
                  <td className="px-3 py-2 font-medium">{d.defect_type}</td>
                  <td className="px-3 py-2">{(d.confidence * 100).toFixed(1)}%</td>
                  <td className="px-3 py-2">{d.severity || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
