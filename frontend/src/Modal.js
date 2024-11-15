// Modal.js
import React from "react";
import "./Modal.css"; // Import modal styles
import { Line } from "react-chartjs-2";
import {
    CategoryScale,
    Chart as ChartJS,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    Title,
    Tooltip
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend);


const Modal = ({ message, graphData, onClose }) => {
  if (!message && !graphData) return null; // Don't render the modal if there's no message or graph

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <span className="close-btn" onClick={onClose}>×</span>

        {message && <p>{message}</p>} {/* Display the message */}

        {graphData && (
          <div style={{ width: "600px", height: "400px", margin: "auto" }}>
            <h2>Price Trend</h2>
            <Line data={graphData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Modal;
