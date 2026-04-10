import { Router } from "express";
import { sourceStatus, summary } from "../controllers/orgController.js";

const router = Router();

router.get("/summary", summary);
router.get("/sources/status", sourceStatus);

export default router;
