import { pythonRequest } from "../lib/pythonService.js";

export async function query(req, res) {
  const result = await pythonRequest("/query", {
    method: "POST",
    body: JSON.stringify({
      question: req.body?.question || "",
    }),
  });
  res.status(result.status).json(result.data);
}

export function sourceById(req, res) {
  res.json({
    id: req.params.id,
    message: "Source detail route scaffolded.",
    status: "todo",
  });
}

export function graph(_req, res) {
  res.json({
    message: "Decision graph route scaffolded.",
    status: "todo",
  });
}
