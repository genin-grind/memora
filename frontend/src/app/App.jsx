import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "../components/AppShell";
import ProtectedRoute from "../components/ProtectedRoute";
import LoginPage from "../pages/LoginPage";
import MemoraPage from "../pages/MemoraPage";
import OrganizationPage from "../pages/OrganizationPage";
import ExplorerPage from "../pages/ExplorerPage";
import ControlCenterPage from "../pages/ControlCenterPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/organization" replace />} />
          <Route path="/memora" element={<MemoraPage />} />
          <Route path="/organization" element={<OrganizationPage />} />
          <Route path="/explorer" element={<ExplorerPage />} />
          <Route path="/control" element={<ControlCenterPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
