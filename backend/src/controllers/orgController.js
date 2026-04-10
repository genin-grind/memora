import { pythonRequest } from "../lib/pythonService.js";

export async function summary(_req, res) {
  const result = await pythonRequest("/org/summary");
  res.status(result.status).json(result.data);
}

export async function sourceStatus(_req, res) {
  const result = await pythonRequest("/org/sources/status");
  res.status(result.status).json(result.data);
}
