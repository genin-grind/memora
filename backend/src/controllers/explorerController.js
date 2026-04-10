import { pythonRequest } from "../lib/pythonService.js";

export async function workspace(_req, res) {
  const result = await pythonRequest("/explorer/workspace");
  res.status(result.status).json(result.data);
}
