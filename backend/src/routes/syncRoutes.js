import { Router } from "express";
import { runSync, syncStatus, uploadDocument } from "../controllers/syncController.js";

const router = Router();

router.post("/run", runSync);
router.post("/upload", uploadDocument);
router.get("/status", syncStatus);

export default router;
