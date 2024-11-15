import React, { useEffect, useState } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend } from "chart.js";
import { useNavigate } from "react-router-dom";
import Modal from "./Modal"


// Register the necessary chart.js components
ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend);

function HistoryPage() {
  const [trackedProducts, setTrackedProducts] = useState([]);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const [dates, setDates] = useState([]);
  const [prices, setPrices] = useState([]);
  const [showGraph, setShowGraph] = useState(false);
  const [loading, setLoading] = useState(false);

  // Fetch tracked products when the page loads
  useEffect(() => {
    fetchTrackedProducts();
  }, []);

  const fetchTrackedProducts = async () => {
    try {
      const response = await axios.get("http://localhost:5000/tracked-products");
      if (response.data.status === "success") {
        setTrackedProducts(response.data.products);
      } else {
        console.error("Failed to load tracked products.");
      }
    } catch (error) {
      console.error("Error fetching tracked products:", error);
    }
  };


  const handleScrapeProduct = async (productID) => {
    try {

      setLoading(true);
      const url = `https://amazon.in/dp/${productID}`;
      console.log(url);
      const response = await axios.post("http://localhost:5000/scrape", { url,email:null,threshval:null});
      if (response.data.status === "success") {
        setMessage(`${response.data.product_name} ₹${response.data.price}`);
      } else {
        alert(response.data.message);
      }
    } catch (error) {
      console.error("Error scraping product:", error);
      alert("Failed to scrape product.");
    }
    setLoading(false);
  };
  const handleDelete = async (productID) => {
    try {
      const response = await axios.delete("http://localhost:5000/delete-history", { data:{product_id:productID}});
      if (response.data.status === "success") {
        fetchTrackedProducts();
      } else {
        alert(response.data.message);
      }
    } catch (error) {
      console.error("Error deleting product:", error);
      alert("Failed to delete product.");
    }
  };



  const handlePlotPrice = async (productID) => {
    try {
      const url = `https://amazon.in/dp/${productID}`;
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
  const closeModal = () => {
    setMessage(""); // Close the modal by clearing the message
    setShowGraph(false);
  };


  return (
    <div>
      <h1 className="tra">Tracked Products History</h1>
      <div className="hisbutt"><button onClick={() => navigate("/")}>Go Back</button></div>
      <div className="content">
      {trackedProducts.map((product) => (
          <div key={product.id} style={{border: "1px solid grey", padding: "20px", marginBottom: "10px",color:"white",borderRadius:"10px",backgroundColor:"rgb(0,0,0,0.1)",backdropFilter:"blur(10px)"}}>
            <div className="display">
              <img alt="image" src={product.image_url} width="200" height="200"/>
              <div className="non-image">
              <h2>{product.name}</h2>
               <div className="buttons his">
              <button onClick={() => handleScrapeProduct(product.id)}>Scrape</button>
              <button onClick={() => handlePlotPrice(product.id)}>Plot Price</button>
              <button onClick={() => handleDelete(product.id)}>Delete history</button>
              </div>
             </div>
            </div>
          </div>
      ))}
      </div>

      {loading && <div className="spinner"></div>}
      <Modal message={message} graphData={showGraph ? graphData : null} onClose={closeModal}/>
    </div>
  );
}

export default HistoryPage;
