import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getStoredUser } from "../services/authStore";

export default function ProtectedRoute() {
  const location = useLocation();
  const user = getStoredUser();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
