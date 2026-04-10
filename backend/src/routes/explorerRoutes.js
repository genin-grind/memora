import { Router } from "express";
import { workspace } from "../controllers/explorerController.js";

const router = Router();

router.get("/workspace", workspace);

export default router;
