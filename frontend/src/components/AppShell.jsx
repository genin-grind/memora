import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { clearStoredUser, getStoredUser } from "../services/authStore";

const navItems = [
  { to: "/organization", label: "Organization" },
  { to: "/memora", label: "Memora Core" },
  { to: "/explorer", label: "Explorer" },
  { to: "/control", label: "Control" },
];

export default function AppShell() {
  const navigate = useNavigate();
  const user = getStoredUser();

  function handleLogout() {
    clearStoredUser();
    navigate("/login", { replace: true });
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <p className="brand-kicker">Memora</p>
          <h1 className="brand-title">Decision Intelligence</h1>
          <p className="sidebar-copy">
            Secure internal workspace for organizational memory, source tracing,
            and decision reasoning.
          </p>
        </div>

        <nav className="nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `nav-link${isActive ? " nav-link-active" : ""}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <p className="user-name">{user?.name || "Member"}</p>
            <p className="user-email">{user?.email || ""}</p>
          </div>
          <button className="secondary-button" onClick={handleLogout} type="button">
            Log out
          </button>
        </div>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
