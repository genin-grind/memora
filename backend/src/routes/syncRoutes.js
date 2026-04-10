import { Router } from "express";
import { runSync, syncStatus } from "../controllers/syncController.js";

const router = Router();

router.post("/run", runSync);
router.get("/status", syncStatus);

export default router;
