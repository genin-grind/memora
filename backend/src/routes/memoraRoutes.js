import { Router } from "express";
import { graph, query, sourceById } from "../controllers/memoraController.js";

const router = Router();

router.post("/query", query);
router.post("/graph", graph);
router.get("/source/:id", sourceById);

export default router;
