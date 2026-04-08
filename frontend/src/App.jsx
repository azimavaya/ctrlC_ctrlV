import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import HelpButton from "./components/HelpButton";
import Login from "./pages/Login";
import Home from "./pages/Home";
import BookFlight from "./pages/BookFlight";
import Timetable from "./pages/Timetable";
import Simulation from "./pages/Simulation";
import Finances from "./pages/Finances";
import MyBookings from "./pages/MyBookings";
import AdminDashboard from "./pages/AdminDashboard";
import Search from "./pages/Search";
import Unauthorized from "./pages/Unauthorized";
import "./App.css";

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app">
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(v => !v)} />
      <div className={`layout-body ${sidebarOpen ? "layout-body--open" : "layout-body--closed"}`}>
        <main className="main-content">{children}</main>
        <footer className="footer">
          <p>Panther Cloud Air &copy; 2026</p>
        </footer>
      </div>
      <HelpButton />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/unauthorized" element={<Layout><Unauthorized /></Layout>} />

        <Route path="/" element={
          <ProtectedRoute>
            <Layout><Home /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/book" element={
          <ProtectedRoute>
            <Layout><BookFlight /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/bookings" element={
          <ProtectedRoute>
            <Layout><MyBookings /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/timetable" element={
          <ProtectedRoute>
            <Layout><Timetable /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/search" element={
          <ProtectedRoute>
            <Layout><Search /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/simulation" element={
          <ProtectedRoute roles={["admin"]}>
            <Layout><Simulation /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/finances" element={
          <ProtectedRoute roles={["admin"]}>
            <Layout><Finances /></Layout>
          </ProtectedRoute>
        } />

        <Route path="/admin" element={
          <ProtectedRoute roles={["admin"]}>
            <Layout><AdminDashboard /></Layout>
          </ProtectedRoute>
        } />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
