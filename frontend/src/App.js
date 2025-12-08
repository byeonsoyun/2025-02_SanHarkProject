import React, { createContext, useState, useContext, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Chatbot from "./pages/Chatbot";
import About from "./pages/About";
import CalendarPage from "./pages/CalendarPage";
import NavbarComp from "./components/Navbar";
import Footer from "./components/Footer";
import ScrollToTopButton from "./components/ScrollToTopButton";

export const ThemeContext = createContext({
  theme: 'light',
  toggleTheme: () => {},
});

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

  const toggleTheme = () => {
    setTheme(currentTheme => {
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', newTheme);
      return newTheme;
    });
  };

  useEffect(() => {
    document.body.className = theme === 'dark' ? 'dark-mode' : '';
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="d-flex flex-column min-vh-100">
          <NavbarComp />
          <main className="flex-grow-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/chat" element={<Chatbot />} />
              <Route path="/about" element={<About />} />
              <Route path="/calendar" element={<CalendarPage />} />
            </Routes>
          </main>
          <ScrollToTopButton />
          <Footer />
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
