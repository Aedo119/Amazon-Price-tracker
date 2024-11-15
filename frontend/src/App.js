import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import HistoryPage from "./history";
import Home from "./main";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home/>} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </Router>
  );
};

export default App;

