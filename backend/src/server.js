import "dotenv/config";
import express from "express";
import cors from "cors";
import authRoutes from "./routes/authRoutes.js";
import healthRoutes from "./routes/healthRoutes.js";
import memoraRoutes from "./routes/memoraRoutes.js";
import orgRoutes from "./routes/orgRoutes.js";
import explorerRoutes from "./routes/explorerRoutes.js";
import syncRoutes from "./routes/syncRoutes.js";

const app = express();
const port = process.env.PORT || 8080;

app.use(
  cors({
    origin: process.env.FRONTEND_ORIGIN || "http://localhost:5173",
    credentials: true,
  }),
);
app.use(express.json());

app.use("/api/health", healthRoutes);
app.use("/api/auth", authRoutes);
app.use("/api/memora", memoraRoutes);
app.use("/api/org", orgRoutes);
app.use("/api/explorer", explorerRoutes);
app.use("/api/sync", syncRoutes);

app.listen(port, () => {
  console.log(`Memora backend listening on http://localhost:${port}`);
});
