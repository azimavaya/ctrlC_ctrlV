// Shown when a user tries to access a page they don't have permission for.
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Unauthorized() {
  const { user } = useAuth();
  return (
    <div style={{ textAlign: "center", padding: "4rem 1rem" }}>
      <h2 style={{ fontSize: "2rem", marginBottom: "1rem" }}>🚫 Access Denied</h2>
      <p style={{ color: "var(--pca-gray)", marginBottom: "1.5rem" }}>
        Your account (<strong>{user?.role}</strong>) does not have permission to view this page.
      </p>
      <Link to="/" className="btn-primary" style={{ padding: "0.6rem 1.4rem", borderRadius: "var(--radius)" }}>
        Go Home
      </Link>
    </div>
  );
}
