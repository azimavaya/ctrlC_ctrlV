/**
 * main.jsx — Application entry point for Panther Cloud Air.
 * Mounts the React app into the DOM with React Router (BrowserRouter)
 * and StrictMode enabled for development warnings.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

// Create the root React node and render into the #root div in index.html
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {/* BrowserRouter provides client-side routing for the entire app */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
