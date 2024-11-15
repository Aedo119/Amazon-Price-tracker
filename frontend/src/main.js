import React, { useState, useEffect } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend } from "chart.js";
import { useNavigate } from "react-router-dom";
import Modal from "./Modal";

// Register chart.js components
ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend);

function App() {
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [threshold, setThreshold] = useState("");
  const [message, setMessage] = useState("");
  const [dates, setDates] = useState([]);
  const [prices, setPrices] = useState([]);
  const [showGraph, setShowGraph] = useState(false);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  // Handle product scraping
  const handleScrapeSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:5000/scrape", {
        url,
        email,
        threshval: parseFloat(threshold),
      });
      if (response.data.status === "success") {
        setMessage(`Scraped data: Product: ${response.data.product_name}, Price: ${response.data.price}`);
      } else {
        setMessage(response.data.message);
      }
    } catch (error) {
      console.error("Error scraping product:", error);
      setMessage("Error scraping product.");
    }
    setLoading(false);
  };
   const closeModal = () => {
    setMessage(""); // Close the modal by clearing the message
    setShowGraph(false);
  };
  // Fetch historical price data to plot the graph (only once)
  const handlePlotPrice = async () => {
    try {
      const response = await axios.post("http://localhost:5000/price-trend", { url });
      if (response.data) {
        setDates(response.data.dates);
        setPrices(response.data.prices);
        setShowGraph(true); // Show the graph once data is loaded
      }
    } catch (error) {
      console.error("Error fetching price trend:", error);
      setMessage("Failed to fetch price trend data.");
    }
  };

  const graphData = {
    labels: dates,
    datasets: [
      {
        label: "Price Over Time",
        data: prices,
        borderColor: "rgb(75, 192, 192)",
        backgroundColor: "rgba(75, 192, 192, 0.2)",
      },
    ],
  };

  return (
    <div className="App">
      <div className="text">
      <h1>Amazon Price Tracker</h1>
      <form onSubmit={handleScrapeSubmit}>

        <div className="userin">
          <input
            placeholder="Enter product link"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
        </div>
        <div className="userin">

          <input
            placeholder="Email for alerts"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="userin">

          <input
            placeholder="Enter threshold price"
            type="number"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            required
          />
        </div>
        <div className="buttons">
        <button type="submit">Scrape</button>
        <button type="button" onClick={handlePlotPrice}>Plot Graph</button> {/* Use correct function */}
        </div>
        <div className="hisbutt"><button type="button" onClick={() => navigate("/history")}>See History</button></div>

      </form>


        {loading && <div className="spinner"></div>}
        {/* Modal for displaying messages */}
        <Modal message={message} graphData={showGraph ? graphData : null} onClose={closeModal} />

        </div>
    </div>
  );
}

export default App;
