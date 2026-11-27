/**
 * Saves `data` as a pretty-printed JSON file through a temporary link: no package, and
 * nothing leaves the browser (the data came from our own API a moment before).
 */
export function saveJson(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  // Revoked a little later: some browsers start the download after click() returns.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** movie-match-data-2026-11-27.json, in the user's local date. */
export function exportFileName(now: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `movie-match-data-${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}.json`;
}
