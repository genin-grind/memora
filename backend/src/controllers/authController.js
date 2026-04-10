import { pythonRequest } from "../lib/pythonService.js";

export async function login(req, res) {
  const result = await pythonRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify(req.body || {}),
  });

  res.status(result.status).json(result.data);
}

export function logout(_req, res) {
  res.json({ ok: true });
}

export async function me(_req, res) {
  const result = await pythonRequest("/auth/me");
  res.status(result.status).json(result.data);
}
