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
