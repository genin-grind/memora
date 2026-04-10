import { pythonRequest } from "../lib/pythonService.js";

export async function runSync(_req, res) {
  const result = await pythonRequest("/sync/run", {
    method: "POST",
  });
  res.status(result.status).json(result.data);
}

export async function syncStatus(_req, res) {
  const result = await pythonRequest("/sync/status");
  res.status(result.status).json(result.data);
}

export async function uploadDocument(req, res) {
  const result = await pythonRequest("/sync/upload", {
    method: "POST",
    body: JSON.stringify({
      kind: req.body?.kind || "",
      filename: req.body?.filename || "",
      content: req.body?.content || "",
    }),
  });
  res.status(result.status).json(result.data);
}
