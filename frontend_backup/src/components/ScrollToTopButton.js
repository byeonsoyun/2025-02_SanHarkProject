import React, { useState, useEffect } from "react";
import { FaArrowUp } from "react-icons/fa";

const ScrollToTopButton = () => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrolled = document.documentElement.scrollTop;
      setVisible(scrolled > 150); // ✅ 150px 이상일 때 보이게 (너무 작지도 크지도 않게)
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <button
      onClick={scrollToTop}
      style={{
        position: "fixed",
        bottom: "40px",
        right: "40px",
        backgroundColor: "#007bff",
        color: "white",
        border: "none",
        borderRadius: "50%",
        padding: "12px",
        cursor: "pointer",
        display: visible ? "inline" : "none",
        boxShadow: "0px 4px 8px rgba(0,0,0,0.2)",
        zIndex: 9999,
        transition: "opacity 0.3s ease-in-out",
      }}
    >
      <FaArrowUp />
    </button>
  );
};

export default ScrollToTopButton;
